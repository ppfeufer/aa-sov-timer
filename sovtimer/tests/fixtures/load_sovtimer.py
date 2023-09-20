"""
Generate sov timer test objects from sovtimers.json.
"""

# Standard Library
import json
from pathlib import Path

# Alliance Auth (External Libs)
from eveuniverse.models import EveConstellation, EveEntity, EveRegion, EveSolarSystem

# AA Sovereignty Timer
from sovtimer.models import Campaign, SovereigntyStructure


def _load_sovtimer_data():
    """
    Load sov timer data

    :return:
    :rtype:
    """

    with open(file=Path(__file__).parent / "sovtimer.json", encoding="utf-8") as fp:
        return json.load(fp=fp)


_entities_data = _load_sovtimer_data()


def load_sovtimer():
    """
    Load sov timers test objects.
    """

    EveSolarSystem.objects.all().delete()
    EveConstellation.objects.all().delete()
    EveRegion.objects.all().delete()
    EveEntity.objects.all().delete()
    SovereigntyStructure.objects.all().delete()
    Campaign.objects.all().delete()

    for region_info in _entities_data.get("EveRegion"):
        EveRegion.objects.create(
            id=region_info.get("id"),
            name=region_info.get("name"),
            last_updated=region_info.get("last_updated"),
            description=region_info.get("description"),
        )

    for constellation_info in _entities_data.get("EveConstellation"):
        EveConstellation.objects.create(
            id=constellation_info.get("id"),
            name=constellation_info.get("name"),
            last_updated=constellation_info.get("last_updated"),
            position_x=constellation_info.get("position_x"),
            position_y=constellation_info.get("position_y"),
            position_z=constellation_info.get("position_z"),
            eve_region_id=constellation_info.get("eve_region_id"),
        )

    for solarsystem_info in _entities_data.get("EveSolarSystem"):
        EveSolarSystem.objects.create(
            id=solarsystem_info.get("id"),
            name=solarsystem_info.get("name"),
            last_updated=solarsystem_info.get("last_updated"),
            position_x=solarsystem_info.get("position_x"),
            position_y=solarsystem_info.get("position_y"),
            position_z=solarsystem_info.get("position_z"),
            security_status=solarsystem_info.get("security_status"),
            eve_constellation_id=solarsystem_info.get("eve_constellation_id"),
            eve_star_id=solarsystem_info.get("eve_star_id"),
            enabled_sections=solarsystem_info.get("enabled_sections"),
        )

    for entity_info in _entities_data.get("EveEntity"):
        EveEntity.objects.create(
            id=entity_info.get("id"),
            name=entity_info.get("name"),
            last_updated=entity_info.get("last_updated"),
            category=entity_info.get("category"),
        )

    for structures_info in _entities_data.get("SovereigntyStructure"):
        SovereigntyStructure.objects.create(
            structure_id=structures_info.get("structure_id"),
            alliance_id=structures_info.get("alliance_id"),
            solar_system_id=structures_info.get("solar_system_id"),
            structure_type_id=structures_info.get("structure_type_id"),
            vulnerability_occupancy_level=structures_info.get(
                "vulnerability_occupancy_level"
            ),
            vulnerable_end_time=structures_info.get("vulnerable_end_time"),
            vulnerable_start_time=structures_info.get("vulnerable_start_time"),
        )

    for campaigns_info in _entities_data.get("Campaign"):
        Campaign.objects.create(
            campaign_id=campaigns_info.get("campaign_id"),
            attackers_score=campaigns_info.get("attackers_score"),
            defender_score=campaigns_info.get("defender_score"),
            event_type=campaigns_info.get("event_type"),
            start_time=campaigns_info.get("start_time"),
            structure_id=campaigns_info.get("structure_id"),
            progress_current=campaigns_info.get("progress_current"),
            progress_previous=campaigns_info.get("progress_previous"),
        )
