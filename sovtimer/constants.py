"""
Constants we use throughout the app
"""

# Standard Library
import os

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

# aa-sov-timer/sovtimer
APP_BASE_DIR = os.path.join(os.path.dirname(__file__))
# aa-sov-timer/sovtimer/static/sovtimer
APP_STATIC_DIR = os.path.join(APP_BASE_DIR, "static", PACKAGE_NAME)

# All internal URLs need to start with this prefix
INTERNAL_URL_PREFIX = "-"
