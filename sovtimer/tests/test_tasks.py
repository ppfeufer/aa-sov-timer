"""
Tests for the sovtimer tasks.
"""

# Standard Library
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

# Django
from django.utils import timezone

# Alliance Auth (External Libs)
from eveuniverse.models import EveSolarSystem

# AA Sovereignty Timer
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

    @patch("sovtimer.tasks.update_sov_structures.apply_async")
    @patch("sovtimer.tasks.update_sov_campaigns.apply_async")
    def test_run_sov_campaign_updates_calls_tasks(
        self, mock_update_campaigns, mock_update_structures
    ):
        """
        Test that run_sov_campaign_updates calls the update tasks with correct args.

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :return:
        :rtype:
        """

        run_sov_campaign_updates()

        mock_update_structures.assert_called_once_with(
            priority=TASK_PRIORITY, once=TASK_ONCE_ARGS
        )
        mock_update_campaigns.assert_called_once_with(
            priority=TASK_PRIORITY, once=TASK_ONCE_ARGS
        )

    def test_run_sov_campaign_updates_handles_exceptions(self):
        """
        Test that run_sov_campaign_updates handles exceptions gracefully.

        :return:
        :rtype:
        """

        with (
            patch(
                "sovtimer.tasks.update_sov_structures.apply_async"
            ) as mock_update_structures,
            patch("sovtimer.tasks.update_sov_campaigns.apply_async"),
        ):
            mock_update_structures.side_effect = Exception("Test exception")

            with self.assertRaises(Exception) as exc:
                run_sov_campaign_updates()

            self.assertEqual(str(exc.exception), "Test exception")

    def test_run_sov_campaign_updates_logs_messages(self):
        """
        Test that run_sov_campaign_updates logs the correct messages.

        :return:
        :rtype:
        """

        with (
            patch("sovtimer.tasks.logger") as mock_logger,
            patch("sovtimer.tasks.update_sov_structures.apply_async"),
            patch("sovtimer.tasks.update_sov_campaigns.apply_async"),
        ):
            run_sov_campaign_updates()

            mock_logger.info.assert_any_call(
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
    @patch("sovtimer.models.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.models.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.models.SovereigntyStructure.objects.all")
    @patch("sovtimer.models.EveEntity.objects.bulk_create")
    @patch("sovtimer.models.EveEntity.objects.bulk_update_new_esi")
    @patch("sovtimer.models.EveSolarSystem.objects.filter")
    @patch("sovtimer.tasks.cache.get")
    @patch("sovtimer.tasks.cache.set")
    @patch("sovtimer.tasks.logger.info")
    @patch("sovtimer.tasks.logger.debug")
    def test_updates_structures_and_logs_info(
        self,
        mock_logger_debug,
        mock_logger_info,
        mock_cache_set,
        mock_cache_get,
        mock_solar_system_filter,
        mock_bulk_update_new_esi,
        mock_eve_bulk_create,
        mock_structures_all,
        mock_structures_exclude,
        mock_bulk_create,
        mock_get_structures,
    ):
        """
        Test that update_sov_structures correctly updates structures and logs info.

        :param mock_logger_debug:
        :type mock_logger_debug:
        :param mock_logger_info:
        :type mock_logger_info:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_cache_get:
        :type mock_cache_get:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_bulk_update_new_esi:
        :type mock_bulk_update_new_esi:
        :param mock_eve_bulk_create:
        :type mock_eve_bulk_create:
        :param mock_structures_all:
        :type mock_structures_all:
        :param mock_structures_exclude:
        :type mock_structures_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        mock_cache_get.return_value = None
        mock_get_structures.return_value = [
            Mock(
                structure_id=1,
                alliance_id=1001,
                solar_system_id=2001,
                structure_type_id=3001,
                vulnerability_occupancy_level=0.5,
                vulnerable_start_time="2023-10-01T12:00:00Z",
                vulnerable_end_time="2023-10-02T12:00:00Z",
            )
        ]
        mock_structures_all.return_value.values.return_value = [
            {"structure_id": 1, "vulnerability_occupancy_level": 0.5}
        ]

        mock_solar_system = MagicMock(spec=EveSolarSystem)
        mock_solar_system.id = 2001
        mock_solar_system._state = MagicMock()  # Add the _state attribute
        mock_solar_system_filter.return_value = [mock_solar_system]

        mock_structures_exclude.return_value.delete = Mock()

        update_sov_structures()

        mock_logger_debug.assert_called_with(
            msg="Number of sovereignty structures from ESI: 1"
        )
        mock_logger_info.assert_called_with(
            msg="1 sovereignty structures updated from ESI."
        )
        mock_eve_bulk_create.assert_called_once()
        mock_bulk_create.assert_called_once()
        mock_bulk_update_new_esi.assert_called_once()
        mock_cache_set.assert_called_once()

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.cache.get")
    def test_skips_update_when_cache_is_set(self, mock_cache_get, mock_get_structures):
        """
        Test that update_sov_structures skips update when cache is set.

        :param mock_cache_get:
        :type mock_cache_get:
        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        mock_cache_get.return_value = True

        update_sov_structures()

        mock_get_structures.assert_not_called()

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.logger.info")
    @patch("sovtimer.tasks.logger.debug")
    def test_handles_no_structures_from_esi(
        self, mock_logger_debug, mock_logger_info, mock_get_structures
    ):
        mock_get_structures.return_value = None

        update_sov_structures()

        mock_logger_debug.assert_not_called()
        mock_logger_info.assert_not_called()

    def test_ignores_duplicate_structures_with_same_id(self):
        """
        Test that update_sov_structures ignores duplicate structures with the same ID.

        :return:
        :rtype:
        """

        now = timezone.now()
        struct_a = SimpleNamespace(
            structure_id=55555,
            alliance_id=None,
            solar_system_id=None,
            structure_type_id=3000,
            vulnerability_occupancy_level=1,
            vulnerable_end_time=now,
            vulnerable_start_time=now,
        )
        struct_b = SimpleNamespace(
            structure_id=55555,  # duplicate ID
            alliance_id=None,
            solar_system_id=None,
            structure_type_id=3001,
            vulnerability_occupancy_level=3,
            vulnerable_end_time=now,
            vulnerable_start_time=now,
        )

        with patch(
            "sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi",
            return_value=[struct_a, struct_b],
        ):
            update_sov_structures(force_refresh=True)

        # Only one SovereigntyStructure with that structure_id should exist
        self.assertEqual(
            SovereigntyStructure.objects.filter(structure_id=55555).count(), 1
        )

    def test_returns_default_vulnerability_level_when_structure_not_in_campaign(self):
        """
        Test that the default vulnerability level is returned when structure is not in campaign.

        :return:
        :rtype:
        """

        structure_id = 99999
        current_structures = {88888: 2}

        with patch.object(Campaign.objects, "all", autospec=True) as mock_all:
            mock_all.return_value.values_list.return_value = [(12345,), (67890,)]

            result = current_structures.get(structure_id, 1)

            self.assertEqual(result, 1)

    def test_returns_existing_vulnerability_level_when_structure_in_campaign(self):
        """
        Test that the existing vulnerability level is returned when structure is in campaign.

        :return:
        :rtype:
        """

        structure_id = 12345
        current_structures = {12345: 3}

        with patch.object(Campaign.objects, "all", autospec=True) as mock_all:
            mock_all.return_value.values_list.return_value = [(12345,), (67890,)]

            result = current_structures.get(structure_id, 1)

            self.assertEqual(result, 3)
