# -*- coding: utf-8 -*-

"""
the views
"""

from sovtimer.utils import LoggerAddTag

from django.contrib.auth.decorators import login_required, permission_required

from django.http import JsonResponse
from django.shortcuts import render

from sovtimer import __title__
from sovtimer.app_settings import avoid_cdn

from allianceauth.services.hooks import get_extension_logger

from eveuniverse.models import EveRegion, EveConstellation, EveSolarSystem

from sovtimer.providers import esi

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


# module constants
MAP_EVENT_TO_TYPE = {
    "tcu_defense": "TCU",
    "ihub_defense": "IHub",
    "station_defense": "Station",
    "station_freeport": "Freeport",
}


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


def dashboard_data(request) -> JsonResponse:
    data = list()

    sovereignty_campaigns_esi = (
        esi.client.Sovereignty.get_sovereignty_campaigns().results()
    )

    # sovereignty_structures_esi = (
    #     esi.client.Sovereignty.get_sovereignty_structures().results()
    # )

    if sovereignty_campaigns_esi:
        for campaign in sovereignty_campaigns_esi:
            alliance_esi = esi.client.Alliance.get_alliances_alliance_id(
                alliance_id=campaign["defender_id"]
            ).results()

            defender_name = alliance_esi["name"]

            eve_solar_system = EveSolarSystem.objects.get(
                id=campaign["solar_system_id"]
            )

            solar_system_name = eve_solar_system.name
            constellation_name = eve_solar_system.eve_constellation.name
            region_name = eve_solar_system.eve_constellation.eve_region.name

            # structure_adm = 1
            # for structure in sovereignty_structures_esi:
            #     if (
            #         structure["solar_system_id"] == campaign["solar_system_id"]
            #     ) and structure["vulnerability_occupancy_level"] != "":
            #         structure_adm = structure["vulnerability_occupancy_level"]

            start_time = campaign["start_time"].replace(tzinfo=None)

            data.append(
                {
                    "attackers_score": "{:.0f}%".format(
                        campaign["attackers_score"] * 100
                    ),
                    "campaign_id": campaign["campaign_id"],
                    "constellation_id": campaign["constellation_id"],
                    "constellation_name": constellation_name,
                    "defender_id": campaign["defender_id"],
                    "defender_name": defender_name,
                    "defender_score": "{:.0f}%".format(
                        campaign["defender_score"] * 100
                    ),
                    "event_type": MAP_EVENT_TO_TYPE[campaign["event_type"]],
                    "solar_system_id": campaign["solar_system_id"],
                    "solar_system_name": solar_system_name,
                    "start_time": start_time,
                    "structure_id": campaign["structure_id"],
                    "region_name": region_name,
                    # "adm": structure_adm,
                }
            )

    return JsonResponse(data, safe=False)
