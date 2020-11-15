# -*- coding: utf-8 -*-

"""
the views
"""

import datetime as dt

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
            # defender name
            defender_name = campaign.defender.name
            defender_name_html = (
                '<a href="https://evemaps.dotlan.net/search?q={defender_name}" '
                'target="_blank" rel="noopener noreferer">{defender_name}</a>'.format(
                    defender_name=defender_name
                )
            )

            # solar system
            solar_system_name = campaign.solar_system.name
            solar_system_name_html = (
                '<a href="https://evemaps.dotlan.net/search?q={solar_system_name}" '
                'target="_blank" rel="noopener noreferer">{solar_system_name}</a>'.format(
                    solar_system_name=solar_system_name
                )
            )

            # constellation
            constellation_name = campaign.solar_system.eve_constellation.name
            constellation_name_html = (
                '<a href="https://evemaps.dotlan.net/search?q={constellation_name}" '
                'target="_blank" rel="noopener noreferer">{constellation_name}</a>'.format(
                    constellation_name=constellation_name
                )
            )

            # region
            region_name = campaign.solar_system.eve_constellation.eve_region.name
            region_name_html = (
                '<a href="https://evemaps.dotlan.net/search?q={region_name}" '
                'target="_blank" rel="noopener noreferer">{region_name}</a>'.format(
                    region_name=region_name
                )
            )

            # activity defense multiplier
            structure_adm = 1
            for structure in sovereignty_structures:
                if (
                    structure.solar_system_id == campaign.solar_system_id
                ) and structure.vulnerability_occupancy_level:
                    structure_adm = structure.vulnerability_occupancy_level

            # start time
            start_time = campaign.start_time.replace(tzinfo=None)

            # remaining time field
            remaining_time_in_seconds = dt.timedelta(
                seconds=(start_time.timestamp() - dt.datetime.now().timestamp())
            ).total_seconds()

            # campaign progress field
            campaign_progress_previous = campaign.progress_previous
            campaign_progress_previous_percentage = campaign_progress_previous * 100
            campaign_progress_previous_percentage_formatted = "{:.0f}%".format(
                campaign_progress_previous_percentage
            )
            if campaign_progress_previous_percentage < 10:
                campaign_progress_previous_percentage_formatted = (
                    "0" + campaign_progress_previous_percentage_formatted
                )

            campaign_pogress_current = campaign.progress_current
            campaign_pogress_current_percentage = campaign_pogress_current * 100
            campaign_pogress_current_percentage_formatted = "{:.0f}%".format(
                campaign_pogress_current_percentage
            )
            if campaign_pogress_current_percentage < 10:
                campaign_pogress_current_percentage_formatted = (
                    "0" + campaign_pogress_current_percentage_formatted
                )

            campaign_progress_html = campaign_pogress_current_percentage_formatted

            active_campaign = _("No")
            if remaining_time_in_seconds < 0:
                active_campaign = _("Yes")

                campaign_progress_icon = (
                    '<i class="material-icons aa-sovtimer-trend aa-sovtimer-trend-flat" '
                    'title="{title_text}">trending_flat</i>'.format(
                        title_text=_("Neither side has made any progress yet")
                    )
                )

                if campaign_progress_previous < campaign_pogress_current:
                    campaign_progress_icon = (
                        '<i class="material-icons aa-sovtimer-trend aa-sovtimer-trend-up" '
                        'title="{title_text}">trending_up</i>'.format(
                            title_text=_("Defenders making progress")
                        )
                    )

                if campaign_progress_previous > campaign_pogress_current:
                    campaign_progress_icon = (
                        '<i class="material-icons aa-sovtimer-trend aa-sovtimer-trend-down" '
                        'title="{title_text}">trending_down</i>'.format(
                            title_text=_("Attackers making progress")
                        )
                    )

                constellation_killboard_link = (
                    '<a href="https://zkillboard.com/constellation/{constellation_id}/" '
                    'target="_blank" rel="noopener noreferer" '
                    'class="aa-sov-timer-zkb-icon">{zkb_icon}</a>'.format(
                        constellation_id=campaign.solar_system.eve_constellation.id,
                        zkb_icon='<img src="/static/sovtimer/images/zkillboard.png">',
                    )
                )

                campaign_progress_html = (
                    campaign_progress_previous_percentage_formatted
                    + campaign_progress_icon
                    + campaign_pogress_current_percentage_formatted
                    + constellation_killboard_link
                )

            data.append(
                {
                    # type column
                    "event_type": MAP_EVENT_TO_TYPE[campaign.event_type],
                    # system column + filter
                    "solar_system_name": solar_system_name,
                    "solar_system_name_html": solar_system_name_html,
                    # constellazion column + filter
                    "constellation_name": constellation_name,
                    "constellation_name_html": constellation_name_html,
                    # region column + filter
                    "region_name": region_name,
                    "region_name_html": region_name_html,
                    # defender column + filter
                    "defender_name": defender_name,
                    "defender_name_html": defender_name_html,
                    # adm column
                    "adm": structure_adm,
                    # start column
                    "start_time": start_time,
                    # remaining column
                    "remaining_time": "",
                    "remaining_time_in_seconds": remaining_time_in_seconds,
                    # progress column
                    "campaign_progress": campaign_progress_html,
                    # acive filter column (hidden)
                    "active_campaign": active_campaign,
                }
            )

    return JsonResponse(data, safe=False)
