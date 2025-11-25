"""
Providers
"""

# Standard Library
import logging

# Alliance Auth
from esi.openapi_clients import ESIClientProvider

# AA Sovereignty Timer
from sovtimer import (
    __app_name_verbose__,
    __esi_compatibility_date__,
    __github_url__,
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
    operations=["GetSovereigntyCampaigns", "GetSovereigntyStructures"],
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
