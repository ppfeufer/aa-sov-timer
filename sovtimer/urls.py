"""
App's URL config
"""

# Django
from django.urls import path

# AA Sovereignty Timer
from sovtimer import views
from sovtimer.constants import INTERNAL_URL_PREFIX

app_name: str = "sovtimer"

urlpatterns = [
    path(route="", view=views.dashboard, name="dashboard"),
    # Ajax call
    path(
        route=f"{INTERNAL_URL_PREFIX}/ajax/sov-campaign_data/",
        view=views.dashboard_data,
        name="dashboard_data",
    ),
]
