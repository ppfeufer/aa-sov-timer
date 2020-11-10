# -*- coding: utf-8 -*-

"""
the views
"""

from sovtimer.utils import LoggerAddTag

from django.contrib.auth.decorators import login_required, permission_required

from django.shortcuts import render, redirect

from sovtimer import __title__
from sovtimer.app_settings import avoid_cdn

from allianceauth.services.hooks import get_extension_logger

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permission_required("sovtimer.basic_access")
def dashboard(request):
    """
    Index view
    """

    logger.info("Module called by %s", request.user)

    context = {
        "avoidCdn": avoid_cdn(),
    }

    return render(request, "sovtimer/dashboard.html", context)
