"""
ETag helper functions
"""

# Third Party
from httpx import Response

# Django
from django.core.cache import cache

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
    ETag helper class for managing ETag caching and operations.
    """

    @classmethod
    def get_etag_key(cls, operation: EsiOperation) -> str:
        """
        Get the cache key for the ETag of the given operation.

        :param operation: The ESI operation for which the cache key is generated.
        :type operation: EsiOperation
        :return: The cache key for the ETag.
        :rtype: str
        """

        return "etag-" + operation._cache_key()

    @classmethod
    def get_etag_header(cls, operation: EsiOperation) -> str | bool:
        """
        Get the ETag header from the cache for the given operation.

        :param operation: The ESI operation for which the ETag is retrieved.
        :type operation: EsiOperation
        :return: The cached ETag header or False if not found.
        :rtype: str | bool
        """

        return cache.get(key=cls.get_etag_key(operation=operation), default=False)

    @classmethod
    def del_etag_header(cls, operation: EsiOperation) -> bool:
        """
        Delete the ETag header from the cache for the given operation.

        :param operation: The ESI operation for which the ETag is deleted.
        :type operation: EsiOperation
        :return: True if the deletion was successful, False otherwise.
        :rtype: bool
        """

        return cache.delete(key=cls.get_etag_key(operation=operation), version=False)

    @classmethod
    def set_etag_header(
        cls, operation: EsiOperation, response: Response | HTTPNotModified
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
                key=cls.get_etag_key(operation=operation), value=etag, timeout=ETAG_TTL
            )

            logger.debug(f"ETag: set_etag {operation} - {etag} - Stored: {result}")

    @classmethod
    def update_page_num(cls, operation: EsiOperation, page_number: int) -> None:
        """
        Update the page number parameter for the given operation.

        :param operation: The ESI operation to update.
        :type operation: EsiOperation
        :param page_number: The page number to set.
        :type page_number: int
        """

        if operation._has_page_param():
            operation._kwargs["page"] = page_number

    @classmethod
    def get_total_pages(cls, res: Response) -> int:
        """
        Get the total number of pages from the response headers.

        :param res: The HTTP response containing the total pages header.
        :type res: Response
        :return: The total number of pages.
        :rtype: int
        """

        return int(res.headers["X-Pages"]) if res and "X-Pages" in res.headers else 1

    @classmethod
    def single_page(cls, operation: EsiOperation, force_refresh: bool) -> tuple:
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
            cls.del_etag_header(operation)

        etag = cls.get_etag_header(operation)

        try:
            result = operation.result(etag=etag, return_response=True)

            if isinstance(result, tuple) and len(result) == 2:
                data, res = result
            else:
                # Handle case where result is not a tuple of (data, res)
                data, res = result, None
        except HTTPNotModified as exc:
            logger.debug(f"ETag: Match - Resetting TTL - {operation} - {etag}")

            cls.set_etag_header(operation, exc)

            raise NotModifiedError() from exc

        if etag == (res.headers.get("ETag") if res else None):
            logger.debug(
                f"ETag: Hard cache match - Resetting TTL - {operation} - {etag}"
            )

            cls.set_etag_header(operation, res)

            raise NotModifiedError()

        cls.set_etag_header(operation, res)

        return data, res

    @classmethod
    def etag_result(
        cls, operation: EsiOperation, force_refresh: bool = False
    ) -> dict | list | None:
        """
        Get the result of the given operation, using ETag caching.

        :param operation: The ESI operation to execute.
        :type operation: EsiOperation
        :param force_refresh: Whether to force a refresh by deleting the cached ETag.
        :type force_refresh: bool
        :return: The data retrieved from the operation.
        :rtype: dict
        """

        if operation._has_page_param():
            page = 1

            cls.update_page_num(operation=operation, page_number=page)

            data, res = cls.single_page(
                operation=operation, force_refresh=force_refresh
            )
            total_pages = int(cls.get_total_pages(res=res))

            logger.info(f"Page {operation} / Pages {total_pages}")

            while page < total_pages:
                page += 1

                cls.update_page_num(operation=operation, page_number=page)

                if force_refresh:
                    cls.del_etag_header(operation=operation)

                _data, res = cls.single_page(
                    operation=operation, force_refresh=force_refresh
                )

                if _data:
                    data += _data

                logger.info(
                    f"Page {operation} - Page {page}/{total_pages} - {len(_data)}"
                )
        else:
            data, res = cls.single_page(
                operation=operation, force_refresh=force_refresh
            )

            cls.set_etag_header(operation=operation, response=res)

        return data
