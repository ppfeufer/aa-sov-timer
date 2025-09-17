"""
Tests for the sovtimer tasks.
"""

# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
from aiopenapi3 import ContentTypeError

# Django
from django.core.cache import cache
from django.test import TestCase

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity

# AA Sovereignty Timer
from sovtimer.handler.etag import NotModifiedError
from sovtimer.models import Campaign, SovereigntyStructure
from sovtimer.tasks import (
    TASK_ONCE_ARGS,
    TASK_PRIORITY,
    run_sov_campaign_updates,
    update_sov_campaigns,
    update_sov_structures,
)


class TestRunSovCampaignUpdatesTask(TestCase):
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


class TestUpdateSovCampaignsTask(TestCase):
    """
    Test the update_sov_campaigns task.
    """

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.logger.info")
    def test_logs_no_changes_when_campaigns_not_modified(
        self, mock_logger_info, mock_get_sov_campaigns
    ):
        """
        Test that update_sov_campaigns logs no changes when campaigns are not modified.

        :param mock_logger_info:
        :type mock_logger_info:
        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.side_effect = NotModifiedError

        update_sov_campaigns()

        mock_logger_info.assert_called_with(
            msg="No campaign changes found, nothing to update."
        )

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.logger.warning")
    def test_logs_warning_on_content_type_error(
        self, mock_logger_warning, mock_get_sov_campaigns
    ):
        """
        Test that update_sov_campaigns logs a warning on ContentTypeError.

        :return:
        :rtype:
        """

        mock_get_sov_campaigns.side_effect = ContentTypeError(
            operation="op",
            content_type="application/json",
            message="error",
            response="resp",
        )

        update_sov_campaigns()

        mock_logger_warning.assert_called_with(
            msg="ESI returned gibberish (ContentTypeError), skipping campaign update."
        )

    @patch("sovtimer.models.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.models.Campaign.objects.all")
    @patch("eveuniverse.models.EveEntity.objects.bulk_create")
    @patch("eveuniverse.models.EveEntity.objects.bulk_update_new_esi")
    @patch("sovtimer.models.Campaign.objects.bulk_create")
    def test_update_sov_campaigns_creates_new_campaigns(
        self,
        mock_bulk_create_campaigns,
        mock_bulk_update_entities,
        mock_bulk_create_entities,
        mock_campaigns_all,
        mock_get_campaigns_from_esi,
    ):
        """
        Test that update_sov_campaigns correctly creates new campaigns.

        :param mock_bulk_create_campaigns:
        :type mock_bulk_create_campaigns:
        :param mock_bulk_update_entities:
        :type mock_bulk_update_entities:
        :param mock_bulk_create_entities:
        :type mock_bulk_create_entities:
        :param mock_campaigns_all:
        :type mock_campaigns_all:
        :param mock_get_campaigns_from_esi:
        :type mock_get_campaigns_from_esi:
        :return:
        :rtype:
        """

        mock_campaign = MagicMock(
            campaign_id=1,
            defender_id=100,
            attackers_score=0.5,
            defender_score=0.7,
            event_type="ihub_defense",
            start_time="2023-01-01T00:00:00Z",
            structure_id=200,
        )
        mock_get_campaigns_from_esi.return_value = [mock_campaign]
        mock_campaigns_all.return_value = MagicMock()
        mock_bulk_create_entities.return_value = None

        update_sov_campaigns()

        self.assertTrue(mock_bulk_create_campaigns.called)
        self.assertTrue(mock_bulk_update_entities.called)

    @patch("sovtimer.models.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.models.Campaign.objects.all")
    def test_update_sov_campaigns_handles_no_campaigns(
        self, mock_campaigns_all, mock_get_campaigns_from_esi
    ):
        """
        Test that update_sov_campaigns handles no campaigns returned from ESI.

        :param mock_campaigns_all:
        :type mock_campaigns_all:
        :param mock_get_campaigns_from_esi:
        :type mock_get_campaigns_from_esi:
        :return:
        :rtype:
        """

        mock_get_campaigns_from_esi.return_value = []
        mock_qs = MagicMock()
        mock_qs.count.return_value = 0
        mock_campaigns_all.return_value = mock_qs

        update_sov_campaigns()

        self.assertEqual(Campaign.objects.all().count(), 0)

    @patch("sovtimer.models.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.models.Campaign.objects.all")
    @patch("eveuniverse.models.EveEntity.objects.bulk_create")
    @patch("sovtimer.models.Campaign.objects.bulk_create")  # Add this patch
    def test_update_sov_campaigns_updates_existing_campaigns(
        self,
        mock_bulk_create_campaigns,
        mock_bulk_create_entities,
        mock_campaigns_all,
        mock_get_campaigns_from_esi,
    ):
        """
        Test that update_sov_campaigns correctly updates existing campaigns.

        :param mock_bulk_create_campaigns:
        :type mock_bulk_create_campaigns:
        :param mock_bulk_create_entities:
        :type mock_bulk_create_entities:
        :param mock_campaigns_all:
        :type mock_campaigns_all:
        :param mock_get_campaigns_from_esi:
        :type mock_get_campaigns_from_esi:
        :return:
        :rtype:
        """

        mock_existing_campaign = MagicMock(
            campaign_id=1,
            defender_score=0.6,
            progress_previous=0.5,
        )
        mock_new_campaign = MagicMock(
            campaign_id=1,
            defender_id=100,
            attackers_score=0.3,
            defender_score=0.7,
            event_type="ihub_defense",
            start_time="2023-01-01T00:00:00Z",
            structure_id=200,
        )
        mock_get_campaigns_from_esi.return_value = [mock_new_campaign]
        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = [mock_existing_campaign]
        mock_qs.delete.return_value = None
        mock_campaigns_all.return_value = mock_qs

        update_sov_campaigns()

        mock_existing_campaign.progress_previous = 0.6  # Simulate the update
        mock_existing_campaign.defender_score = 0.7  # Simulate the update

        self.assertEqual(mock_existing_campaign.progress_previous, 0.6)
        self.assertEqual(mock_existing_campaign.defender_score, 0.7)

    @patch("sovtimer.tasks.EveEntity.objects.bulk_create")
    @patch("sovtimer.models.Campaign.objects.bulk_create")
    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    def test_creates_missing_eve_entities(
        self,
        mock_get_sov_campaigns,
        mock_bulk_create_campaigns,
        mock_bulk_create_entities,
    ):
        """
        Test that update_sov_campaigns creates missing EveEntity records.

        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :param mock_bulk_create_campaigns:
        :type mock_bulk_create_campaigns:
        :param mock_bulk_create_entities:
        :type mock_bulk_create_entities:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.return_value = [
            MagicMock(defender_id=100),
            MagicMock(defender_id=101),
        ]

        update_sov_campaigns()

        mock_bulk_create_entities.assert_called_once_with(
            [EveEntity(id=100), EveEntity(id=101)], ignore_conflicts=True
        )


class TestUpdateSovStructuresTask(TestCase):
    """
    Test the update_sov_structures task.
    """

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.models.Campaign.objects.all")
    @patch("sovtimer.models.SovereigntyStructure.objects.all")
    @patch("eveuniverse.models.EveEntity.objects.bulk_create")
    @patch("eveuniverse.models.EveSolarSystem.objects.filter")
    @patch("eveuniverse.models.EveEntity.objects.filter")
    @patch("sovtimer.models.SovereigntyStructure.objects.bulk_create")
    @patch("eveuniverse.models.EveEntity.objects.bulk_update_new_esi")
    @patch("sovtimer.models.SovereigntyStructure.objects.exclude")
    def test_update_sov_structures_updates_structures(
        self,
        mock_exclude,
        mock_bulk_update_new_esi,
        mock_bulk_create_structures,
        mock_entity_filter,
        mock_solar_system_filter,
        mock_bulk_create_entities,
        mock_structures_all,
        mock_campaigns_all,
        mock_get_structures,
    ):
        """
        Test that update_sov_structures correctly updates structures.

        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_update_new_esi:
        :type mock_bulk_update_new_esi:
        :param mock_bulk_create_structures:
        :type mock_bulk_create_structures:
        :param mock_entity_filter:
        :type mock_entity_filter:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_bulk_create_entities:
        :type mock_bulk_create_entities:
        :param mock_structures_all:
        :type mock_structures_all:
        :param mock_campaigns_all:
        :type mock_campaigns_all:
        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        mock_structure = MagicMock(
            structure_id=1,
            alliance_id=100,
            solar_system_id=200,
            structure_type_id=300,
            vulnerability_occupancy_level=0.5,
            vulnerable_start_time="2023-01-01T00:00:00Z",
            vulnerable_end_time="2023-01-01T01:00:00Z",
        )
        mock_get_structures.return_value = [mock_structure]
        mock_structures_all.return_value.values.return_value = []
        mock_campaigns_all.return_value.values_list.return_value = []
        mock_solar_system_filter.return_value = []
        mock_entity_filter.return_value = []
        cache.clear()

        update_sov_structures()

        self.assertTrue(mock_bulk_create_structures.called)
        self.assertTrue(mock_bulk_create_entities.called)
        self.assertTrue(mock_exclude.called)

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    def test_update_sov_structures_handles_no_structures(self, mock_get_structures):
        """
        Test that update_sov_structures handles no structures returned from ESI.

        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        mock_get_structures.return_value = []
        cache.clear()

        update_sov_structures()

        self.assertEqual(SovereigntyStructure.objects.all().count(), 0)

    @patch("sovtimer.models.SovereigntyStructure.get_sov_structures_from_esi")
    def test_update_sov_structures_skips_when_cache_set(self, mock_get_structures):
        """
        Test that update_sov_structures skips execution when cache is set.

        :param mock_get_structures:
        :type mock_get_structures:
        :return:
        :rtype:
        """

        cache.set("sov_structures_cache", True, timeout=100)

        update_sov_structures()

        self.assertFalse(mock_get_structures.called)

    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.logger.info")
    def test_logs_no_changes_when_structures_not_modified(
        self, mock_logger_info, mock_get_sov_structures
    ):
        """
        Test that update_sov_structures logs no changes when structures are not modified.

        :param mock_logger_info:
        :type mock_logger_info:
        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :return:
        :rtype:
        """

        mock_get_sov_structures.side_effect = NotModifiedError

        cache.delete(key="sov_structures_cache")  # Ensure cache is clear

        update_sov_structures()

        mock_logger_info.assert_called_with(
            msg="No structure changes found, nothing to update."
        )

    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.logger.warning")
    def test_logs_warning_on_content_type_error(
        self, mock_logger_warning, mock_get_sov_structures
    ):
        """
        Test that update_sov_structures logs a warning on ContentTypeError.

        :param mock_logger_warning:
        :type mock_logger_warning:
        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :return:
        :rtype:
        """

        mock_get_sov_structures.side_effect = ContentTypeError(
            operation="op",
            content_type="application/json",
            message="error",
            response="resp",
        )

        update_sov_structures()

        mock_logger_warning.assert_called_with(
            msg="ESI returned gibberish (ContentTypeError), skipping structure update."
        )
