"""
app config
"""

from django.apps import AppConfig

from sovtimer import __version__


class AaSovtimerConfig(AppConfig):
    """
    application config
    """

    name = "sovtimer"
    label = "sovtimer"
    verbose_name = f"Sovereignty Timer v{__version__}"
