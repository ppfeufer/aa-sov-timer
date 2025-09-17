"""
Providers
"""

# Alliance Auth
from esi.openapi_clients import ESIClientProvider

# AA Sovereignty Timer
from sovtimer import (
    __app_name_useragent__,
    __esi_compatibility_date__,
    __github_url__,
    __package_name__,
    __version__,
)
from sovtimer.handler.etag import Etag

# ESI client
esi = ESIClientProvider(
    # Use the latest compatibility date, see https://esi.evetech.net/meta/compatibility-dates
    compatibility_date=__esi_compatibility_date__,
    # User agent for the ESI client
    ua_appname=__app_name_useragent__,
    ua_version=__version__,
    ua_url=__github_url__,
)

# ETag handler
etag = Etag(app_name=__package_name__)
