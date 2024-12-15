"""
Constants we use throughout the app
"""

# Alliance Auth
from esi import __version__ as esi_version

# AA Sovereignty Timer
from sovtimer import __version__

APP_NAME = "aa-sov-timer"
GITHUB_URL = f"https://github.com/ppfeufer/{APP_NAME}"
USER_AGENT = f"{APP_NAME}/{__version__} +{GITHUB_URL} via django-esi/{esi_version}"
