"""
Loading initial data into sovtimer tables
"""

# Django
from django.core.management.base import BaseCommand

# Alliance Auth (External Libs)
from eveuniverse.core.esitools import is_esi_online

# AA Sovereignty Timer
from sovtimer.tasks import update_sov_campaigns, update_sov_structures

ESI_SOV_STRUCTURES_CACHE_KEY = "sov_structures_cache"


def get_input(text):
    """
    Get input from the user
    """

    return input(text)


class Command(BaseCommand):
    """
    Imports initial sov campaign data
    """

    help = "Imports initial data"

    def _import_sov_data(self) -> None:  # pylint: disable=too-many-locals
        """
        Import sovereignty data

        :return:
        """

        if not is_esi_online():
            self.stdout.write(
                msg="ESI is currently offline. Can not start ESI related tasks. Aborting"
            )

            return

        update_sov_structures(force_refresh=True)
        update_sov_campaigns(force_refresh=True)

    def handle(self, *args, **options):  # pylint: disable=unused-argument
        """
        Ask before running …

        :param args:
        :param options:
        """

        self.stdout.write(
            msg=(
                "This will start the initial import for SOV campaigns and structures. "
                "It's quite a bit to import, so this might take a moment or two. "
                "Please be patient …"
            )
        )

        user_input = get_input(text="Are you sure you want to proceed? (yes/no)?")

        if user_input == "yes":
            self.stdout.write(msg="Starting import. Please stand by.")
            self._import_sov_data()
            self.stdout.write(msg=self.style.SUCCESS("Import complete!"))
        else:
            self.stdout.write(msg=self.style.WARNING("Aborted."))
