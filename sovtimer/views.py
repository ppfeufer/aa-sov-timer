"""
The views
"""

# Standard Library
import datetime as dt

# Django
from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.evelinks.eveimageserver import alliance_logo_url
from allianceauth.eveonline.templatetags.evelinks import (
    dotlan_alliance_url,
    dotlan_region_url,
)
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.models import Campaign, SovereigntyStructure

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required
@permission_required("sovtimer.basic_access")
def dashboard(request: WSGIRequest) -> HttpResponse:
    """
    Index view
    """

    logger.info("Module called by %s", request.user)

    context = {}

    return render(request, "sovtimer/dashboard.html", context)


def dashboard_data(request: WSGIRequest) -> JsonResponse:
    """
    ajax call
    get dashboard data
    :param request:
    :return:
    """

    data = []

    sovereignty_campaigns = Campaign.objects.select_related(
        "structure",
        "structure__alliance",
        "structure__solar_system",
        "structure__solar_system__eve_constellation",
        "structure__solar_system__eve_constellation__eve_region",
    ).filter(structure__isnull=False)

    campaign_systems = sovereignty_campaigns.values_list(
        "structure__solar_system_id", flat=True
    )

    sovereignty_structures = SovereigntyStructure.objects.filter(
        solar_system_id__in=set(campaign_systems)
    )

    if sovereignty_campaigns:
        for campaign in sovereignty_campaigns:
            # defender name
            defender_name = campaign.structure.alliance.name
            defender_url = dotlan_alliance_url(campaign.structure.alliance)
            defender_logo_url = alliance_logo_url(
                alliance_id=campaign.structure.alliance.id, size=32
            )

            defender_name_html = (
                f'<a href="{defender_url}" target="_blank" rel="noopener noreferer">'
                f'<img class="aa-sovtimer-entity-logo-left" src="{defender_logo_url}" '
                f'alt="{defender_name}">{defender_name}</a>'
            )

            # solar system
            solar_system_name = campaign.structure.solar_system.name
            region_url = dotlan_region_url(
                campaign.structure.solar_system.eve_constellation.eve_region
            )
            campaign_system_name = campaign.structure.solar_system.name
            solar_system_url = f"{region_url}/{campaign_system_name}"
            solar_system_name_html = (
                f'<a href="{solar_system_url}" target="_blank" '
                f'rel="noopener noreferer">{campaign_system_name}</a>'
            )

            # constellation
            constellation_name = campaign.structure.solar_system.eve_constellation.name
            constellation_name_html = (
                f'<a href="//evemaps.dotlan.net/search?q={constellation_name}" '
                f'target="_blank" rel="noopener noreferer">{constellation_name}</a>'
            )

            # region
            region_name = (
                campaign.structure.solar_system.eve_constellation.eve_region.name
            )
            region_url = dotlan_region_url(
                campaign.structure.solar_system.eve_constellation.eve_region
            )
            region_name_html = (
                f'<a href="{region_url}" target="_blank" '
                f'rel="noopener noreferer">{region_name}</a>'
            )

            # activity defense multiplier
            structure_adm = 1
            for structure in sovereignty_structures:
                if (
                    structure.solar_system_id == campaign.structure.solar_system_id
                ) and structure.vulnerability_occupancy_level:
                    structure_adm = structure.vulnerability_occupancy_level

            # start time
            start_time = campaign.start_time

            # remaining time field
            remaining_time_in_seconds = dt.timedelta(
                seconds=(start_time.timestamp() - dt.datetime.now().timestamp())
            ).total_seconds()

            # campaign progress field
            campaign_progress_previous = campaign.progress_previous
            campaign_progress_previous_percentage = campaign_progress_previous * 100
            campaign_progress_previous_percentage_formatted = (
                f"{campaign_progress_previous_percentage:.0f}%"
            )

            if campaign_progress_previous_percentage < 10:
                campaign_progress_previous_percentage_formatted = (
                    "0" + campaign_progress_previous_percentage_formatted
                )

            campaign_pogress_current = campaign.progress_current
            campaign_pogress_current_percentage = campaign_pogress_current * 100
            campaign_pogress_current_percentage_formatted = (
                f"{campaign_pogress_current_percentage:.0f}%"
            )
            if campaign_pogress_current_percentage < 10:
                campaign_pogress_current_percentage_formatted = (
                    "0" + campaign_pogress_current_percentage_formatted
                )

            campaign_progress_html = campaign_pogress_current_percentage_formatted

            active_campaign = _("No")
            if remaining_time_in_seconds < 0:
                active_campaign = _("Yes")

                progress_text = _("Neither side has made any progress yet")
                campaign_progress_icon = (
                    "<i "
                    'class="material-icons aa-sovtimer-trend aa-sovtimer-trend-flat" '
                    f'title="{progress_text}">trending_flat</i>'
                )

                if campaign_progress_previous < campaign_pogress_current:
                    defender_progress_text = _("Defenders making progress")
                    campaign_progress_icon = (
                        "<i "
                        'class="material-icons aa-sovtimer-trend aa-sovtimer-trend-up" '
                        f'title="{defender_progress_text}">trending_up</i>'
                    )

                if campaign_progress_previous > campaign_pogress_current:
                    attacker_progress_text = _("Attackers making progress")
                    campaign_progress_icon = (
                        "<i "
                        'class="material-icons aa-sovtimer-trend aa-sovtimer-trend-down" '
                        f'title="{attacker_progress_text}">trending_down</i>'
                    )

                constellation_id = campaign.structure.solar_system.eve_constellation.id
                zkb_href = f"https://zkillboard.com/constellation/{constellation_id}/"
                zkb_icon = '<img src="/static/sovtimer/images/zkillboard.png">'
                constellation_killboard_link = (
                    f'<a href="{zkb_href}" target="_blank" rel="noopener noreferer" '
                    f'class="aa-sov-timer-zkb-icon">{zkb_icon}</a>'
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
                    "event_type": Campaign.Type(campaign.event_type).label,
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
