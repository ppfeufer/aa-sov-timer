"""
App config
"""

# Django
from django.apps import AppConfig
from django.utils.text import format_lazy

# AA Sovereignty Timer
from sovtimer import __title_translated__, __version__


class AaSovtimerConfig(AppConfig):
    """
    Application config
    """

    name = "sovtimer"
    label = "sovtimer"
    verbose_name = format_lazy(
        "{app_title} v{version}", app_title=__title_translated__, version=__version__
    )
