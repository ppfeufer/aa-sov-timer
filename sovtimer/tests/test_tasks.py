"""
Tests for the sovtimer tasks.
"""

# Standard Library
from unittest.mock import MagicMock, patch

# Alliance Auth (External Libs)
from eveuniverse.models import EveEntity, EveSolarSystem

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

    def test_skips_update_when_campaigns_returned_as_none(self):
        """
        Test that update_sov_campaigns skips update when ESI returns None.

        :return:
        :rtype:
        """

        with patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi") as mock_get:
            mock_get.return_value = None

            update_sov_campaigns(force_refresh=True)

            mock_get.assert_called_once_with(True)
            self.assertEqual(Campaign.objects.count(), 0)

    def test_updates_campaigns_from_esi_creates_and_updates_campaigns(self):
        """
        Test that update_sov_campaigns correctly creates and updates campaigns from ESI.

        :return:
        :rtype:
        """

        SovereigntyStructure.objects.create(structure_id=200, structure_type_id=1)

        campaign = MagicMock(
            campaign_id=1,
            defender_id=100,
            attackers_score=0.5,
            defender_score=0.5,
            event_type="test_event",
            start_time="2023-01-01T00:00:00Z",
            structure_id=200,
        )

        with (
            patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi") as mock_get,
            patch("sovtimer.tasks.EveEntity.objects.bulk_create") as mock_bulk_create,
            patch(
                "sovtimer.tasks.EveEntity.objects.bulk_update_new_esi"
            ) as mock_bulk_update,
        ):
            mock_get.return_value = [campaign]

            update_sov_campaigns(force_refresh=False)

            mock_get.assert_called_once_with(False)
            mock_bulk_create.assert_called_once_with(
                [EveEntity(id=100)], ignore_conflicts=True
            )
            mock_bulk_update.assert_called_once()
            self.assertEqual(Campaign.objects.count(), 1)
            created_campaign = Campaign.objects.first()
            self.assertEqual(created_campaign.campaign_id, 1)
            self.assertEqual(created_campaign.defender_score, 0.5)

    def test_handles_existing_campaigns_with_updated_scores(self):
        """
        Test that update_sov_campaigns correctly updates existing campaigns with new scores.

        :return:
        :rtype:
        """

        SovereigntyStructure.objects.create(structure_id=200, structure_type_id=1)

        Campaign.objects.create(
            campaign_id=1,
            defender_score=0.4,
            progress_previous=0.4,
            attackers_score=0.6,
            event_type="test_event",
            start_time="2023-01-01T00:00:00Z",
            structure_id=200,
        )
        campaign = MagicMock(
            campaign_id=1,
            defender_id=100,
            attackers_score=0.6,
            defender_score=0.5,
            event_type="test_event",
            start_time="2023-01-01T00:00:00Z",
            structure_id=200,
        )

        with (
            patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi") as mock_get,
            patch("sovtimer.tasks.EveEntity.objects.bulk_create") as mock_bulk_create,
            patch(
                "sovtimer.tasks.EveEntity.objects.bulk_update_new_esi"
            ) as mock_bulk_update,
        ):
            mock_get.return_value = [campaign]

            update_sov_campaigns(force_refresh=False)

            mock_get.assert_called_once_with(False)
            mock_bulk_create.assert_called_once_with(
                [EveEntity(id=100)], ignore_conflicts=True
            )
            mock_bulk_update.assert_called_once()
            self.assertEqual(Campaign.objects.count(), 1)
            updated_campaign = Campaign.objects.first()
            self.assertEqual(updated_campaign.campaign_id, 1)
            self.assertEqual(updated_campaign.defender_score, 0.5)
            self.assertEqual(updated_campaign.progress_previous, 0.4)


class TestUpdateSovStructuresTask(BaseTestCase):
    """
    Test the update_sov_structures task.
    """

    def test_skips_update_when_structures_returned_as_none(self):
        """
        Test that update_sov_structures skips update when ESI returns None.

        :return:
        :rtype:
        """

        with (
            patch(
                "sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi"
            ) as mock_get,
            patch("sovtimer.tasks.EveEntity.objects.bulk_create") as mock_eve_bulk,
        ):
            mock_get.return_value = None

            update_sov_structures(force_refresh=True)

            mock_get.assert_called_once_with(True)
            mock_eve_bulk.assert_not_called()

    def test_updates_structures_from_esi_creates_and_updates_structures(self):
        """
        Test that update_sov_structures correctly creates and updates structures from ESI.

        :return:
        :rtype:
        """

        structure = MagicMock(
            structure_id=1,
            alliance_id=100,
            solar_system_id=200,
            structure_type_id=300,
            vulnerability_occupancy_level=0.5,
            vulnerable_start_time="2023-01-01T00:00:00Z",
            vulnerable_end_time="2023-01-02T00:00:00Z",
        )

        with (
            patch(
                "sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi"
            ) as mock_get,
            patch("sovtimer.tasks.SovereigntyStructure.objects.values") as mock_values,
            patch("sovtimer.tasks.Campaign.objects.values_list") as mock_campaign_vals,
            patch(
                "sovtimer.tasks.EveEntity.objects.bulk_create"
            ) as mock_eve_bulk_create,
            patch("sovtimer.tasks.EveEntity.objects.filter") as mock_eve_filter,
            patch("sovtimer.tasks.EveSolarSystem.objects.filter") as mock_ss_filter,
            patch(
                "sovtimer.tasks.SovereigntyStructure.objects.bulk_create"
            ) as mock_sov_bulk,
            patch(
                "sovtimer.tasks.SovereigntyStructure.objects.exclude"
            ) as mock_exclude,
            patch(
                "sovtimer.tasks.EveEntity.objects.bulk_update_new_esi"
            ) as mock_eve_update,
            patch("sovtimer.tasks.transaction.atomic") as mock_atomic,
        ):
            mock_get.return_value = [structure]
            mock_values.return_value = [
                {"structure_id": 1, "vulnerability_occupancy_level": 0.2}
            ]
            mock_campaign_vals.return_value = [1]
            mock_eve_filter.return_value = [tasks_module.EveEntity(id=100)]
            mock_ss_filter.return_value = [EveSolarSystem(id=200)]
            mock_atomic.return_value.__enter__.return_value = None

            update_sov_structures(force_refresh=False)

            mock_eve_bulk_create.assert_called_once()
            assert mock_sov_bulk.called
            args, kwargs = mock_sov_bulk.call_args
            created_list = args[0]
            assert len(created_list) == 1
            assert getattr(created_list[0], "vulnerability_occupancy_level") == 0.2
            mock_exclude.assert_called_once_with(pk__in={1})
            mock_exclude.return_value.delete.assert_called_once()
            mock_eve_update.assert_called_once()

    def test_ignores_structures_with_missing_or_duplicate_ids(self):
        s_missing = MagicMock(structure_id=None, alliance_id=None, solar_system_id=None)
        s_dup_a = MagicMock(
            structure_id=2,
            alliance_id=101,
            solar_system_id=201,
            structure_type_id=301,
            vulnerability_occupancy_level=0.7,
            vulnerable_start_time=None,
            vulnerable_end_time=None,
        )
        s_dup_b = MagicMock(
            structure_id=2,
            alliance_id=101,
            solar_system_id=201,
            structure_type_id=301,
            vulnerability_occupancy_level=0.9,
            vulnerable_start_time=None,
            vulnerable_end_time=None,
        )

        with (
            patch(
                "sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi"
            ) as mock_get,
            patch("sovtimer.tasks.SovereigntyStructure.objects.values") as mock_values,
            patch("sovtimer.tasks.Campaign.objects.values_list") as mock_campaign_vals,
            patch("sovtimer.tasks.EveEntity.objects.bulk_create"),
            patch("sovtimer.tasks.EveEntity.objects.filter") as mock_eve_filter,
            patch("sovtimer.tasks.EveSolarSystem.objects.filter") as mock_ss_filter,
            patch(
                "sovtimer.tasks.SovereigntyStructure.objects.bulk_create"
            ) as mock_sov_bulk,
            patch(
                "sovtimer.tasks.SovereigntyStructure.objects.exclude"
            ) as mock_exclude,
            patch("sovtimer.tasks.EveEntity.objects.bulk_update_new_esi"),
            patch("sovtimer.tasks.transaction.atomic") as mock_atomic,
        ):
            mock_get.return_value = [s_missing, s_dup_a, s_dup_b]
            mock_values.return_value = []
            mock_campaign_vals.return_value = []
            mock_eve_filter.return_value = [tasks_module.EveEntity(id=101)]
            mock_ss_filter.return_value = [EveSolarSystem(id=201)]
            mock_atomic.return_value.__enter__.return_value = None

            update_sov_structures()

            assert mock_sov_bulk.called
            args, kwargs = mock_sov_bulk.call_args
            created_list = args[0]
            assert len(created_list) == 1
            assert getattr(created_list[0], "vulnerability_occupancy_level") == 0.7
            mock_exclude.assert_called_once_with(pk__in={2})
            mock_exclude.return_value.delete.assert_called_once()
