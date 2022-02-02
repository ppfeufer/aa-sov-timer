"""
pages url config
"""

# Django
from django.urls import path

# AA Sovereignty Timer
from sovtimer import views

app_name: str = "sovtimer"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # ajax call
    path("dashboard_data/", views.dashboard_data, name="dashboard_data"),
]
