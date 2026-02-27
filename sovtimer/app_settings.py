"""
App settings
"""

# Django
from django.conf import settings


def debug_enabled() -> bool:
    """
    Check if DEBUG is enabled

    :return:
    :rtype:
    """

    return settings.DEBUG
