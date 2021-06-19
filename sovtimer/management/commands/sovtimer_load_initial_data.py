"""
loading initial data into sovtimer tables
"""

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction

from eveuniverse.core.esitools import is_esi_online
from eveuniverse.models import EveEntity, EveSolarSystem

from sovtimer.models import AaSovtimerCampaigns, AaSovtimerStructures

ESI_SOV_STRUCTURES_CACHE_KEY = "sov_structures_cache"


def get_input(text):
    """
    wrapped input to enable tz import
    """

    return input(text)


class Command(BaseCommand):
    help = "Imports initial data"

    def _import_sov_data(self) -> None:
        """
        import sovereignty data
        :return:
        """

        if not is_esi_online():
            self.stdout.write(
                "ESI is currently offline. Can not start ESI related tasks. Aborting"
            )
            return

        # Import sov structures
        structures_from_esi = AaSovtimerStructures.sov_structures_from_esi()
        if structures_from_esi:
            with transaction.atomic():
                AaSovtimerStructures.objects.all().delete()
                sov_structures = list()

                structure_count = 0

                for structure in structures_from_esi:
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
                        AaSovtimerStructures(
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

                AaSovtimerStructures.objects.bulk_create(
                    sov_structures,
                    batch_size=500,
                    ignore_conflicts=True,
                )

                EveEntity.objects.bulk_update_new_esi()

                cache.set(ESI_SOV_STRUCTURES_CACHE_KEY, True, 120)

                self.stdout.write(
                    (
                        "{structure_count} sovereignty structures imported from ESI."
                    ).format(structure_count=structure_count)
                )

        # import sov campaigns
        campaigns_from_esi = AaSovtimerCampaigns.sov_campaigns_from_esi()
        if campaigns_from_esi:
            with transaction.atomic():
                campaigns = list()

                campaign_count = 0

                for campaign in campaigns_from_esi:
                    campaign_current__defender, _ = EveEntity.objects.get_or_create(
                        id=campaign["defender_id"]
                    )

                    campaign_current__solar_system = EveSolarSystem.objects.get(
                        id=campaign["solar_system_id"]
                    )

                    campaign_current__defender_score = campaign["defender_score"]

                    try:
                        campaign_previous = AaSovtimerCampaigns.objects.get(
                            campaign_id=campaign["campaign_id"]
                        )

                        campaign_previous__progress_previous = (
                            campaign_previous.progress_previous
                        )

                        campaign_previous__progress = campaign_previous.defender_score
                        campaign_current__progress_previous = (
                            campaign_previous__progress
                        )

                        if (
                            campaign_previous__progress
                            == campaign_current__defender_score
                        ):
                            campaign_current__progress_previous = (
                                campaign_previous__progress_previous
                            )
                    except AaSovtimerCampaigns.DoesNotExist:
                        campaign_current__progress_previous = (
                            campaign_current__defender_score
                        )

                    campaigns.append(
                        AaSovtimerCampaigns(
                            attackers_score=campaign["attackers_score"],
                            campaign_id=campaign["campaign_id"],
                            defender=campaign_current__defender,
                            defender_score=campaign["defender_score"],
                            event_type=campaign["event_type"],
                            solar_system=campaign_current__solar_system,
                            start_time=campaign["start_time"],
                            structure_id=campaign["structure_id"],
                            progress_current=campaign_current__defender_score,
                            progress_previous=campaign_current__progress_previous,
                        )
                    )

                    campaign_count += 1

                AaSovtimerCampaigns.objects.all().delete()
                AaSovtimerCampaigns.objects.bulk_create(
                    campaigns,
                    batch_size=500,
                    ignore_conflicts=True,
                )

                EveEntity.objects.bulk_update_new_esi()

                self.stdout.write(
                    "{campaign_count} sovereignty campaigns imported from ESI.".format(
                        campaign_count=campaign_count
                    )
                )

    def handle(self, *args, **options):
        """
        ask before running ...
        :param args:
        :param options:
        """

        self.stdout.write(
            "This will start the initial import for SOV campaigns and structures. "
            "It's quite a bit to import, so this might take a moment or two. "
            "Please be patient ..."
        )

        user_input = get_input("Are you sure you want to proceed? (yes/no)?")

        if user_input == "yes":
            self.stdout.write("Starting import. Please stand by.")
            self._import_sov_data()
            self.stdout.write(self.style.SUCCESS("Import complete!"))
        else:
            self.stdout.write(self.style.WARNING("Aborted."))
