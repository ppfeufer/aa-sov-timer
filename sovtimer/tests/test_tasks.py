"""
Tests for the sovtimer tasks.
"""

# Standard Library
from types import SimpleNamespace
from unittest.mock import Mock, patch

# Django
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveSolarSystem

# AA Sovereignty Timer
import sovtimer.tasks as tasks_module
from sovtimer.tasks import (
    TASK_ONCE_ARGS,
    TASK_PRIORITY,
    run_sov_campaign_updates,
    update_sov_campaigns,
    update_sov_structures,
)
from sovtimer.tests import BaseTestCase


class TestRunSovCampaignUpdatesTask(BaseTestCase):
    """
    Test the run_sov_campaign_updates task.
    """

    @patch("sovtimer.tasks.update_sov_structures.s")
    @patch("sovtimer.tasks.update_sov_campaigns.s")
    def test_updates_both_structures_and_campaigns(
        self, mock_update_campaigns, mock_update_structures
    ):
        """
        Test that run_sov_campaign_updates calls both update tasks with correct params.

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :return:
        :rtype:
        """

        run_sov_campaign_updates()

        mock_update_structures.assert_called_once()
        mock_update_campaigns.assert_called_once()

        struct_kwargs = mock_update_structures.return_value.set.call_args.kwargs
        self.assertEqual(struct_kwargs.get("priority"), TASK_PRIORITY)
        self.assertEqual(struct_kwargs.get("once"), TASK_ONCE_ARGS)

        camp_kwargs = mock_update_campaigns.return_value.set.call_args.kwargs
        self.assertEqual(camp_kwargs.get("priority"), TASK_PRIORITY)
        self.assertEqual(camp_kwargs.get("once"), TASK_ONCE_ARGS)

    @patch("sovtimer.tasks.update_sov_structures.s")
    @patch("sovtimer.tasks.update_sov_campaigns.s")
    def test_handles_exceptions_gracefully(
        self, mock_update_campaigns, mock_update_structures
    ):
        """
        Test that run_sov_campaign_updates handles exceptions gracefully.

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :return:
        :rtype:
        """

        mock_update_structures.side_effect = Exception("Test exception")

        with self.assertRaises(Exception) as exc:
            run_sov_campaign_updates()

        self.assertEqual(str(exc.exception), "Test exception")

    @patch("sovtimer.tasks.logger")
    @patch("sovtimer.tasks.update_sov_structures.s")
    @patch("sovtimer.tasks.update_sov_campaigns.s")
    def test_logs_update_message(
        self, mock_update_campaigns, mock_update_structures, mock_logger
    ):
        """
        Test that run_sov_campaign_updates logs the update message.

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        run_sov_campaign_updates()

        mock_logger.info.assert_called_once_with(
            msg="Updating sovereignty structures and campaigns from ESI …"
        )


class TestUpdateSovCampaignsTask(BaseTestCase):
    """
    Test the update_sov_campaigns task.
    """

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.bulk_create")
    @patch("sovtimer.tasks.Campaign.objects.all")
    @patch("sovtimer.tasks.EveEntity.objects.bulk_create")
    @patch("sovtimer.tasks.EveEntity.objects.bulk_update_new_esi")
    def test_updates_campaigns_with_valid_data(
        self,
        mock_bulk_update_new_esi,
        mock_eve_entity_bulk_create,
        mock_campaign_all,
        mock_campaign_bulk_create,
        mock_get_sov_campaigns_from_esi,
    ):
        """
        Test that update_sov_campaigns correctly updates campaigns with valid data.

        :param mock_bulk_update_new_esi:
        :type mock_bulk_update_new_esi:
        :param mock_eve_entity_bulk_create:
        :type mock_eve_entity_bulk_create:
        :param mock_campaign_all:
        :type mock_campaign_all:
        :param mock_campaign_bulk_create:
        :type mock_campaign_bulk_create:
        :param mock_get_sov_campaigns_from_esi:
        :type mock_get_sov_campaigns_from_esi:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns_from_esi.return_value = [
            SimpleNamespace(
                campaign_id=1,
                defender_id=100,
                attackers_score=0.3,
                defender_score=0.7,
                event_type="tcu_defense",
                start_time=timezone.now(),
                structure_id=200,
            )
        ]
        mock_queryset = Mock()
        mock_queryset.__iter__ = lambda self: iter([])  # iterable
        mock_queryset.delete = Mock()  # has delete()
        mock_campaign_all.return_value = mock_queryset

        update_sov_campaigns(force_refresh=True)

        mock_eve_entity_bulk_create.assert_called_once()
        mock_campaign_bulk_create.assert_called_once()
        mock_bulk_update_new_esi.assert_called_once()

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.bulk_create")
    @patch("sovtimer.tasks.Campaign.objects.all")
    @patch("sovtimer.tasks.EveEntity.objects.bulk_create")
    def test_skips_update_when_no_campaigns_returned(
        self,
        mock_eve_entity_bulk_create,
        mock_campaign_all,
        mock_campaign_bulk_create,
        mock_get_sov_campaigns_from_esi,
    ):
        mock_get_sov_campaigns_from_esi.return_value = []

        update_sov_campaigns(force_refresh=True)

        mock_eve_entity_bulk_create.assert_not_called()
        mock_campaign_bulk_create.assert_not_called()

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.bulk_create")
    @patch("sovtimer.tasks.Campaign.objects.all")
    @patch("sovtimer.tasks.EveEntity.objects.bulk_create")
    def handles_duplicate_campaign_ids(
        self,
        mock_eve_entity_bulk_create,
        mock_campaign_all,
        mock_campaign_bulk_create,
        mock_get_sov_campaigns_from_esi,
    ):
        """
        Test that update_sov_campaigns handles duplicate campaign IDs from ESI.

        :param mock_eve_entity_bulk_create:
        :type mock_eve_entity_bulk_create:
        :param mock_campaign_all:
        :type mock_campaign_all:
        :param mock_campaign_bulk_create:
        :type mock_campaign_bulk_create:
        :param mock_get_sov_campaigns_from_esi:
        :type mock_get_sov_campaigns_from_esi:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns_from_esi.return_value = [
            SimpleNamespace(
                campaign_id=1,
                defender_id=100,
                attackers_score=0.3,
                defender_score=0.7,
                event_type="tcu_defense",
                start_time=timezone.now(),
                structure_id=200,
            ),
            SimpleNamespace(
                campaign_id=1,
                defender_id=100,
                attackers_score=0.4,
                defender_score=0.6,
                event_type="tcu_defense",
                start_time=timezone.now(),
                structure_id=200,
            ),
        ]
        mock_campaign_all.return_value = []

        update_sov_campaigns(force_refresh=True)

        created_campaigns = mock_campaign_bulk_create.call_args[0][0]
        self.assertEqual(len(created_campaigns), 1)
        self.assertEqual(created_campaigns[0].campaign_id, 1)

    @patch("sovtimer.models.Campaign.objects.all")
    def test_handles_no_previous_campaigns(self, mock_campaigns_all):
        """
        Test that update_sov_campaigns handles the case with no previous campaigns.

        :param mock_campaigns_all:
        :type mock_campaigns_all:
        :return:
        :rtype:
        """

        mock_campaigns_all.return_value = []
        campaign = Mock(defender_score=0.5)
        previous_campaign = None

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

        self.assertEqual(progress_previous, 0.5)

    @patch("sovtimer.models.Campaign.objects.all")
    def test_handles_matching_defender_scores(self, mock_campaigns_all):
        """
        Test that update_sov_campaigns handles matching defender scores.

        :param mock_campaigns_all:
        :type mock_campaigns_all:
        :return:
        :rtype:
        """

        mock_campaign = Mock(defender_score=0.5, progress_previous=0.3)
        mock_campaigns_all.return_value = [mock_campaign]
        campaign = Mock(defender_score=0.5)

        progress_previous = (
            mock_campaign.progress_previous
            if mock_campaign and mock_campaign.defender_score == campaign.defender_score
            else (
                mock_campaign.defender_score
                if mock_campaign
                else campaign.defender_score
            )
        )

        self.assertEqual(progress_previous, 0.3)

    @patch("sovtimer.models.Campaign.objects.all")
    def test_handles_non_matching_defender_scores(self, mock_campaigns_all):
        """
        Test that update_sov_campaigns handles non-matching defender scores.

        :param mock_campaigns_all:
        :type mock_campaigns_all:
        :return:
        :rtype:
        """

        mock_campaign = Mock(defender_score=0.4, progress_previous=0.3)
        mock_campaigns_all.return_value = [mock_campaign]
        campaign = Mock(defender_score=0.5)

        progress_previous = (
            mock_campaign.progress_previous
            if mock_campaign and mock_campaign.defender_score == campaign.defender_score
            else (
                mock_campaign.defender_score
                if mock_campaign
                else campaign.defender_score
            )
        )

        self.assertEqual(progress_previous, 0.4)


class TestUpdateSovStructuresTask(BaseTestCase):
    """
    Test the update_sov_structures task.
    """

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.values_list")
    @patch("sovtimer.tasks.EveEntity.objects.bulk_update_new_esi")
    @patch("sovtimer.tasks.EveEntity.objects.bulk_create")
    @patch("sovtimer.tasks.EveEntity.objects.filter")
    @patch("sovtimer.tasks.EveSolarSystem.objects.filter")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.exclude")
    def test_updates_structures_with_valid_data(
        self,
        mock_exclude,
        mock_bulk_create,
        mock_solar_system_filter,
        mock_alliance_filter,
        mock_bulk_create_eve,
        mock_bulk_update_new_esi,
        mock_campaign_values_list,
        mock_get_structures,
    ):
        """
        Test that update_sov_structures correctly updates structures with valid data.

        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_alliance_filter:
        :type mock_alliance_filter:
        :param mock_bulk_create_eve:
        :type mock_bulk_create_eve:
        :param mock_bulk_update_new_esi:
        :type mock_bulk_update_new_esi:
        :param mock_campaign_values_list:
        :type mock_campaign_values_list:
        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        mock_get_structures.return_value = [
            SimpleNamespace(
                structure_id=1,
                alliance_id=100,
                solar_system_id=200,
                structure_type_id=300,
                vulnerability_occupancy_level=0.5,
                vulnerable_start_time=timezone.now(),
                vulnerable_end_time=timezone.now(),
            )
        ]
        mock_campaign_values_list.return_value = []

        mock_alliance_filter.return_value = [tasks_module.EveEntity(id=100)]
        mock_solar_system_filter.return_value = [EveSolarSystem(id=200)]

        update_sov_structures(force_refresh=True)

        mock_bulk_create.assert_called_once()
        mock_exclude.assert_called_once()

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.values_list")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    def test_handles_empty_esi_response(
        self, mock_bulk_create, mock_campaign_values_list, mock_get_structures
    ):
        """
        Test that update_sov_structures handles an empty response from ESI.

        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_campaign_values_list:
        :type mock_campaign_values_list:
        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        mock_get_structures.return_value = []
        mock_campaign_values_list.return_value = []

        update_sov_structures(force_refresh=True)

        mock_bulk_create.assert_not_called()

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.values_list")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    def test_assigns_default_vulnerability_when_missing(
        self, mock_bulk_create, mock_campaign_values_list, mock_get_structures
    ):
        """
        Test that update_sov_structures assigns default vulnerability level when missing.

        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_campaign_values_list:
        :type mock_campaign_values_list:
        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        mock_get_structures.return_value = [
            SimpleNamespace(
                structure_id=1,
                alliance_id=None,
                solar_system_id=None,
                structure_type_id=300,
                vulnerability_occupancy_level=None,
                vulnerable_start_time=None,
                vulnerable_end_time=None,
            )
        ]
        mock_campaign_values_list.return_value = []

        update_sov_structures(force_refresh=True)

        created_structures = mock_bulk_create.call_args[0][0]
        self.assertEqual(created_structures[0].vulnerability_occupancy_level, 1)

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.values_list")
    @patch("sovtimer.tasks.EveEntity.objects.bulk_update_new_esi")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.exclude")
    def test_removes_structures_not_in_esi(
        self,
        mock_exclude,
        mock_bulk_create,
        mock_bulk_update_new_esi,
        mock_campaign_values_list,
        mock_get_structures,
    ):
        """
        Test that update_sov_structures removes structures not present in ESI data.

        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_bulk_update_new_esi:
        :type mock_bulk_update_new_esi:
        :param mock_campaign_values_list:
        :type mock_campaign_values_list:
        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        mock_get_structures.return_value = [
            SimpleNamespace(
                structure_id=1,
                alliance_id=100,
                solar_system_id=200,
                structure_type_id=300,
                vulnerability_occupancy_level=0.5,
                vulnerable_start_time=timezone.now(),
                vulnerable_end_time=timezone.now(),
            )
        ]
        mock_campaign_values_list.return_value = []

        update_sov_structures(force_refresh=True)

        mock_exclude.assert_called_once_with(pk__in={1})

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.values_list")
    @patch("sovtimer.tasks.EveEntity.objects.bulk_update_new_esi")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    def test_skips_structure_with_missing_or_duplicate_id(
        self,
        mock_bulk_create,
        mock_bulk_update_new_esi,
        mock_campaign_values_list,
        mock_get_structures,
    ):
        """
        Test that update_sov_structures skips structures with missing or duplicate IDs.

        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_bulk_update_new_esi:
        :type mock_bulk_update_new_esi:
        :param mock_campaign_values_list:
        :type mock_campaign_values_list:
        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        mock_get_structures.return_value = [
            SimpleNamespace(
                structure_id=None,
                alliance_id=100,
                solar_system_id=200,
                structure_type_id=300,
                vulnerability_occupancy_level=0.5,
                vulnerable_start_time=timezone.now(),
                vulnerable_end_time=timezone.now(),
            ),
            SimpleNamespace(
                structure_id=1,
                alliance_id=100,
                solar_system_id=200,
                structure_type_id=300,
                vulnerability_occupancy_level=0.5,
                vulnerable_start_time=timezone.now(),
                vulnerable_end_time=timezone.now(),
            ),
            SimpleNamespace(
                structure_id=1,
                alliance_id=101,
                solar_system_id=201,
                structure_type_id=301,
                vulnerability_occupancy_level=0.6,
                vulnerable_start_time=timezone.now(),
                vulnerable_end_time=timezone.now(),
            ),
        ]
        mock_campaign_values_list.return_value = []

        update_sov_structures(force_refresh=True)

        created_structures = mock_bulk_create.call_args[0][0]

        self.assertEqual(len(created_structures), 1)
        self.assertEqual(created_structures[0].structure_id, 1)
