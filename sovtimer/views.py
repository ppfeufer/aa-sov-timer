# -*- coding: utf-8 -*-

"""
the views
"""

import datetime as dt

from django.core.cache import cache
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from sovtimer import __title__
from sovtimer.app_settings import avoid_cdn
from sovtimer.models import AaSovtimerCampaigns, AaSovtimerStructures
from sovtimer.utils import LoggerAddTag

from allianceauth.services.hooks import get_extension_logger


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


# module constants
MAP_EVENT_TO_TYPE = {
    "tcu_defense": "TCU",
    "ihub_defense": "IHub",
    "station_defense": "Station",
    "station_freeport": "Freeport",
}

CAMPAIGN_TREND_CACHE_TIME = 30


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
    """
    ajax call
    get dashboard data
    :param request:
    :return:
    """
    data = list()

    sovereignty_campaigns = AaSovtimerCampaigns.objects.all()
    sovereignty_structures = AaSovtimerStructures.objects.all()

    if sovereignty_campaigns and sovereignty_structures:
        for campaign in sovereignty_campaigns:
            defender_name = campaign.defender.name
            defender_name_html = (
                '<a href="https://evemaps.dotlan.net/search?q={defender_name}" '
                'target="_blank" rel="noopener noreferer">{defender_name}</a>'.format(
                    defender_name=defender_name
                )
            )

            # eve_solar_system = EveSolarSystem.objects.get(id=campaign.solar_system_id)

            solar_system_name = campaign.solar_system.name
            solar_system_name_html = (
                '<a href="https://evemaps.dotlan.net/search?q={solar_system_name}" '
                'target="_blank" rel="noopener noreferer">{solar_system_name}</a>'.format(
                    solar_system_name=solar_system_name
                )
            )

            constellation_name = campaign.solar_system.eve_constellation.name
            constellation_name_html = (
                '<a href="https://evemaps.dotlan.net/search?q={constellation_name}" '
                'target="_blank" rel="noopener noreferer">{constellation_name}</a>'.format(
                    constellation_name=constellation_name
                )
            )

            region_name = campaign.solar_system.eve_constellation.eve_region.name
            region_name_html = (
                '<a href="https://evemaps.dotlan.net/search?q={region_name}" '
                'target="_blank" rel="noopener noreferer">{region_name}</a>'.format(
                    region_name=region_name
                )
            )

            structure_adm = 1
            for structure in sovereignty_structures:
                if (
                    structure.solar_system_id == campaign.solar_system_id
                ) and structure.vulnerability_occupancy_level:
                    structure_adm = structure.vulnerability_occupancy_level

            start_time = campaign.start_time.replace(tzinfo=None)

            remaining_time_in_seconds = dt.timedelta(
                seconds=(start_time.timestamp() - dt.datetime.now().timestamp())
            ).total_seconds()

            attackers_score = campaign.attackers_score
            attackers_score_percent = "{:.0f}%".format(attackers_score * 100)
            if (attackers_score * 100) < 10:
                attackers_score_percent = "0" + attackers_score_percent

            defender_score = campaign.defender_score
            campaign_progress_html = "{:.0f}%".format(defender_score * 100)

            if (defender_score * 100) < 10:
                campaign_progress_html = "0" + campaign_progress_html

            active_campaign = _("No")
            if remaining_time_in_seconds < 0:
                active_campaign = _("Yes")

                cache_key_score_before = "sovtimer_defender_score_before_" + str(
                    campaign.campaign_id
                )

                cache_key_defender_progress_icon_before = (
                    "sovtimer_defender_progress_icon_before_"
                    + str(campaign.campaign_id)
                )

                defender_score_before = cache.get(cache_key_score_before)
                campaign_progress_icon_before = cache.get(
                    cache_key_defender_progress_icon_before
                )

                # campaign_progress_icon = ""
                campaign_progress_icon = (
                    '<i class="material-icons aa-sovtimer-trend aa-sovtimer-trend-flat" '
                    'title="{title_text}">trending_flat</i>'.format(
                        title_text=_("Neither side has made any progress yet")
                    )
                )
                if campaign_progress_icon_before is not None:
                    campaign_progress_icon = campaign_progress_icon_before

                if defender_score_before is not None:
                    if defender_score_before < (defender_score * 100):
                        campaign_progress_icon = (
                            '<i class="material-icons aa-sovtimer-trend aa-sovtimer-trend-up" '
                            'title="{title_text}">trending_up</i>'.format(
                                title_text=_("Defenders making progress")
                            )
                        )

                    if defender_score_before > (defender_score * 100):
                        campaign_progress_icon = (
                            '<i class="material-icons aa-sovtimer-trend aa-sovtimer-trend-down" '
                            'title="{title_text}">trending_down</i>'.format(
                                title_text=_("Attackers making progress")
                            )
                        )

                    cache.set(
                        cache_key_defender_progress_icon_before,
                        campaign_progress_icon,
                        CAMPAIGN_TREND_CACHE_TIME,
                    )

                if defender_score_before is not None and defender_score_before == (
                    defender_score * 100
                ):
                    cache.set(
                        cache_key_score_before,
                        defender_score_before,
                        CAMPAIGN_TREND_CACHE_TIME,
                    )
                else:
                    cache.set(
                        cache_key_score_before,
                        defender_score * 100,
                        CAMPAIGN_TREND_CACHE_TIME,
                    )

                constellation_killboard_link = (
                    '<a href="https://zkillboard.com/constellation/{constellation_id}/" '
                    'target="_blank" rel="noopener noreferer" '
                    'class="aa-sov-timer-zkb-icon">{zkb_icon}</a>'.format(
                        constellation_id=campaign.solar_system.eve_constellation.id,
                        zkb_icon='<img src="/static/sovtimer/images/zkillboard.png">',
                    )
                )

                campaign_progress_html += (
                    constellation_killboard_link + campaign_progress_icon
                )

            data.append(
                {
                    "campaign_id": campaign.campaign_id,
                    "event_type": MAP_EVENT_TO_TYPE[campaign.event_type],
                    "solar_system_id": campaign.solar_system_id,
                    "solar_system_name": solar_system_name,
                    "solar_system_name_html": solar_system_name_html,
                    "constellation_id": campaign.solar_system.eve_constellation.id,
                    "constellation_name": constellation_name,
                    "constellation_name_html": constellation_name_html,
                    "structure_id": campaign.structure_id,
                    "region_name": region_name,
                    "region_name_html": region_name_html,
                    "attackers_score": attackers_score_percent,
                    "defender_id": campaign.defender_id,
                    "defender_name": defender_name,
                    "defender_name_html": defender_name_html,
                    "campaign_progress": campaign_progress_html,
                    "adm": structure_adm,
                    "start_time": start_time,
                    "remaining_time": "",
                    "remaining_time_in_seconds": remaining_time_in_seconds,
                    "active_campaign": active_campaign,
                }
            )

    return JsonResponse(data, safe=False)
