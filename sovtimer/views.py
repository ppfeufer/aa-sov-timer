"""
The views
"""

# Django
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.eveonline.evelinks.eveimageserver import alliance_logo_url
from allianceauth.eveonline.templatetags.evelinks import (
    dotlan_alliance_url,
    dotlan_region_url,
)
from allianceauth.services.hooks import get_extension_logger

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.models import Campaign, SovereigntyStructure
from sovtimer.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(name=__name__), prefix=__title__)


def _fmt_float_to_percentage(value: float) -> str:
    """
    Format a float value (0.0-1.0) as a percentage string with leading zero if <10%

    :param value:
    :type value:
    :return:
    :rtype:
    """

    pct = int(round(value * 100))
    s = f"{pct}%"

    if pct < 10:
        s = "0" + s

    return s


def dashboard(request: WSGIRequest) -> HttpResponse:
    """
    Index view
    """

    logger.info(msg=f"Module called by {request.user}")

    return render(request=request, template_name="sovtimer/dashboard.html")


def dashboard_data(  # pylint: disable=too-many-statements too-many-locals
    request: WSGIRequest,  # pylint: disable=unused-argument
) -> JsonResponse:
    """
    Ajax call => Get dashboard data

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

    campaign_system_ids = set(
        sovereignty_campaigns.values_list("structure__solar_system_id", flat=True)
    )

    if not campaign_system_ids:
        return JsonResponse(data=data, safe=False)

    sovereignty_structures = SovereigntyStructure.objects.filter(
        solar_system_id__in=campaign_system_ids
    )

    # Map solar_system_id -> vulnerability_occupancy_level for O(1) lookup
    occupancy_by_system = {
        s.solar_system_id: s.vulnerability_occupancy_level
        for s in sovereignty_structures
        if s.vulnerability_occupancy_level
    }

    now = timezone.now()

    for campaign in sovereignty_campaigns:
        alliance = campaign.structure.alliance
        solar_system = campaign.structure.solar_system
        constellation = solar_system.eve_constellation
        region = constellation.eve_region

        # Defender
        defender_name = alliance.name
        defender_url = dotlan_alliance_url(eve_obj=alliance)
        defender_logo_url = alliance_logo_url(alliance_id=alliance.id, size=32)
        defender_name_html = (
            f'<a href="{defender_url}" target="_blank" rel="noopener noreferer">'
            f'<img class="aa-sovtimer-entity-logo-left me-2" src="{defender_logo_url}" '
            f'alt="{defender_name}">{defender_name}</a>'
        )

        # Region / System / Constellation URLs and HTML (compute region_url once)
        region_url = dotlan_region_url(eve_obj=region)
        campaign_system_name = solar_system.name
        solar_system_url = f"{region_url}/{campaign_system_name}"
        solar_system_name_html = f'<a href="{solar_system_url}" target="_blank" rel="noopener noreferer">{campaign_system_name}</a>'

        constellation_name = constellation.name
        constellation_url = f"{region_url}/{constellation_name}"
        constellation_name_html = f'<a href="{constellation_url}" target="_blank" rel="noopener noreferer">{constellation_name}</a>'

        region_name = region.name
        region_name_html = f'<a href="{region_url}" target="_blank" rel="noopener noreferer">{region_name}</a>'

        # Activity defense multiplier (fast lookup)
        structure_adm = occupancy_by_system.get(campaign.structure.solar_system_id, 1)

        # Start time and remaining seconds (use timezone-aware now)
        start_time = campaign.start_time
        remaining_time_in_seconds = (start_time - now).total_seconds()

        # Progress formatting
        prev_formatted = _fmt_float_to_percentage(campaign.progress_previous)
        curr_formatted = _fmt_float_to_percentage(campaign.progress_current)

        campaign_progress_html = curr_formatted

        active_campaign = _("No")
        campaign_status = "inactive"

        if 0 <= remaining_time_in_seconds <= 14400:
            campaign_status = "upcoming"

        if remaining_time_in_seconds < 0:
            active_campaign = _("Yes")
            campaign_status = "active"

            if campaign.progress_previous < campaign.progress_current:
                title = _("Defenders making progress")
                cls = "aa-sovtimer-trend-up"
                icon_name = "trending_up"
            elif campaign.progress_previous > campaign.progress_current:
                title = _("Attackers making progress")
                cls = "aa-sovtimer-trend-down"
                icon_name = "trending_down"
            else:
                title = _("Neither side has made any progress yet")
                cls = "aa-sovtimer-trend-flat"
                icon_name = "trending_flat"

            campaign_progress_icon = (
                f'<i class="material-icons aa-sovtimer-trend {cls}" '
                f'title="{title}" data-bs-tooltip="aa-sovtimer">{icon_name}</i>'
            )

            constellation_id = constellation.id
            zkb_href = f"https://zkillboard.com/constellation/{constellation_id}/"
            zkb_icon = f'<img src="{static("sovtimer/images/zkillboard.png")}" alt="zKillboard">'
            constellation_killboard_link = (
                f'<a href="{zkb_href}" target="_blank" rel="noopener noreferer" '
                f'class="aa-sov-timer-zkb-icon ms-2">{zkb_icon}</a>'
            )

            campaign_progress_html = (
                prev_formatted
                + campaign_progress_icon
                + curr_formatted
                + constellation_killboard_link
            )

        data.append(
            {
                "event_type": Campaign.Type(campaign.event_type).label,
                "solar_system_name": campaign_system_name,
                "solar_system_name_html": solar_system_name_html,
                "constellation_name": constellation_name,
                "constellation_name_html": constellation_name_html,
                "region_name": region_name,
                "region_name_html": region_name_html,
                "defender_name": defender_name,
                "defender_name_html": defender_name_html,
                "adm": structure_adm,
                "start_time": start_time,
                "remaining_time": "",
                "remaining_time_in_seconds": remaining_time_in_seconds,
                "campaign_progress": campaign_progress_html,
                "active_campaign": active_campaign,
                "campaign_status": campaign_status,
            }
        )

    return JsonResponse(data=data, safe=False)
