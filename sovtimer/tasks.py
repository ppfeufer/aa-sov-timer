# -*- coding: utf-8 -*-

"""
the tasks
"""

from bravado.exception import (
    HTTPBadGateway,
    HTTPGatewayTimeout,
    HTTPServiceUnavailable,
)

from celery import shared_task

from eveuniverse.core.esitools import is_esi_online

from sovtimer import __title__
from sovtimer.models import AaSovtimerCampaigns, AaSovtimerStructures
from sovtimer.utils import LoggerAddTag

from allianceauth.services.hooks import get_extension_logger


logger = LoggerAddTag(get_extension_logger(__name__), __title__)

DEFAULT_TASK_PRIORITY = 6
ESI_ERROR_LIMIT = 50
ESI_TIMEOUT_ONCE_ERROR_LIMIT_REACHED = 60

# params for all tasks
TASK_DEFAULT_KWARGS = {
    "time_limit": 15,
}

# params for tasks that make ESI calls
TASK_ESI_KWARGS = {
    **TASK_DEFAULT_KWARGS,
    **{
        "autoretry_for": (
            OSError,
            HTTPBadGateway,
            HTTPGatewayTimeout,
            HTTPServiceUnavailable,
        ),
        "retry_kwargs": {"max_retries": 3},
        "retry_backoff": True,
    },
}


@shared_task(**TASK_DEFAULT_KWARGS)
def run_sov_campaign_updates() -> None:
    """
    update all sov campaigns
    """

    if not is_esi_online():
        logger.info(
            "ESI is currently offline. Can not start ESI related tasks. Aborting"
        )
        return

    logger.info("Updating sovereignty structures and campaigns from ESI.")

    update_sov_structures.apply_async(priority=DEFAULT_TASK_PRIORITY)
    update_sov_campaigns.apply_async(priority=DEFAULT_TASK_PRIORITY)


@shared_task(**TASK_ESI_KWARGS)
def update_sov_campaigns() -> None:
    """
    update campaigns
    """

    logger.info("Updating sov campaigns from ESI.")

    campaigns_from_esi = AaSovtimerCampaigns.sov_campaigns_from_esi()

    if campaigns_from_esi:
        AaSovtimerCampaigns.objects.all().delete()
        campaigns = list()

        for campaign in campaigns_from_esi:
            campaigns.append(
                AaSovtimerCampaigns(
                    attackers_score=campaign["attackers_score"],
                    campaign_id=campaign["campaign_id"],
                    constellation_id=campaign["constellation_id"],
                    defender_id=campaign["defender_id"],
                    defender_score=campaign["defender_score"],
                    event_type=campaign["event_type"],
                    solar_system_id=campaign["solar_system_id"],
                    start_time=campaign["start_time"],
                    structure_id=campaign["structure_id"],
                )
            )

        AaSovtimerCampaigns.objects.bulk_create(
            campaigns,
            batch_size=500,
            ignore_conflicts=True,
        )


@shared_task(**TASK_ESI_KWARGS)
def update_sov_structures() -> None:
    """
    update structures
    """

    logger.info("Updating sov structures from ESI.")

    structures_from_esi = AaSovtimerStructures.sov_structures_from_esi()

    if structures_from_esi:
        AaSovtimerStructures.objects.all().delete()
        sov_structures = list()

        for structure in structures_from_esi:
            vulnerability_occupancy_level = 1
            if structure["vulnerability_occupancy_level"]:
                vulnerability_occupancy_level = structure[
                    "vulnerability_occupancy_level"
                ]

            vulnerable_end_time = None
            if structure["vulnerable_end_time"]:
                vulnerable_end_time = structure["vulnerable_end_time"]

            vulnerable_start_time = None
            if structure["vulnerable_start_time"]:
                vulnerable_start_time = structure["vulnerable_start_time"]

            sov_structures.append(
                AaSovtimerStructures(
                    alliance_id=structure["alliance_id"],
                    solar_system_id=structure["solar_system_id"],
                    structure_id=structure["structure_id"],
                    structure_type_id=structure["structure_type_id"],
                    vulnerability_occupancy_level=vulnerability_occupancy_level,
                    vulnerable_end_time=vulnerable_end_time,
                    vulnerable_start_time=vulnerable_start_time,
                )
            )

        AaSovtimerStructures.objects.bulk_create(
            sov_structures,
            batch_size=500,
            ignore_conflicts=True,
        )
