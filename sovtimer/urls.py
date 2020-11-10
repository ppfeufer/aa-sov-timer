# -*- coding: utf-8 -*-

"""
pages url config
"""

from django.conf.urls import url

from sovtimer import views


app_name: str = "sovtimer"

urlpatterns = [url(r"^$", views.dashboard, name="dashboard")]
