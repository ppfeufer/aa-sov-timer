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

logger = LoggerAddTag(my_logger=get_extension_logger(name=__name__), prefix=__title__)


ESI_ERROR_LIMIT = 50
ESI_TIMEOUT_ONCE_ERROR_LIMIT_REACHED = 60
ESI_SOV_STRUCTURES_CACHE_KEY = "sov_structures_cache"
ESI_MAX_RETRIES = 3

TASK_TIME_LIMIT = 600  # Stop after 10 minutes

# Params for all tasks
TASK_PRIORITY = 6
TASK_ONCE_ARGS = {"graceful": True}
TASK_ONCE = {"base": QueueOnce, "once": TASK_ONCE_ARGS}

TASK_DEFAULTS = {"time_limit": TASK_TIME_LIMIT, "max_retries": ESI_MAX_RETRIES}
TASK_DEFAULTS_ONCE = {**TASK_DEFAULTS, **TASK_ONCE}


@shared_task(**TASK_DEFAULTS_ONCE)
def run_sov_campaign_updates() -> None:
    """
    Update all sov campaigns
    """

    if not is_esi_online():
        logger.info(
            msg=(
                "ESI seems to be offline, currently. "
                "Can't start ESI related tasks. Aborting …"
            )
        )

        return

    logger.info(msg="Updating sovereignty structures and campaigns from ESI …")

    update_sov_structures.apply_async(priority=TASK_PRIORITY, once=TASK_ONCE_ARGS)
    update_sov_campaigns.apply_async(priority=TASK_PRIORITY, once=TASK_ONCE_ARGS)


@shared_task(**TASK_DEFAULTS_ONCE)
def update_sov_campaigns() -> None:
    """
    Update sov campaigns
    """

    campaigns_from_esi = Campaign.get_sov_campaigns_from_esi()

    logger.debug(
        msg=f"Number of sovereignty campaigns from ESI: {len(campaigns_from_esi)}"
    )

    if campaigns_from_esi:
        logger.debug(msg="Updating sovereignty campaigns …")

        with transaction.atomic():
            campaigns = []

            for campaign in campaigns_from_esi:
                EveEntity.objects.get_or_create(id=campaign["defender_id"])

                campaign_current__defender_score = campaign["defender_score"]

                try:
                    campaign_previous = Campaign.objects.get(
                        campaign_id=campaign["campaign_id"]
                    )
                except Campaign.DoesNotExist:
                    campaign_current__progress_previous = (
                        campaign_current__defender_score
                    )
                else:
                    campaign_previous__progress_previous = (
                        campaign_previous.progress_previous
                    )

                    campaign_previous__progress = campaign_previous.defender_score
                    campaign_current__progress_previous = campaign_previous__progress

                    if campaign_previous__progress == campaign_current__defender_score:
                        campaign_current__progress_previous = (
                            campaign_previous__progress_previous
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

            Campaign.objects.all().delete()
            Campaign.objects.bulk_create(
                objs=campaigns,
                batch_size=500,
                ignore_conflicts=True,
            )

            EveEntity.objects.bulk_update_new_esi()

            logger.info(msg=f"{len(campaigns)} sovereignty campaigns updated from ESI.")


@shared_task(**TASK_DEFAULTS_ONCE)
def update_sov_structures() -> None:
    """
    Update sov structures
    """

    if cache.get(ESI_SOV_STRUCTURES_CACHE_KEY) is None:
        logger.debug(msg="Updating sovereignty structures …")
        structures_from_esi = SovereigntyStructure.get_sov_structures_from_esi()

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
                    objs=sov_structures,
                    batch_size=500,
                    ignore_conflicts=True,
                )

                EveEntity.objects.bulk_update_new_esi()
                SovereigntyStructure.objects.exclude(pk__in=esi_structure_ids).delete()

                cache.set(ESI_SOV_STRUCTURES_CACHE_KEY, True, 120)

                logger.info(
                    msg=f"{structure_count} sovereignty structures updated from ESI."
                )
