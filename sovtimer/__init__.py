"""
App init
"""

# Standard Library
from importlib import metadata

# Django
from django.utils.translation import gettext_lazy as _

__version__ = metadata.version(distribution_name="aa-sov-timer")
__title__ = _("Sovereignty Timers")

del metadata
