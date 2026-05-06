"""
Providers
"""

# Standard Library
import logging
from typing import TYPE_CHECKING, Any

# Third Party
from aiopenapi3 import ContentTypeError, RequestError
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

if TYPE_CHECKING:
    # Alliance Auth
    from esi.stubs import AllianceDetail, SovereigntyCampaignsGetItem

# ESI client
esi = ESIClientProvider(
    # Use the latest compatibility date, see https://esi.evetech.net/meta/compatibility-dates
    compatibility_date=__esi_compatibility_date__,
    # spec_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "openapi.json"),
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
        "GetSovereigntySystems",
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
    ) -> Any | tuple[Any, Response] | None:
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
        :return: The result of the ESI operation.
        :rtype: Any | tuple[Any, Response] | None
        """

        logger.debug(f"Handling ESI operation: {operation.operation.operationId}")
        logger.debug(
            f"Operation parameters: use_etag={use_etag}, return_response={return_response}, force_refresh={force_refresh}, use_cache={use_cache}, extra={extra}"
        )

        response: Response | None = None

        try:
            # Call operation.result differently depending on whether the caller
            # requested the raw Response object. Some implementations return a
            # single result when return_response is False and a (result, response)
            # tuple when True, so only unpack when return_response is True.
            if return_response:
                esi_result, response = operation.result(
                    use_etag=use_etag,
                    return_response=return_response,
                    force_refresh=force_refresh,
                    use_cache=use_cache,
                    **extra,
                )

                logger.debug(
                    f"ESI Response for operation: {operation.operation.operationId}: {response}"
                )
            else:
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
        except (HTTPClientError, RequestError) as exc:
            logger.error(msg=f"Error while fetching data from ESI: {str(exc)}")

            esi_result = None

        # If caller requested the raw response, return a tuple (result, response)
        if return_response:
            return esi_result, response

        return esi_result

    @classmethod
    def get_alliances_alliance_id(
        cls,
        alliance_id: int,
        use_etags: bool = True,
        force_refresh: bool = False,
        return_response: bool = False,
    ) -> "AllianceDetail | tuple[AllianceDetail, Response] | Any":
        """
        Get alliance information from ESI.

        :param alliance_id: The ID of the alliance to retrieve.
        :type alliance_id: int
        :param use_etags: Whether to use ETag for caching.
        :type use_etags: bool
        :param force_refresh: Whether to force a refresh of the data from ESI, bypassing any caches.
        :type force_refresh: bool
        :param return_response: Whether to return the full response object.
        :type return_response: bool
        :return: Alliance information or None if an error occurred.
        :rtype: AllianceDetail | tuple[AllianceDetail, Response] | None
        """

        logger.debug(
            f"Fetching alliance information for alliance ID {alliance_id} from ESI…"
        )

        return cls.result(
            operation=esi.client.Alliance.GetAlliancesAllianceId(
                alliance_id=alliance_id
            ),
            use_etag=use_etags,
            force_refresh=force_refresh,
            return_response=return_response,
        )

    @classmethod
    def get_sovereignty_campaigns(
        cls,
        use_etags: bool = True,
        force_refresh: bool = False,
        return_response: bool = False,
    ) -> "list[SovereigntyCampaignsGetItem] | tuple[list[SovereigntyCampaignsGetItem], Response] | None":
        """
        Get sovereignty campaigns from ESI.

        :param use_etags: Whether to use ETag for caching.
        :type use_etags: bool
        :param force_refresh: Whether to force a refresh of the data from ESI, bypassing any caches.
        :type force_refresh: bool
        :param return_response: Whether to return the full response object.
        :type return_response: bool
        :return: List of sovereignty campaigns or None if an error occurred.
        :rtype: list[SovereigntyCampaignsGetItem] | tuple[list[SovereigntyCampaignsGetItem], Response] | None
        """

        logger.debug("Fetching sovereignty campaigns from ESI…")

        return cls.result(
            operation=esi.client.Sovereignty.GetSovereigntyCampaigns(),
            use_etag=use_etags,
            force_refresh=force_refresh,
            return_response=return_response,
        )

    @classmethod
    def get_sovereignty_systems(
        cls,
        use_etags: bool = True,
        force_refresh: bool = False,
        return_response: bool = False,
    ):
        """
        Get sovereignty systems from ESI.

        :param use_etags: Whether to use ETag for caching.
        :type use_etags: bool
        :param force_refresh: Whether to force a refresh of the data from ESI, bypassing any caches.
        :type force_refresh: bool
        :param return_response: Whether to return the full response object.
        :type return_response: bool
        :return: List of sovereignty systems or None if an error occurred.
        :rtype: list | tuple[list, Response] | None
        """

        logger.debug("Fetching sovereignty systems from ESI…")

        return cls.result(
            operation=esi.client.Sovereignty.GetSovereigntySystems(),
            use_etag=use_etags,
            force_refresh=force_refresh,
            return_response=return_response,
        )


class AppLogger(logging.LoggerAdapter):
    """
    Custom logger adapter that adds a prefix to log messages.

    Taken from the `allianceauth-app-utils` package.
    Credits to: Erik Kalkoken
    """

    def __init__(self, my_logger: logging.Logger, prefix: str = "Sovereignty Timer"):
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
