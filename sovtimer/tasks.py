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
from sovtimer.models import AaSovtimerCampaigns
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
