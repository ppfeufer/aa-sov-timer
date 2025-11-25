"""
The tasks
"""

# Third Party
from celery import chain, shared_task

# Django
from django.db import transaction

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity, EveSolarSystem

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.models import Campaign, SovereigntyStructure
from sovtimer.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(name=__name__), prefix=__title__)


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
    Update all sovereignty campaigns and structures.

    This task triggers the update of sovereignty campaigns and structures by chaining
    two Celery tasks: `update_sov_structures` and `update_sov_campaigns`. It ensures
    that both tasks are executed sequentially and with the specified priority and
    task-once arguments.

    The task is designed to be scheduled periodically, for example, every 30 seconds,
    to keep the sovereignty data up-to-date. Below is an example of how to configure
    this task in the `local.py` settings file:

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

    # Log the start of the update process
    logger.info(msg="Updating sovereignty structures and campaigns from ESI …")

    # Chain the update tasks for structures and campaigns, and execute them asynchronously
    chain(
        update_sov_structures.s().set(priority=TASK_PRIORITY, once=TASK_ONCE_ARGS),
        update_sov_campaigns.s().set(priority=TASK_PRIORITY, once=TASK_ONCE_ARGS),
    ).apply_async()


@shared_task(**TASK_DEFAULTS_ONCE)
def update_sov_campaigns(force_refresh: bool = False) -> None:
    """
    Update sovereignty campaigns from ESI (EVE Swagger Interface).

    This task fetches sovereignty campaigns from the EVE Swagger Interface (ESI),
    processes the data, and updates the database with the latest information. It ensures
    that all related entities (e.g., defenders) are pre-fetched or created as needed to
    minimize database hits.

    :param force_refresh: Whether to force refresh the data from ESI.
    :type force_refresh: bool
    :return: None
    :rtype: None
    """

    # Fetch campaigns from ESI
    campaigns_from_esi = Campaign.get_sov_campaigns_from_esi(force_refresh)

    # Exit early if no campaigns are returned
    if campaigns_from_esi is None:
        return

    # Log the number of campaigns fetched from ESI
    logger.debug(f"Number of sovereignty campaigns from ESI: {len(campaigns_from_esi)}")

    # Collect all unique defender IDs from the fetched campaigns
    defender_ids = {campaign.defender_id for campaign in campaigns_from_esi}

    # Fetch existing campaigns from the database and map them by campaign ID
    existing_campaigns = {c.campaign_id: c for c in Campaign.objects.all()}

    # Ensure all defenders exist in the EveEntity model
    EveEntity.objects.bulk_create(
        [EveEntity(id=defender_id) for defender_id in defender_ids],
        ignore_conflicts=True,
    )

    # Prepare a list to hold new Campaign instances for bulk creation
    campaigns = []
    for campaign in campaigns_from_esi:
        # Retrieve the previous campaign from the database, if it exists
        previous_campaign = existing_campaigns.get(campaign.campaign_id)

        # Determine the progress_previous value based on the defender score
        progress_previous = (
            previous_campaign.progress_previous
            if previous_campaign
            and previous_campaign.defender_score == campaign.defender_score
            else (
                previous_campaign.defender_score
                if previous_campaign
                else campaign.defender_score
            )
        )

        # Create a new Campaign instance
        campaigns.append(
            Campaign(
                attackers_score=campaign.attackers_score,
                campaign_id=campaign.campaign_id,
                defender_score=campaign.defender_score,
                event_type=campaign.event_type,
                start_time=campaign.start_time,
                structure_id=campaign.structure_id,
                progress_current=campaign.defender_score,
                progress_previous=progress_previous,
            )
        )

    # Delete all existing campaigns from the database
    Campaign.objects.all().delete()

    # Bulk create the new campaigns in the database
    Campaign.objects.bulk_create(campaigns, batch_size=500)

    # Update EVE entities from ESI
    EveEntity.objects.bulk_update_new_esi()

    # Log the number of campaigns updated
    logger.info(f"{len(campaigns)} sovereignty campaigns updated from ESI.")


@shared_task(**TASK_DEFAULTS_ONCE)
def update_sov_structures(force_refresh: bool = False) -> None:
    """
    Update sovereignty structures from ESI (EVE Swagger Interface).

    This task fetches sovereignty structures from ESI, processes the data, and updates
    the database with the latest information. It ensures that all related entities
    (alliances and solar systems) are pre-fetched or created as needed to minimize
    database hits.

    :param force_refresh: Whether to force refresh the data from ESI.
    :type force_refresh: bool
    :return: None
    :rtype: None
    """

    # Fetch sovereignty structures from ESI
    structures_from_esi = SovereigntyStructure.get_sov_structures_from_esi(
        force_refresh
    )

    # Exit early if no structures are returned
    if structures_from_esi is None:
        return

    logger.debug(
        msg=f"Number of sovereignty structures from ESI: {len(structures_from_esi or [])}"
    )

    # Pre-fetch current structures and their vulnerability levels for fast lookup
    current_structures = {
        s["structure_id"]: s["vulnerability_occupancy_level"]
        for s in SovereigntyStructure.objects.values(
            "structure_id", "vulnerability_occupancy_level"
        )
    }

    # Get all structure IDs that are currently part of campaigns
    campaign_structure_ids = set(
        Campaign.objects.values_list("structure_id", flat=True)
    )

    # Collect all alliance IDs from the fetched structures
    alliance_ids = {s.alliance_id for s in structures_from_esi if s.alliance_id}

    # Ensure all alliances exist in the EveEntity model
    EveEntity.objects.bulk_create(
        [EveEntity(id=aid) for aid in alliance_ids], ignore_conflicts=True
    )

    # Fetch alliances from the database
    alliances = {e.id: e for e in EveEntity.objects.filter(id__in=alliance_ids)}

    # Collect all solar system IDs from the fetched structures
    solar_system_ids = {
        s.solar_system_id for s in structures_from_esi if s.solar_system_id
    }

    # Fetch solar systems from the database
    solar_systems = {
        ss.id: ss for ss in EveSolarSystem.objects.filter(id__in=solar_system_ids)
    }

    esi_structure_ids = set()  # Track structure IDs from ESI to avoid duplicates
    sov_structures = []  # List to hold SovereigntyStructure instances for bulk creation

    # Build SovereigntyStructure instances from the fetched data
    for structure in structures_from_esi:
        # Skip structures with missing or duplicate IDs
        if not structure.structure_id or structure.structure_id in esi_structure_ids:
            continue

        esi_structure_ids.add(structure.structure_id)

        # Determine the vulnerability level based on current structures or campaigns
        vulnerability = (
            current_structures.get(structure.structure_id, 1)
            if structure.structure_id in campaign_structure_ids
            else structure.vulnerability_occupancy_level or 1
        )

        # Create a SovereigntyStructure instance
        sov_structures.append(
            SovereigntyStructure(
                alliance=alliances.get(structure.alliance_id),
                solar_system=solar_systems.get(structure.solar_system_id),
                structure_id=structure.structure_id,
                structure_type_id=structure.structure_type_id,
                vulnerability_occupancy_level=vulnerability,
                vulnerable_end_time=structure.vulnerable_end_time,
                vulnerable_start_time=structure.vulnerable_start_time,
            )
        )

    # Perform bulk database operations within a transaction
    with transaction.atomic():
        # Bulk create or update sovereignty structures
        SovereigntyStructure.objects.bulk_create(
            sov_structures,
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
        # Update EVE entities from ESI
        EveEntity.objects.bulk_update_new_esi()

        # Remove structures that are no longer in the ESI data
        SovereigntyStructure.objects.exclude(pk__in=esi_structure_ids).delete()

    logger.info(f"{len(sov_structures)} sovereignty structures updated from ESI.")
