# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
from eve_sde.models import SolarSystem

# AA Sovereignty Timer
from sovtimer.models import Alliance
from sovtimer.tasks import (
    run_sov_campaign_updates,
    update_sov_campaigns,
    update_sov_structures,
)
from sovtimer.tests import BaseTestCase


class TestUpdateSovStructures(BaseTestCase):
    """
    Test the update_sov_structures task
    """

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.models.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.models.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.models.SolarSystem.objects.filter")
    @patch("sovtimer.models.Campaign.objects.values_list")
    @patch("sovtimer.models.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.models.SovereigntyStructure.objects.values")
    def test_updates_structures_when_esi_returns_data(
        self,
        mock_values,
        mock_bulk_get_or_create,
        mock_campaign_values_list,
        mock_solar_system_filter,
        mock_exclude,
        mock_bulk_create,
        mock_get_sov_structures,
    ):
        """
        Test that the task correctly updates structures when ESI returns data

        :param mock_values:
        :type mock_values:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_campaign_values_list:
        :type mock_campaign_values_list:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :return:
        :rtype:
        """

        mock_get_sov_structures.return_value = [
            MagicMock(
                structure_id=1001,
                alliance_id=2001,
                solar_system_id=3001,
                structure_type_id=4001,
                vulnerability_occupancy_level=0.5,
                vulnerable_start_time="2023-01-01T12:00:00Z",
                vulnerable_end_time="2023-01-01T18:00:00Z",
            )
        ]
        mock_values.return_value = [
            {"structure_id": 1001, "vulnerability_occupancy_level": 0.5}
        ]
        mock_campaign_values_list.return_value = []
        mock_bulk_get_or_create.return_value = {
            2001: Alliance(alliance_id=2001, name="Alliance 2001")
        }
        mock_solar_system_filter.return_value = [SolarSystem(id=3001)]
        mock_bulk_create.return_value = None

        update_sov_structures(force_refresh=False)

        mock_get_sov_structures.assert_called_once_with(False)
        mock_bulk_get_or_create.assert_called_once_with(
            alliance_ids={2001}, force_refresh=False
        )
        mock_solar_system_filter.assert_called_once_with(id__in={3001})
        mock_bulk_create.assert_called_once()
        mock_exclude.assert_called_once_with(pk__in={1001})

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    def test_does_nothing_when_esi_returns_no_data(self, mock_get_sov_structures):
        """
        Test that the task does nothing when ESI returns no data

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :return:
        :rtype:
        """

        mock_get_sov_structures.return_value = None

        update_sov_structures(force_refresh=False)

        mock_get_sov_structures.assert_called_once_with(False)

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.models.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.models.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.models.SolarSystem.objects.filter")
    @patch("sovtimer.models.Campaign.objects.values_list")
    @patch("sovtimer.models.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.models.SovereigntyStructure.objects.values")
    def test_skips_invalid_or_duplicate_structures(
        self,
        mock_values,
        mock_bulk_get_or_create,
        mock_campaign_values_list,
        mock_solar_system_filter,
        mock_exclude,
        mock_bulk_create,
        mock_get_sov_structures,
    ):
        """
        Test that the task correctly skips structures with missing or duplicate IDs

        :param mock_values:
        :type mock_values:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_campaign_values_list:
        :type mock_campaign_values_list:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :return:
        :rtype:
        """

        mock_get_sov_structures.return_value = [
            MagicMock(structure_id=None, alliance_id=2001, solar_system_id=3001),
            MagicMock(structure_id=1001, alliance_id=2001, solar_system_id=3001),
            MagicMock(structure_id=1001, alliance_id=2001, solar_system_id=3001),
        ]
        mock_values.return_value = []
        mock_campaign_values_list.return_value = []
        mock_bulk_get_or_create.return_value = {
            2001: Alliance(alliance_id=2001, name="Alliance 2001")
        }
        mock_solar_system_filter.return_value = [SolarSystem(id=3001)]
        mock_bulk_create.return_value = None

        update_sov_structures(force_refresh=False)

        mock_get_sov_structures.assert_called_once_with(False)
        mock_bulk_create.assert_called_once()
        mock_exclude.assert_called_once_with(pk__in={1001})


class TestUpdateSovCampaigns(BaseTestCase):
    """
    Test the update_sov_campaigns task
    """

    @patch("sovtimer.models.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.models.Campaign.objects.bulk_create")
    @patch("sovtimer.models.Campaign.objects.all")
    @patch("sovtimer.models.Alliance.bulk_get_or_create_from_esi")
    def test_updates_campaigns_when_esi_returns_data(
        self,
        mock_bulk_get_or_create,
        mock_campaign_all,
        mock_bulk_create,
        mock_get_sov_campaigns,
    ):
        """
        Test that the task correctly updates campaigns when ESI returns data

        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_campaign_all:
        :type mock_campaign_all:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.return_value = [
            MagicMock(
                campaign_id=1001,
                defender_id=2001,
                attackers_score=0.3,
                defender_score=0.7,
                event_type="type1",
                start_time="2023-01-01T12:00:00Z",
                structure_id=3001,
            )
        ]
        empty_qs = MagicMock()
        empty_qs.__iter__.return_value = iter([])
        empty_qs.delete = MagicMock()
        mock_campaign_all.return_value = empty_qs

        mock_bulk_get_or_create.return_value = {2001: MagicMock()}
        mock_bulk_create.return_value = None

        update_sov_campaigns(force_refresh=False)

        mock_get_sov_campaigns.assert_called_once_with(False)
        mock_bulk_get_or_create.assert_called_once_with(
            alliance_ids={2001}, force_refresh=False
        )
        mock_bulk_create.assert_called_once()

    @patch("sovtimer.models.Campaign.get_sov_campaigns_from_esi")
    def test_does_nothing_when_esi_returns_no_data(self, mock_get_sov_campaigns):
        """
        Test that the task does nothing when ESI returns no data

        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.return_value = None

        update_sov_campaigns(force_refresh=False)

        mock_get_sov_campaigns.assert_called_once_with(False)

    @patch("sovtimer.models.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.models.Campaign.objects.bulk_create")
    @patch("sovtimer.models.Campaign.objects.all")
    @patch("sovtimer.models.Alliance.bulk_get_or_create_from_esi")
    def test_handles_existing_campaigns_correctly(
        self,
        mock_bulk_get_or_create,
        mock_campaign_all,
        mock_bulk_create,
        mock_get_sov_campaigns,
    ):
        """
        Test that the task correctly handles existing campaigns in the database

        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_campaign_all:
        :type mock_campaign_all:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.return_value = [
            MagicMock(
                campaign_id=1001,
                defender_id=2001,
                attackers_score=0.3,
                defender_score=0.7,
                event_type="type1",
                start_time="2023-01-01T12:00:00Z",
                structure_id=3001,
            )
        ]
        existing = MagicMock(
            campaign_id=1001, defender_score=0.7, progress_previous=0.5
        )
        existing_qs = MagicMock()
        existing_qs.__iter__.return_value = iter([existing])
        existing_qs.delete = MagicMock()
        mock_campaign_all.return_value = existing_qs

        mock_bulk_get_or_create.return_value = {2001: MagicMock()}
        mock_bulk_create.return_value = None

        update_sov_campaigns(force_refresh=False)

        mock_get_sov_campaigns.assert_called_once_with(False)
        mock_bulk_get_or_create.assert_called_once_with(
            alliance_ids={2001}, force_refresh=False
        )
        mock_bulk_create.assert_called_once()


class TestRunSovCampaignUpdates(BaseTestCase):
    """
    Test the run_sov_campaign_updates task
    """

    @patch("sovtimer.tasks.chain")
    @patch("sovtimer.tasks.update_sov_structures.s")
    @patch("sovtimer.tasks.update_sov_campaigns.s")
    def test_runs_both_tasks_in_sequence(
        self, mock_update_campaigns, mock_update_structures, mock_chain
    ):
        """
        Test that the task runs both update tasks in sequence with the correct priority

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :param mock_chain:
        :type mock_chain:
        :return:
        :rtype:
        """

        run_sov_campaign_updates()

        mock_update_structures.assert_called_once_with()
        mock_update_campaigns.assert_called_once_with()
        mock_update_structures.return_value.set.assert_called_once_with(priority=6)
        mock_update_campaigns.return_value.set.assert_called_once_with(priority=6)
        mock_chain.return_value.apply_async.assert_called_once()

    @patch("sovtimer.tasks.chain")
    @patch("sovtimer.tasks.update_sov_structures.s")
    @patch("sovtimer.tasks.update_sov_campaigns.s")
    def test_handles_no_priority_set(
        self, mock_update_campaigns, mock_update_structures, mock_chain
    ):
        """
        Test that the task runs both update tasks in sequence even if no priority is set

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :param mock_chain:
        :type mock_chain:
        :return:
        :rtype:
        """

        run_sov_campaign_updates()

        mock_update_structures.return_value.set.assert_called_once_with(priority=6)
        mock_update_campaigns.return_value.set.assert_called_once_with(priority=6)
        mock_chain.return_value.apply_async.assert_called_once()

    @patch("sovtimer.tasks.logger.info")
    @patch("sovtimer.tasks.chain")
    @patch("sovtimer.tasks.update_sov_structures.s")
    @patch("sovtimer.tasks.update_sov_campaigns.s")
    def test_logs_start_of_update_process(
        self,
        mock_update_campaigns,
        mock_update_structures,
        mock_chain,
        mock_logger_info,
    ):
        """
        Test that the task logs the start of the update process

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :param mock_chain:
        :type mock_chain:
        :param mock_logger_info:
        :type mock_logger_info:
        :return:
        :rtype:
        """

        run_sov_campaign_updates()

        mock_logger_info.assert_called_once_with(
            msg="Updating sovereignty structures and campaigns from ESI …"
        )
        mock_chain.return_value.apply_async.assert_called_once()
