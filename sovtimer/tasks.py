"""
The tasks
"""

# Third Party
from celery import shared_task

# Django
from django.core.cache import cache
from django.db import transaction

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.core.esitools import is_esi_online
from eveuniverse.models import EveEntity, EveSolarSystem

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.models import Campaign, SovereigntyStructure

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

DEFAULT_TASK_PRIORITY = 6

ESI_ERROR_LIMIT = 50
ESI_TIMEOUT_ONCE_ERROR_LIMIT_REACHED = 60
ESI_SOV_STRUCTURES_CACHE_KEY = "sov_structures_cache"
ESI_MAX_RETRIES = 3

TASK_TIME_LIMIT = 600  # stop after 10 minutes

# params for all tasks
TASK_DEFAULT_KWARGS = {"time_limit": TASK_TIME_LIMIT, "max_retries": ESI_MAX_RETRIES}


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


@shared_task(**{**TASK_DEFAULT_KWARGS, **{"base": QueueOnce}})
def update_sov_campaigns() -> None:
    """
    update campaigns
    """

    campaigns_from_esi = Campaign.sov_campaigns_from_esi()

    if campaigns_from_esi:
        with transaction.atomic():
            campaigns = []

            campaign_count = 0

            for campaign in campaigns_from_esi:
                EveEntity.objects.get_or_create(id=campaign["defender_id"])

                campaign_current__defender_score = campaign["defender_score"]

                try:
                    campaign_previous = Campaign.objects.get(
                        campaign_id=campaign["campaign_id"]
                    )

                    campaign_previous__progress_previous = (
                        campaign_previous.progress_previous
                    )

                    campaign_previous__progress = campaign_previous.defender_score
                    campaign_current__progress_previous = campaign_previous__progress

                    if campaign_previous__progress == campaign_current__defender_score:
                        campaign_current__progress_previous = (
                            campaign_previous__progress_previous
                        )
                except Campaign.DoesNotExist:
                    campaign_current__progress_previous = (
                        campaign_current__defender_score
                    )

                campaigns.append(
                    Campaign(
                        attackers_score=campaign["attackers_score"],
                        campaign_id=campaign["campaign_id"],
                        defender_score=campaign["defender_score"],
                        event_type=campaign["event_type"],
                        start_time=campaign["start_time"],
                        structure_id=campaign["structure_id"],
                        progress_current=campaign_current__defender_score,
                        progress_previous=campaign_current__progress_previous,
                    )
                )

                campaign_count += 1

            Campaign.objects.all().delete()
            Campaign.objects.bulk_create(
                campaigns,
                batch_size=500,
                ignore_conflicts=True,
            )

            EveEntity.objects.bulk_update_new_esi()

            logger.info(f"{campaign_count} sovereignty campaigns updated from ESI.")


@shared_task(**{**TASK_DEFAULT_KWARGS, **{"base": QueueOnce}})
def update_sov_structures() -> None:
    """
    update structures
    """

    if cache.get(ESI_SOV_STRUCTURES_CACHE_KEY) is None:
        logger.debug("UPDATING SOV STRUCTURES")
        structures_from_esi = SovereigntyStructure.sov_structures_from_esi()

        if structures_from_esi:
            with transaction.atomic():
                esi_structure_ids = []
                sov_structures = []

                structure_count = 0

                for structure in structures_from_esi:
                    esi_structure_ids.append(structure["structure_id"])

                    structure_alliance, _ = EveEntity.objects.get_or_create(
                        id=structure["alliance_id"]
                    )

                    structure_solar_system = EveSolarSystem.objects.get(
                        id=structure["solar_system_id"]
                    )

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
                        SovereigntyStructure(
                            alliance=structure_alliance,
                            solar_system=structure_solar_system,
                            structure_id=structure["structure_id"],
                            structure_type_id=structure["structure_type_id"],
                            vulnerability_occupancy_level=vulnerability_occupancy_level,
                            vulnerable_end_time=vulnerable_end_time,
                            vulnerable_start_time=vulnerable_start_time,
                        )
                    )

                    structure_count += 1

                SovereigntyStructure.objects.bulk_create(
                    sov_structures,
                    batch_size=500,
                    ignore_conflicts=True,
                )

                EveEntity.objects.bulk_update_new_esi()
                SovereigntyStructure.objects.exclude(pk__in=esi_structure_ids).delete()

                cache.set(ESI_SOV_STRUCTURES_CACHE_KEY, True, 120)

                logger.info(
                    f"{structure_count} sovereignty structures updated from ESI."
                )
