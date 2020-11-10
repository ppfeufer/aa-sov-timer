# -*- coding: utf-8 -*-

"""
pages url config
"""

from django.conf.urls import url

from sovtimer import views


app_name: str = "sovtimer"

urlpatterns = [
    url(r"^$", views.dashboard, name="dashboard"),
    # ajax call
    url(
        r"^dashboard_data/$",
        views.dashboard_data,
        name="dashboard_data",
    ),
]
