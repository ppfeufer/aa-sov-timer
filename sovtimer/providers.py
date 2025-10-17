"""
Providers
"""

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
