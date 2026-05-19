"""
App's URL config
"""

# Django
from django.urls import path

# AA Sovereignty Timer
from sovtimer import views
from sovtimer.constants import Constants

app_name: str = "sovtimer"  # pylint: disable=invalid-name

urlpatterns = [
    path(route="", view=views.dashboard, name="dashboard"),
    # Ajax call
    path(
        route=f"{Constants.INTERNAL_URL_PREFIX}/ajax/sov-campaign_data/",
        view=views.dashboard_data,
        name="dashboard_data",
    ),
]
