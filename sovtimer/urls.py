"""
App's URL config
"""

# Django
from django.urls import path

# AA Sovereignty Timer
from sovtimer import views

app_name: str = "sovtimer"

urlpatterns = [
    path(route="", view=views.dashboard, name="dashboard"),
    # Ajax call
    path(route="dashboard_data/", view=views.dashboard_data, name="dashboard_data"),
]
