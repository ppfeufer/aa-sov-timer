"""
The tasks
"""

# Third Party
from celery import chain, shared_task
from eve_sde.models import SolarSystem

# Django
from django.core.cache import cache
from django.db import transaction

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.constants import Constants
from sovtimer.models import Alliance, Campaign, SovereigntyStructure
from sovtimer.providers import AppLogger

logger = AppLogger(my_logger=get_extension_logger(name=__name__), prefix=__title__)


# Params for all tasks
TASK_DEFAULTS = {
    **{
        "time_limit": Constants.TASK_RUN_TTL,
        "max_retries": Constants.TASK_ESI_MAX_RETRIES,
        "default_retry_delay": Constants.TASK_DEFAULT_RETRY_DELAY,
    },
    **{"base": QueueOnce},
}


@shared_task(**TASK_DEFAULTS)
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
    logger.info(msg="Updating sovereignty structures and campaigns from ESI…")

    # Chain the update tasks for structures and campaigns, and execute them asynchronously
    # Use immutable signatures (.si) so the result of the previous task is NOT
    # passed as the first positional argument to the next task.
    chain(
        update_sov_structures.si(use_etags=True, force_refresh=False).set(
            priority=Constants.TASK_PRIORITY
        ),
        update_sov_campaigns.si(use_etags=True, force_refresh=False).set(
            priority=Constants.TASK_PRIORITY
        ),
    ).apply_async()


@shared_task(**TASK_DEFAULTS)
def update_sov_campaigns(use_etags: bool = True, force_refresh: bool = False) -> None:
    """
    Update sovereignty campaigns from ESI (EVE Swagger Interface).

    This task fetches sovereignty campaigns from the EVE Swagger Interface (ESI),
    processes the data, and updates the database with the latest information. It ensures
    that all related entities (e.g., defenders) are pre-fetched or created as needed to
    minimize database hits.

    :param use_etags: Whether to use ETags instead of hashes.
    :type use_etags: bool
    :param force_refresh: Whether to force refresh the data from ESI.
    :type force_refresh: bool
    :return: None
    :rtype: None
    """

    # Fetch campaigns from ESI
    campaigns_from_esi = Campaign.get_sov_campaigns_from_esi(
        use_etags=use_etags, force_refresh=force_refresh
    )

    # Exit early if no campaigns are returned
    if campaigns_from_esi is None:
        return

    # Log the number of campaigns fetched from ESI
    logger.debug(f"Number of sovereignty campaigns from ESI: {len(campaigns_from_esi)}")

    # Collect all unique defender IDs from the fetched campaigns
    defender_ids = {campaign.defender_id for campaign in campaigns_from_esi}

    # Fetch existing campaigns from the database and map them by campaign ID
    existing_campaigns = {c.campaign_id: c for c in Campaign.objects.all()}

    # Ensure all defenders exist in the Alliance model
    Alliance.bulk_get_or_create_from_esi(
        alliance_ids=defender_ids, force_refresh=force_refresh
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
                campaign_id=campaign.campaign_id,
                attackers_score=campaign.attackers_score,
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

    # Log the number of campaigns updated
    logger.info(f"{len(campaigns)} sovereignty campaigns updated from ESI.")


@shared_task(**TASK_DEFAULTS)
def update_sov_structures(  # pylint: disable=too-many-locals
    use_etags: bool = True, force_refresh: bool = False
) -> None:
    """
    Update sovereignty structures from ESI (EVE Swagger Interface).

    This task fetches sovereignty structures from ESI, processes the data, and updates
    the database with the latest information. It ensures that all related entities
    (alliances and solar systems) are pre-fetched or created as needed to minimize
    database hits.

    :param use_etags: Whether to use ETags instead of hashes.
    :type use_etags: bool
    :param force_refresh: Whether to force refresh the data from ESI.
    :type force_refresh: bool
    :return: None
    :rtype: None
    """

    if cache.get(Constants.TASK_STRUCTURE_CACHE_KEY) and force_refresh is False:
        logger.debug(
            "Cache TTL not yet expired for sovereignty structures, skipping update."
        )

        return

    cache.set(
        key=Constants.TASK_STRUCTURE_CACHE_KEY,
        value=True,
        timeout=Constants.TASK_STRUCTURE_CACHE_TTL,
    )

    # Fetch sovereignty structures from ESI
    structures_from_esi = SovereigntyStructure.get_sov_structures_from_esi(
        use_etags=use_etags, force_refresh=force_refresh
    )

    # Exit early if no structures are returned
    if structures_from_esi is None:
        return

    logger.debug(
        msg=f"Number of sovereignty structures from ESI: {len(structures_from_esi or [])}"
    )

    # Collect all alliance IDs from the fetched structures
    alliance_ids = {s["alliance_id"] for s in structures_from_esi}

    # Fetch alliances from the database or create them if they don't exist
    alliances = Alliance.bulk_get_or_create_from_esi(
        alliance_ids=alliance_ids, force_refresh=force_refresh
    )

    # Collect all solar system IDs from the fetched structures
    solar_system_ids = {s["solar_system_id"] for s in structures_from_esi}

    # Fetch solar systems from the database
    solar_systems = {
        ss.id: ss for ss in SolarSystem.objects.filter(id__in=solar_system_ids)
    }

    esi_structure_ids = set()  # Track structure IDs from ESI to avoid duplicates
    sov_structures = []  # List to hold SovereigntyStructure instances for bulk creation

    # Build SovereigntyStructure instances from the fetched data
    for structure in structures_from_esi:
        # Skip structures with missing or duplicate IDs
        if (
            not structure["sovereignty_hub"]["id"]
            or structure["sovereignty_hub"]["id"] in esi_structure_ids
        ):
            continue

        esi_structure_ids.add(structure["sovereignty_hub"]["id"])

        # Determine the vulnerability level. The value is provided by the
        # alliance development data at:
        # structure['development']['activity_defense_multiplier']
        try:
            activity_defense_multiplier = structure["development"][
                "activity_defense_multiplier"
            ]
        except AttributeError:
            activity_defense_multiplier = None

        vulnerability_occupancy_level = (
            activity_defense_multiplier
            if activity_defense_multiplier is not None
            else 1
        )

        # Safely retrieve vulnerability window start/end if available
        sov_hub = (
            structure.get("sovereignty_hub") if isinstance(structure, dict) else None
        )
        vulnerability_window = None
        vulnerable_start_time = None
        vulnerable_end_time = None

        if isinstance(sov_hub, dict):
            vulnerability_window = sov_hub.get("vulnerability_window")

        if isinstance(vulnerability_window, dict):
            vulnerable_start_time = vulnerability_window.get("start")
            vulnerable_end_time = vulnerability_window.get("end")

        # Create a SovereigntyStructure instance for bulk creation. Use .get on alliances and solar_systems to avoid KeyError if missing.
        sov_structures.append(
            SovereigntyStructure(
                alliance=alliances.get(structure["alliance_id"]),
                solar_system=solar_systems.get(structure["solar_system_id"]),
                structure_id=structure["sovereignty_hub"]["id"],
                vulnerability_occupancy_level=vulnerability_occupancy_level,
                vulnerable_start_time=vulnerable_start_time,
                vulnerable_end_time=vulnerable_end_time,
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
                "vulnerability_occupancy_level",
                "vulnerable_end_time",
                "vulnerable_start_time",
            ],
        )

        # Remove structures that are no longer in the ESI data
        SovereigntyStructure.objects.exclude(pk__in=esi_structure_ids).delete()

    logger.info(f"{len(sov_structures)} sovereignty structures updated from ESI.")
