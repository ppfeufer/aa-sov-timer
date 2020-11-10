# -*- coding: utf-8 -*-

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
    verbose_name = "Sovereignty Timer v{}".format(__version__)
