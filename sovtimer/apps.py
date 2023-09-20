"""
App config
"""

# Django
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

# AA Sovereignty Timer
from sovtimer import __version__


class AaSovtimerConfig(AppConfig):
    """
    Application config
    """

    name = "sovtimer"
    label = "sovtimer"
    verbose_name = _(f"Sovereignty Timer v{__version__}")
