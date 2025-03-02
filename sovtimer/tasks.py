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
ESI_MAX_RETRIES = 5

TASK_TIME_LIMIT = 600  # Stop after 10 minutes

# Params for all tasks
TASK_PRIORITY = 6
TASK_ONCE_ARGS = {"graceful": True}
TASK_ONCE = {"base": QueueOnce, "once": TASK_ONCE_ARGS}

TASK_DEFAULTS = {
    "time_limit": TASK_TIME_LIMIT,
    "max_retries": ESI_MAX_RETRIES,
    "default_retry_delay": 300,
}
TASK_DEFAULTS_ONCE = {**TASK_DEFAULTS, **TASK_ONCE}


@shared_task(**TASK_DEFAULTS_ONCE)
def run_sov_campaign_updates() -> None:
    """
    Update all sovereignty campaigns and structures

    This task is used to update all sovereignty campaigns and structures from ESI.
    It should be called by a periodic task, or in your `local.py` settings file via:

    ```python
    # AA Sovereignty Timer - https://github.com/ppfeufer/aa-sov-timer
    if "sovtimer" in INSTALLED_APPS:
        # Run campaign updates every 30 seconds
        CELERYBEAT_SCHEDULE["sovtimer.tasks.run_sov_campaign_updates"] = {
            "task": "sovtimer.tasks.run_sov_campaign_updates",
            "schedule": 30.0,
        }
    ```
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
    Update sovereignty campaigns

    This task is used to update the sovereignty campaigns from ESI.
    """

    campaigns_from_esi = Campaign.get_sov_campaigns_from_esi()

    logger.debug(
        msg=f"Number of sovereignty campaigns from ESI: {len(campaigns_from_esi or [])}"
    )

    if not campaigns_from_esi:
        logger.info(msg="No sovereignty campaigns found, nothing to update.")

        return

    logger.debug(msg="Updating sovereignty campaigns …")

    campaigns = []
    defender_ids = {campaign.get("defender_id") for campaign in campaigns_from_esi}
    existing_campaigns = {c.campaign_id: c for c in Campaign.objects.all()}

    EveEntity.objects.bulk_create(
        [EveEntity(id=defender_id) for defender_id in defender_ids],
        ignore_conflicts=True,
    )

    for campaign in campaigns_from_esi:
        campaign_id = campaign.get("campaign_id")
        campaign_current__defender_score = campaign.get("defender_score")
        campaign_current__progress_previous = campaign_current__defender_score

        if campaign_id in existing_campaigns:
            campaign_previous = existing_campaigns[campaign_id]
            campaign_previous__progress_previous = campaign_previous.progress_previous
            campaign_previous__progress = campaign_previous.defender_score
            campaign_current__progress_previous = campaign_previous__progress

            if campaign_previous__progress == campaign_current__defender_score:
                campaign_current__progress_previous = (
                    campaign_previous__progress_previous
                )

        campaigns.append(
            Campaign(
                attackers_score=campaign.get("attackers_score"),
                campaign_id=campaign_id,
                defender_score=campaign.get("defender_score"),
                event_type=campaign.get("event_type"),
                start_time=campaign.get("start_time"),
                structure_id=campaign.get("structure_id"),
                progress_current=campaign_current__defender_score,
                progress_previous=campaign_current__progress_previous,
            )
        )

    Campaign.objects.all().delete()
    Campaign.objects.bulk_create(
        objs=campaigns,
        batch_size=500,
        # ignore_conflicts=True,
    )
    EveEntity.objects.bulk_update_new_esi()

    logger.info(msg=f"{len(campaigns)} sovereignty campaigns updated from ESI.")


@shared_task(**TASK_DEFAULTS_ONCE)
def update_sov_structures() -> None:
    """
    Update sovereignty structures

    This task is used to update the sovereignty structures from ESI.
    """

    if cache.get(ESI_SOV_STRUCTURES_CACHE_KEY) is None:
        logger.debug(msg="Updating sovereignty structures …")

        structures_from_esi = SovereigntyStructure.get_sov_structures_from_esi()

        if structures_from_esi:
            with transaction.atomic():
                esi_structure_ids = set()
                sov_structures = []

                for structure in structures_from_esi:
                    structure_id = structure.get("structure_id")

                    if structure_id not in esi_structure_ids:
                        esi_structure_ids.add(structure_id)

                        sov_holder, _ = EveEntity.objects.get_or_create(
                            id=structure.get("alliance_id")
                        )

                        structure_solar_system = EveSolarSystem.objects.get(
                            id=structure.get("solar_system_id")
                        )

                        vulnerability_occupancy_level = (
                            1
                            if structure.get("vulnerability_occupancy_level") is None
                            else structure.get("vulnerability_occupancy_level")
                        )

                        vulnerable_end_time = structure.get("vulnerable_end_time")
                        vulnerable_start_time = structure.get("vulnerable_start_time")

                        sov_structures.append(
                            SovereigntyStructure(
                                alliance=sov_holder,
                                solar_system=structure_solar_system,
                                structure_id=structure_id,
                                structure_type_id=structure.get("structure_type_id"),
                                vulnerability_occupancy_level=vulnerability_occupancy_level,
                                vulnerable_end_time=vulnerable_end_time,
                                vulnerable_start_time=vulnerable_start_time,
                            )
                        )

                SovereigntyStructure.objects.bulk_create(
                    objs=sov_structures,
                    batch_size=500,
                    update_conflicts=True,
                    update_fields=[
                        "alliance",
                        "solar_system",
                        "structure_type_id",
                        "vulnerability_occupancy_level",
                        "vulnerable_end_time",
                        "vulnerable_start_time",
                    ],
                )

                EveEntity.objects.bulk_update_new_esi()
                SovereigntyStructure.objects.exclude(pk__in=esi_structure_ids).delete()

                cache.set(key=ESI_SOV_STRUCTURES_CACHE_KEY, value=True, timeout=120)

                logger.info(
                    msg=f"{len(sov_structures)} sovereignty structures updated from ESI."
                )
