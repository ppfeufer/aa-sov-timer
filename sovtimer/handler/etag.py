"""
ETag handling functions

This module provides utility functions and classes for managing ETag caching
and operations. ETags (Entity Tags) are used to optimize HTTP requests by
allowing clients to make conditional requests based on the state of a resource.

The module includes:
- A `NotModifiedError` exception for handling HTTP 304 Not Modified responses.
- An `Etag` class for managing ETag caching, retrieval, and deletion.
- Utility methods for handling paginated API responses and caching ETag headers.

Dependencies:
- Django for caching and logging utilities.
- `httpx` for handling HTTP responses.
- Alliance Auth and Django ESI for integration with external services.
"""

# Third Party
from httpx import Response

# Django
from django.core.cache import cache
from django.utils.text import slugify

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import HTTPNotModified
from esi.openapi_clients import EsiOperation

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.constants import ETAG_TTL

# Initialize a logger with a specific tag for the application
logger = LoggerAddTag(my_logger=get_extension_logger(name=__name__), prefix=__title__)


class NotModifiedError(Exception):
    """
    Exception to raise when a 304 Not Modified response is to be returned.
    """

    pass  # pylint: disable=unnecessary-pass


class Etag:
    """
    ETag handler class for managing ETag caching and operations.
    """

    def __init__(self, app_name: str) -> None:
        """
        Initialize the Etag handler with the given application name.

        :param app_name: The name of the application for which the ETag handler is initialized.
        :type app_name: str
        """

        self.app_name = slugify(app_name)

    def get_etag_key(self, operation: EsiOperation) -> str:
        """
        Get the cache key for the ETag of the given operation.

        :param operation: The ESI operation for which the cache key is generated.
        :type operation: EsiOperation
        :return: The cache key for the ETag.
        :rtype: str
        """

        etag_prefix = f"etag-{self.app_name}"
        etag_key = f"{etag_prefix}-{operation._cache_key()}"

        logger.debug(f"ETag: get_etag_key for {operation}: {etag_key}")

        return etag_key

    def get_etag_header(self, operation: EsiOperation) -> str | bool:
        """
        Get the ETag header from the cache for the given operation.

        :param operation: The ESI operation for which the ETag is retrieved.
        :type operation: EsiOperation
        :return: The cached ETag header or False if not found.
        :rtype: str | bool
        """

        return cache.get(key=self.get_etag_key(operation=operation), default=False)

    def del_etag_header(self, operation: EsiOperation) -> bool:
        """
        Delete the ETag header from the cache for the given operation.

        :param operation: The ESI operation for which the ETag is deleted.
        :type operation: EsiOperation
        :return: True if the deletion was successful, False otherwise.
        :rtype: bool
        """

        return cache.delete(key=self.get_etag_key(operation=operation))

    def set_etag_header(
        self, operation: EsiOperation, response: Response | HTTPNotModified
    ) -> None:
        """
        Store the ETag header in the cache for the given operation.

        :param operation: The ESI operation for which the ETag is set.
        :type operation: EsiOperation
        :param response: The HTTP response containing the ETag header.
        :type response: Response | HTTPNotModified
        """

        etag = response.headers.get("ETag") if response else None

        if etag:
            result = cache.set(
                key=self.get_etag_key(operation=operation), value=etag, timeout=ETAG_TTL
            )

            logger.debug(f"ETag: set_etag {operation} - {etag} - Stored: {result}")

    @staticmethod
    def update_page_num(operation: EsiOperation, page_number: int) -> None:
        """
        Update the page number parameter for the given operation.

        :param operation: The ESI operation to update.
        :type operation: EsiOperation
        :param page_number: The page number to set.
        :type page_number: int
        """

        if operation._has_page_param():
            operation._kwargs["page"] = page_number

    @staticmethod
    def get_total_pages(res: Response) -> int:
        """
        Get the total number of pages from the response headers.

        :param res: The HTTP response containing the total pages header.
        :type res: Response
        :return: The total number of pages.
        :rtype: int
        """

        return int(res.headers["X-Pages"]) if res and "X-Pages" in res.headers else 1

    def single_page(self, operation: EsiOperation, force_refresh: bool) -> tuple:
        """
        Get a single page of results for the given operation.

        :param operation: The ESI operation to execute.
        :type operation: EsiOperation
        :param force_refresh: Whether to force a refresh by deleting the cached ETag.
        :type force_refresh: bool
        :return: The data and response from the operation.
        :rtype: tuple
        """

        if force_refresh:
            self.del_etag_header(operation)

        etag = self.get_etag_header(operation)

        try:
            result = operation.result(etag=etag, return_response=True)

            if isinstance(result, tuple) and len(result) == 2:
                data, res = result
            else:
                # Handle case where result is not a tuple of (data, res)
                data, res = result, None
        except HTTPNotModified as exc:
            logger.debug(f"ETag: Match - Resetting TTL - {operation} - {etag}")

            self.set_etag_header(operation=operation, response=exc)

            raise NotModifiedError() from exc

        if etag == (res.headers.get("ETag") if res else None):
            logger.debug(
                f"ETag: Hard cache match - Resetting TTL - {operation} - {etag}"
            )

            self.set_etag_header(operation=operation, response=res)

            raise NotModifiedError()

        self.set_etag_header(operation=operation, response=res)

        return data, res

    def etag_result(self, operation: EsiOperation, force_refresh: bool = False) -> dict:
        """
        Get the result of the given operation, using ETag caching.

        :param operation: The ESI operation to execute.
        :type operation: EsiOperation
        :param force_refresh: Whether to force a refresh by deleting the cached ETag.
        :type force_refresh: bool
        :return: The data retrieved from the operation.
        :rtype: dict
        """

        if force_refresh:
            self.del_etag_header(operation=operation)

        if operation._has_page_param():
            page = 1

            self.update_page_num(operation=operation, page_number=page)

            data, res = self.single_page(
                operation=operation, force_refresh=force_refresh
            )
            total_pages = int(self.get_total_pages(res=res))

            logger.info(f"Page {operation} / Pages {total_pages}")

            while page < total_pages:
                page += 1

                self.update_page_num(operation=operation, page_number=page)

                _data, res = self.single_page(
                    operation=operation, force_refresh=force_refresh
                )

                if _data:
                    data += _data

                logger.info(
                    f"Page {operation} - Page {page}/{total_pages} - {len(_data)}"
                )
        else:
            data, res = self.single_page(
                operation=operation, force_refresh=force_refresh
            )

            self.set_etag_header(operation=operation, response=res)

        return data
