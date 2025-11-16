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
from sovtimer.models import Campaign, SovereigntyStructure
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

    @patch("sovtimer.models.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.models.Campaign.objects.bulk_create")
    @patch("sovtimer.models.Campaign.objects.all")
    @patch("sovtimer.models.EveEntity.objects.bulk_create")
    @patch("sovtimer.models.EveEntity.objects.bulk_update_new_esi")
    @patch("sovtimer.tasks.logger.info")
    @patch("sovtimer.tasks.logger.debug")
    def test_updates_campaigns_and_logs_info(
        self,
        mock_logger_debug,
        mock_logger_info,
        mock_bulk_update_new_esi,
        mock_eve_bulk_create,
        mock_campaigns_all,
        mock_bulk_create,
        mock_get_campaigns,
    ):
        """
        Test that update_sov_campaigns correctly updates campaigns and logs info.

        :param mock_logger_debug:
        :type mock_logger_debug:
        :param mock_logger_info:
        :type mock_logger_info:
        :param mock_bulk_update_new_esi:
        :type mock_bulk_update_new_esi:
        :param mock_eve_bulk_create:
        :type mock_eve_bulk_create:
        :param mock_campaigns_all:
        :type mock_campaigns_all:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_queryset = Mock()
        mock_queryset.__iter__ = lambda self: iter(
            [Mock(campaign_id=1), Mock(campaign_id=2)]
        )
        mock_campaigns_all.return_value = mock_queryset

        mock_get_campaigns.return_value = [
            Mock(
                campaign_id=1,
                defender_id=1001,
                attackers_score=0.5,
                defender_score=0.7,
                event_type="ihub_defense",
                start_time="2023-10-01T12:00:00Z",
                structure_id=2001,
            ),
            Mock(
                campaign_id=2,
                defender_id=1002,
                attackers_score=0.3,
                defender_score=0.6,
                event_type="ihub_defense",
                start_time="2023-10-02T12:00:00Z",
                structure_id=2002,
            ),
        ]

        update_sov_campaigns()

        mock_logger_debug.assert_called_with(
            msg="Number of sovereignty campaigns from ESI: 2"
        )
        mock_logger_info.assert_called_with(
            msg="2 sovereignty campaigns updated from ESI."
        )
        mock_eve_bulk_create.assert_called_once()
        mock_bulk_create.assert_called_once()
        mock_bulk_update_new_esi.assert_called_once()

    @patch("sovtimer.models.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.models.Campaign.objects.all")
    @patch("sovtimer.tasks.logger.info")
    @patch("sovtimer.tasks.logger.debug")
    def test_handles_no_campaigns_from_esi(
        self,
        mock_logger_debug,
        mock_logger_info,
        mock_campaigns_all,
        mock_get_campaigns,
    ):
        """
        Test that update_sov_campaigns handles no campaigns returned from ESI.

        :param mock_logger_debug:
        :type mock_logger_debug:
        :param mock_logger_info:
        :type mock_logger_info:
        :param mock_campaigns_all:
        :type mock_campaigns_all:
        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = ""

        update_sov_campaigns()

        mock_logger_debug.assert_called_with(
            msg="Number of sovereignty campaigns from ESI: 0"
        )
        mock_logger_info.assert_called_with(
            msg="0 sovereignty campaigns updated from ESI."
        )
        mock_campaigns_all.return_value.delete.assert_called_once()

    @patch("sovtimer.models.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.models.Campaign.objects.all")
    @patch("sovtimer.models.Campaign.objects.bulk_create")
    @patch("sovtimer.models.EveEntity.objects.bulk_create")
    @patch("sovtimer.models.EveEntity.objects.bulk_update_new_esi")
    @patch("sovtimer.tasks.logger.info")
    @patch("sovtimer.tasks.logger.debug")
    def test_deletes_existing_campaigns_when_new_campaigns_arrive(
        self,
        mock_logger_debug,
        mock_logger_info,
        mock_bulk_update_new_esi,
        mock_eve_bulk_create,
        mock_bulk_create,
        mock_campaigns_all,
        mock_get_campaigns,
    ):
        mock_queryset = Mock()
        mock_queryset.__iter__ = lambda self: iter([Mock(campaign_id=1)])
        mock_queryset.delete = Mock()
        mock_campaigns_all.return_value = mock_queryset

        mock_get_campaigns.return_value = [
            Mock(
                campaign_id=1,
                defender_id=1001,
                attackers_score=0.5,
                defender_score=0.7,
                event_type="ihub_defense",
                start_time="2023-10-01T12:00:00Z",
                structure_id=2001,
            )
        ]

        update_sov_campaigns()

        mock_campaigns_all.return_value.delete.assert_called_once()
        mock_bulk_create.assert_called_once()
        mock_eve_bulk_create.assert_called_once()
        mock_bulk_update_new_esi.assert_called_once()
        mock_logger_info.assert_called_with(
            msg="1 sovereignty campaigns updated from ESI."
        )

    @patch("sovtimer.models.EveEntity.objects.bulk_create")
    @patch("sovtimer.models.EveEntity.objects.bulk_update_new_esi")
    def test_preserves_previous_progress_previous_when_defender_score_unchanged(
        self, mock_bulk_update_new_esi, mock_eve_bulk_create
    ):
        now = timezone.now()
        # Create the referenced SovereigntyStructure so FK constraint is satisfied
        SovereigntyStructure.objects.create(
            structure_id=100,
            alliance_id=None,
            solar_system_id=None,
            structure_type_id=0,
            vulnerability_occupancy_level=0,
            vulnerable_start_time=now,
            vulnerable_end_time=now,
        )

        # Existing campaign in DB with previous progress_previous
        Campaign.objects.create(
            attackers_score=0,
            campaign_id=1,
            defender_score=50,
            event_type="test",
            start_time=now,
            structure_id=100,
            progress_current=50,
            progress_previous=20,
        )

        esi_campaign = SimpleNamespace(
            attackers_score=0,
            campaign_id=1,
            defender_id=1001,
            defender_score=50,  # unchanged
            event_type="test",
            start_time=now,
            structure_id=100,
        )

        with patch(
            "sovtimer.tasks.Campaign.get_sov_campaigns_from_esi",
            return_value=[esi_campaign],
        ):
            update_sov_campaigns(force_refresh=True)

        created = Campaign.objects.get(campaign_id=1)
        self.assertEqual(created.progress_current, 50)
        self.assertEqual(created.progress_previous, 20)

    @patch("sovtimer.models.EveEntity.objects.bulk_create")
    @patch("sovtimer.models.EveEntity.objects.bulk_update_new_esi")
    def test_sets_progress_previous_to_current_defender_score_when_defender_score_changed(
        self, mock_bulk_update_new_esi, mock_eve_bulk_create
    ):
        now = timezone.now()
        # Create the referenced SovereigntyStructure so FK constraint is satisfied
        SovereigntyStructure.objects.create(
            structure_id=200,
            alliance_id=None,
            solar_system_id=None,
            structure_type_id=0,
            vulnerability_occupancy_level=0,
            vulnerable_start_time=now,
            vulnerable_end_time=now,
        )

        # Existing campaign in DB with a different defender_score
        Campaign.objects.create(
            attackers_score=0,
            campaign_id=2,
            defender_score=40,
            event_type="test",
            start_time=now,
            structure_id=200,
            progress_current=40,
            progress_previous=10,
        )

        esi_campaign = SimpleNamespace(
            attackers_score=0,
            campaign_id=2,
            defender_id=1002,
            defender_score=60,  # changed
            event_type="test",
            start_time=now,
            structure_id=200,
        )

        with patch(
            "sovtimer.tasks.Campaign.get_sov_campaigns_from_esi",
            return_value=[esi_campaign],
        ):
            update_sov_campaigns(force_refresh=True)

        created = Campaign.objects.get(campaign_id=2)
        self.assertEqual(created.progress_current, 60)
        self.assertEqual(created.progress_previous, 40)

    @patch("sovtimer.models.EveEntity.objects.bulk_create")
    @patch("sovtimer.models.EveEntity.objects.bulk_update_new_esi")
    def test_sets_progress_previous_to_current_when_no_existing_campaign(
        self, mock_bulk_update_new_esi, mock_eve_bulk_create
    ):
        now = timezone.now()
        Campaign.objects.all().delete()

        # Create the referenced SovereigntyStructure so FK constraint is satisfied
        SovereigntyStructure.objects.create(
            structure_id=300,
            alliance_id=None,
            solar_system_id=None,
            structure_type_id=0,
            vulnerability_occupancy_level=0,
            vulnerable_start_time=now,
            vulnerable_end_time=now,
        )

        esi_campaign = SimpleNamespace(
            attackers_score=0,
            campaign_id=3,
            defender_id=1003,
            defender_score=30,
            event_type="test",
            start_time=now,
            structure_id=300,
        )

        with patch(
            "sovtimer.tasks.Campaign.get_sov_campaigns_from_esi",
            return_value=[esi_campaign],
        ):
            update_sov_campaigns(force_refresh=True)

        created = Campaign.objects.get(campaign_id=3)
        self.assertEqual(created.progress_current, 30)
        self.assertEqual(created.progress_previous, 30)


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
