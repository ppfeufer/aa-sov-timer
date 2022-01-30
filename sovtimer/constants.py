"""
Constants we use throughout the app
"""

# Django
from django.utils.text import slugify

# AA Sovereignty Timer
from sovtimer import __version__

VERBOSE_NAME = "Sovereignty Timer for Alliance Auth"

verbose_name_slugified: str = slugify(VERBOSE_NAME, allow_unicode=True)
github_url: str = "https://github.com/ppfeufer/aa-sov-timer"

USER_AGENT = f"{verbose_name_slugified} v{__version__} {github_url}"
