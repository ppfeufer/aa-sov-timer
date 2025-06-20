"""
Constants we use throughout the app
"""

# Alliance Auth
from esi import __version__ as esi_version

# AA Sovereignty Timer
from sovtimer import __version__

APP_NAME = "aa-sov-timer"
APP_NAME_VERBOSE = "AA Sovereignty Timer"
APP_NAME_VERBOSE_USERAGENT = "AA-Sovereignty-Timer"
PACKAGE_NAME = "sovtimer"
GITHUB_URL = f"https://github.com/ppfeufer/{APP_NAME}"
USER_AGENT = f"{APP_NAME_VERBOSE_USERAGENT}/{__version__} (+{GITHUB_URL}) Django-ESI/{esi_version}"

# All internal URLs need to start with this prefix
INTERNAL_URL_PREFIX = "-"
