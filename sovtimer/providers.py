"""
Providers
"""

# Standard Library
import logging
from typing import Any

# Third Party
from aiopenapi3 import ContentTypeError
from httpx import Response

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import HTTPClientError, HTTPNotModified
from esi.openapi_clients import ESIClientProvider, EsiOperation

# AA Sovereignty Timer
from sovtimer import (
    __app_name_verbose__,
    __esi_compatibility_date__,
    __github_url__,
    __title__,
    __version__,
)

# ESI client
esi = ESIClientProvider(
    # Use the latest compatibility date, see https://esi.evetech.net/meta/compatibility-dates
    compatibility_date=__esi_compatibility_date__,
    # User agent for the ESI client
    ua_appname=__app_name_verbose__,
    ua_version=__version__,
    ua_url=__github_url__,
    operations=[
        # Alliance
        "GetAlliancesAllianceId",
        # Sovereignty
        "GetSovereigntyCampaigns",
        "GetSovereigntyStructures",
    ],
)


class ESIHandler:
    """
    Handler for ESI operations, providing a method to retrieve results while handling exceptions.
    """

    @classmethod
    def result(  # pylint: disable=too-many-arguments, too-many-positional-arguments
        cls,
        operation: EsiOperation,
        use_etag: bool = True,
        return_response: bool = False,
        force_refresh: bool = False,
        use_cache: bool = True,
        **extra,
    ) -> tuple[Any, Response] | Any:
        """
        Retrieve the result of an ESI operation, handling HTTPNotModified exceptions.

        :param operation: The ESI operation to execute.
        :type operation: EsiOperation
        :param use_etag: Whether to use ETag for caching.
        :type use_etag: bool
        :param return_response: Whether to return the full response object.
        :type return_response: bool
        :param force_refresh: Whether to force a refresh of the data.
        :type force_refresh: bool
        :param use_cache: Whether to use cached data.
        :type use_cache: bool
        :param extra: Additional parameters to pass to the operation.
        :type extra: dict
        :return: The result of the ESI operation, optionally with the response object.
        :rtype: tuple[Any, Response] | Any
        """

        logger.debug(f"Handling ESI operation: {operation.operation.operationId}")

        try:
            esi_result = operation.result(
                use_etag=use_etag,
                return_response=return_response,
                force_refresh=force_refresh,
                use_cache=use_cache,
                **extra,
            )
        except HTTPNotModified:
            logger.debug(
                f"ESI returned 304 Not Modified for operation: {operation.operation.operationId} - Skipping update."
            )

            esi_result = None
        except ContentTypeError:
            logger.warning(
                msg="ESI returned gibberish (ContentTypeError) - Skipping update."
            )

            esi_result = None
        except HTTPClientError as exc:
            logger.error(msg=f"Error while fetching data from ESI: {str(exc)}")

            esi_result = None

        return esi_result

    @classmethod
    def get_alliances_alliance_id(
        cls, alliance_id: int, force_refresh: bool = False
    ) -> dict | None:
        """
        Get alliance information from ESI.

        :param alliance_id: The ID of the alliance to retrieve.
        :type alliance_id: int
        :param force_refresh: Whether to force a refresh of the data from ESI, bypassing any caches.
        :type force_refresh: bool
        :return: Alliance information or None if an error occurred.
        :rtype: dict | None
        """

        logger.debug(
            f"Fetching alliance information for alliance ID {alliance_id} from ESI..."
        )

        return cls.result(
            operation=esi.client.Alliance.GetAlliancesAllianceId(
                alliance_id=alliance_id
            ),
            force_refresh=force_refresh,
        )

    @classmethod
    def get_sovereignty_campaigns(
        cls, force_refresh: bool = False
    ) -> list[dict] | None:
        """
        Get sovereignty campaigns from ESI.

        :return: List of sovereignty campaigns or None if an error occurred.
        :rtype: list[dict] | None
        """

        logger.debug("Fetching sovereignty campaigns from ESI...")

        return cls.result(
            operation=esi.client.Sovereignty.GetSovereigntyCampaigns(),
            force_refresh=force_refresh,
        )

    @classmethod
    def get_sovereignty_structures(
        cls, force_refresh: bool = False
    ) -> list[dict] | None:
        """
        Get sovereignty structures from ESI.

        :return: List of sovereignty structures or None if an error occurred.
        :rtype: list[dict] | None
        """

        logger.debug("Fetching sovereignty structures from ESI...")

        return cls.result(
            operation=esi.client.Sovereignty.GetSovereigntyStructures(),
            force_refresh=force_refresh,
        )


class AppLogger(logging.LoggerAdapter):
    """
    Custom logger adapter that adds a prefix to log messages.

    Taken from the `allianceauth-app-utils` package.
    Credits to: Erik Kalkoken
    """

    def __init__(self, my_logger, prefix):
        """
        Initializes the AppLogger with a logger and a prefix.

        :param my_logger: Logger instance
        :type my_logger: logging.Logger
        :param prefix: Prefix string to add to log messages
        :type prefix: str
        """

        super().__init__(my_logger, {})

        self.prefix = prefix

    def process(self, msg, kwargs):
        """
        Prepares the log message by adding the prefix.

        :param msg: Log message
        :type msg: str
        :param kwargs: Additional keyword arguments
        :type kwargs: dict
        :return: Prefixed log message and kwargs
        :rtype: tuple
        """

        return f"[{self.prefix}] {msg}", kwargs


logger = AppLogger(my_logger=get_extension_logger(name=__name__), prefix=__title__)
