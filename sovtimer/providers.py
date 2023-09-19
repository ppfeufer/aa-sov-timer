"""
Providers
"""

# Alliance Auth
from esi.clients import EsiClientProvider

# AA Sovereignty Timer
from sovtimer.constants import USER_AGENT

# ESI client
esi = EsiClientProvider(app_info_text=USER_AGENT)
