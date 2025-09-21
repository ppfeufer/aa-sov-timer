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
            "schedule": 30,
        }
    ```
    """

    logger.info(msg="Updating sovereignty structures and campaigns from ESI …")

    update_sov_structures.apply_async(priority=TASK_PRIORITY, once=TASK_ONCE_ARGS)
    update_sov_campaigns.apply_async(priority=TASK_PRIORITY, once=TASK_ONCE_ARGS)


@shared_task(**TASK_DEFAULTS_ONCE)
def update_sov_campaigns(force_refresh: bool = False) -> None:
    """
    Update sovereignty campaigns

    This task is used to update the sovereignty campaigns from ESI.
    """

    campaigns_from_esi = Campaign.get_sov_campaigns_from_esi(
        force_refresh=force_refresh
    )

    if campaigns_from_esi is not None:
        logger.debug(
            msg=f"Number of sovereignty campaigns from ESI: {len(campaigns_from_esi or [])}"
        )

        campaigns = []
        defender_ids = {campaign.defender_id for campaign in campaigns_from_esi}

        existing_campaigns = {c.campaign_id: c for c in Campaign.objects.all()}

        EveEntity.objects.bulk_create(
            [EveEntity(id=defender_id) for defender_id in defender_ids],
            ignore_conflicts=True,
        )

        for campaign in campaigns_from_esi:
            campaign_id = campaign.campaign_id
            campaign_current__defender_score = campaign.defender_score
            campaign_current__progress_previous = campaign_current__defender_score

            if campaign_id in existing_campaigns:
                campaign_previous = existing_campaigns[campaign_id]
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
                    attackers_score=campaign.attackers_score,
                    campaign_id=campaign_id,
                    defender_score=campaign.defender_score,
                    event_type=campaign.event_type,
                    start_time=campaign.start_time,
                    structure_id=campaign.structure_id,
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
def update_sov_structures(force_refresh: bool = False) -> None:
    """
    Update sovereignty structures

    This task is used to update the sovereignty structures from ESI.
    """

    # Check if the cache indicates that the structures have already been updated
    if not force_refresh and cache.get(ESI_SOV_STRUCTURES_CACHE_KEY):
        return

    structures_from_esi = SovereigntyStructure.get_sov_structures_from_esi(
        force_refresh=force_refresh
    )

    if structures_from_esi is not None:
        logger.debug(
            msg=f"Number of sovereignty structures from ESI: {len(structures_from_esi or [])}"
        )

        # Pre-fetch current structures and campaigns for fast lookup
        current_structures = {
            s["structure_id"]: s["vulnerability_occupancy_level"]
            for s in SovereigntyStructure.objects.all().values(
                "structure_id", "vulnerability_occupancy_level"
            )
        }

        # Pre-fetch EveEntities and SolarSystems to avoid repeated DB hits
        alliance_ids = {s.alliance_id for s in structures_from_esi if s.alliance_id}

        # Ensure we have EveEntity entries for all alliances
        EveEntity.objects.bulk_create(
            [EveEntity(id=aid) for aid in alliance_ids],
            ignore_conflicts=True,
        )

        # Fetch existing solar systems and alliances from the database
        solar_system_ids = {
            s.solar_system_id for s in structures_from_esi if s.solar_system_id
        }

        # Ensure we have EveSolarSystem entries for all solar systems
        solar_systems = {
            ss.id: ss for ss in EveSolarSystem.objects.filter(id__in=solar_system_ids)
        }

        # Ensure we have EveEntity entries for all alliances
        alliances = {e.id: e for e in EveEntity.objects.filter(id__in=alliance_ids)}

        esi_structure_ids = set()
        sov_structures = []

        # Iterate through the structures from ESI and prepare them for bulk creation
        for structure in structures_from_esi:
            structure_id = structure.structure_id

            # Skip structures without an ID or if they already exist in the set
            if not structure_id or structure_id in esi_structure_ids:
                continue

            esi_structure_ids.add(structure_id)

            sov_holder = alliances.get(structure.alliance_id)
            structure_solar_system = solar_systems.get(structure.solar_system_id)

            # Get the vulnerability occupancy level
            if structure_id in set(
                Campaign.objects.all().values_list("structure_id", flat=True)
            ):
                vulnerability_occupancy_level = current_structures.get(structure_id, 1)
            else:
                vulnerability_occupancy_level = (
                    structure.vulnerability_occupancy_level or 1
                )

            # Append the structure to the list for bulk creation
            sov_structures.append(
                SovereigntyStructure(
                    alliance=sov_holder,
                    solar_system=structure_solar_system,
                    structure_id=structure_id,
                    structure_type_id=structure.structure_type_id,
                    vulnerability_occupancy_level=vulnerability_occupancy_level,
                    vulnerable_end_time=structure.vulnerable_end_time,
                    vulnerable_start_time=structure.vulnerable_start_time,
                )
            )

        # Create or update the sovereignty structures in bulk
        with transaction.atomic():
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

            # Update EveEntity objects with new ESI data
            EveEntity.objects.bulk_update_new_esi()

            # Delete structures that are no longer present in ESI
            SovereigntyStructure.objects.exclude(pk__in=esi_structure_ids).delete()

        # Set the cache to indicate that the structures have been updated
        cache.set(key=ESI_SOV_STRUCTURES_CACHE_KEY, value=True, timeout=100)

        logger.info(
            msg=f"{len(sov_structures)} sovereignty structures updated from ESI."
        )
