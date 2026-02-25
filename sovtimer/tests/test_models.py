"""
Unit tests for the models in sovtimer
"""

# Standard Library
from unittest.mock import MagicMock, patch

# AA Sovereignty Timer
from sovtimer.models import Alliance, Campaign, SovereigntyStructure, logger
from sovtimer.tests import BaseTestCase


class TestAlliance(BaseTestCase):
    """
    Test cases for the Alliance model
    """

    @patch("sovtimer.models.ESIHandler.get_alliances_alliance_id")
    @patch("sovtimer.models.Alliance.objects.bulk_create")
    @patch("sovtimer.models.Alliance.objects.filter")
    def test_returns_all_alliances_when_all_ids_exist(
        self, mock_filter, mock_bulk_create, mock_get_alliance
    ):
        """
        Test that all alliances are returned when all IDs exist in the database

        :param mock_filter:
        :type mock_filter:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_alliance:
        :type mock_get_alliance:
        :return:
        :rtype:
        """

        mock_existing_alliances = [
            Alliance(alliance_id=1, name="Alliance 1"),
            Alliance(alliance_id=2, name="Alliance 2"),
        ]
        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = iter(mock_existing_alliances)
        mock_qs.values_list.return_value = [1, 2]
        mock_filter.return_value = mock_qs

        result = Alliance.bulk_get_or_create_from_esi(
            alliance_ids={1, 2}, force_refresh=False
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[1].name, "Alliance 1")
        self.assertEqual(result[2].name, "Alliance 2")
        mock_filter.assert_called_once_with(alliance_id__in={1, 2})
        mock_bulk_create.assert_not_called()
        mock_get_alliance.assert_not_called()

    @patch("sovtimer.models.ESIHandler.get_alliances_alliance_id")
    @patch("sovtimer.models.Alliance.objects.bulk_create")
    @patch("sovtimer.models.Alliance.objects.filter")
    def test_creates_new_alliances_when_some_ids_do_not_exist(
        self, mock_filter, mock_bulk_create, mock_get_alliance
    ):
        """
        Test that new alliances are created when some IDs do not exist in the database

        :param mock_filter:
        :type mock_filter:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_alliance:
        :type mock_get_alliance:
        :return:
        :rtype:
        """

        mock_existing_alliances = [
            Alliance(alliance_id=1, name="Alliance 1"),
        ]
        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = iter(mock_existing_alliances)
        mock_qs.values_list.return_value = [1]
        mock_filter.return_value = mock_qs

        a2 = MagicMock()
        a2.name = "Alliance 2"
        a3 = MagicMock()
        a3.name = "Alliance 3"
        mock_get_alliance.side_effect = [a2, a3]

        mock_bulk_create.return_value = [
            Alliance(alliance_id=2, name="Alliance 2"),
            Alliance(alliance_id=3, name="Alliance 3"),
        ]

        result = Alliance.bulk_get_or_create_from_esi(
            alliance_ids={1, 2, 3}, force_refresh=False
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(result[1].name, "Alliance 1")
        self.assertEqual(result[2].name, "Alliance 2")
        self.assertEqual(result[3].name, "Alliance 3")
        mock_filter.assert_called_once_with(alliance_id__in={1, 2, 3})
        mock_get_alliance.assert_any_call(alliance_id=2, force_refresh=False)
        mock_get_alliance.assert_any_call(alliance_id=3, force_refresh=False)
        mock_bulk_create.assert_called_once()

    @patch("sovtimer.models.ESIHandler.get_alliances_alliance_id")
    @patch("sovtimer.models.Alliance.objects.bulk_create")
    @patch("sovtimer.models.Alliance.objects.filter")
    def test_skips_creation_when_esi_returns_no_data(
        self, mock_filter, mock_bulk_create, mock_get_alliance
    ):
        """
        Test that creation is skipped when ESI returns no data for an alliance ID

        :param mock_filter:
        :type mock_filter:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_alliance:
        :type mock_get_alliance:
        :return:
        :rtype:
        """

        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = iter([])
        mock_qs.values_list.return_value = []
        mock_filter.return_value = mock_qs
        mock_get_alliance.return_value = None

        result = Alliance.bulk_get_or_create_from_esi(
            alliance_ids={1}, force_refresh=False
        )

        self.assertEqual(len(result), 0)
        mock_filter.assert_called_once_with(alliance_id__in={1})
        mock_get_alliance.assert_called_once_with(alliance_id=1, force_refresh=False)
        mock_bulk_create.assert_not_called()


class TestSovereigntyStructure(BaseTestCase):
    """
    Test cases for the SovereigntyStructure model
    """

    @patch("sovtimer.models.ESIHandler.get_sovereignty_structures")
    def test_returns_sov_structures_when_esi_returns_data(
        self, mock_get_sov_structures
    ):
        """
        Test that sovereignty structures are returned when ESI returns data

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :return:
        :rtype:
        """

        mock_get_sov_structures.return_value = [
            {
                "structure_id": 1001,
                "alliance_id": 2001,
                "solar_system_id": 3001,
                "structure_type_id": 4001,
                "vulnerability_occupancy_level": 0.5,
                "vulnerable_start_time": "2023-01-01T12:00:00Z",
                "vulnerable_end_time": "2023-01-01T18:00:00Z",
            }
        ]

        result = SovereigntyStructure.get_sov_structures_from_esi(force_refresh=False)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["structure_id"], 1001)
        mock_get_sov_structures.assert_called_once_with(force_refresh=False)

    @patch("sovtimer.models.ESIHandler.get_sovereignty_structures")
    def test_returns_empty_list_when_esi_returns_no_data(self, mock_get_sov_structures):
        """
        Test that an empty list is returned when ESI returns no data for sovereignty structures

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :return:
        :rtype:
        """

        mock_get_sov_structures.return_value = []

        result = SovereigntyStructure.get_sov_structures_from_esi(force_refresh=False)

        self.assertEqual(len(result), 0)
        mock_get_sov_structures.assert_called_once_with(force_refresh=False)

    @patch("sovtimer.models.ESIHandler.get_sovereignty_structures")
    def test_logs_info_when_esi_returns_no_data(self, mock_get_sov_structures):
        """
        Test that an info log is generated when ESI returns no data for sovereignty structures

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :return:
        :rtype:
        """

        mock_get_sov_structures.return_value = []

        with self.assertLogs(logger.logger, level="INFO") as log:
            SovereigntyStructure.get_sov_structures_from_esi(force_refresh=False)

        self.assertIn(
            "No sovereignty structure changes found, nothing to update.", log.output[0]
        )

    @patch("sovtimer.models.ESIHandler.get_sovereignty_structures")
    def test_logs_debug_when_esi_returns_data(self, mock_get_sov_structures):
        """
        Test that a debug log is generated when ESI returns data for sovereignty structures

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :return:
        :rtype:
        """

        mock_get_sov_structures.return_value = [
            {
                "structure_id": 1001,
                "alliance_id": 2001,
                "solar_system_id": 3001,
                "structure_type_id": 4001,
                "vulnerability_occupancy_level": 0.5,
                "vulnerable_start_time": "2023-01-01T12:00:00Z",
                "vulnerable_end_time": "2023-01-01T18:00:00Z",
            }
        ]

        with self.assertLogs(logger.logger, level="DEBUG") as log:
            SovereigntyStructure.get_sov_structures_from_esi(force_refresh=False)

        self.assertIn("Fetched 1 sovereignty structures from ESI", log.output[0])


class TestCampaign(BaseTestCase):
    """
    Test cases for the Campaign model
    """

    @patch("sovtimer.models.ESIHandler.get_sovereignty_campaigns")
    def test_returns_campaigns_when_esi_returns_data(self, mock_get_campaigns):
        """
        Test that campaigns are returned when ESI returns data

        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = [
            {
                "campaign_id": 5001,
                "attackers_score": 0.3,
                "defender_score": 0.7,
                "event_type": "sovhub",
                "start_time": "2023-01-01T12:00:00Z",
                "structure_id": 1001,
            }
        ]

        result = Campaign.get_sov_campaigns_from_esi(force_refresh=False)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["campaign_id"], 5001)
        mock_get_campaigns.assert_called_once_with(force_refresh=False)

    @patch("sovtimer.models.ESIHandler.get_sovereignty_campaigns")
    def test_returns_empty_list_when_esi_returns_no_data(self, mock_get_campaigns):
        """
        Test that an empty list is returned when ESI returns no data for campaigns

        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = []

        result = Campaign.get_sov_campaigns_from_esi(force_refresh=False)

        self.assertEqual(len(result), 0)
        mock_get_campaigns.assert_called_once_with(force_refresh=False)

    @patch("sovtimer.models.ESIHandler.get_sovereignty_campaigns")
    def test_logs_info_when_esi_returns_no_data(self, mock_get_campaigns):
        """
        Test that an info log is generated when ESI returns no data for campaigns

        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = []

        with self.assertLogs(logger.logger, level="INFO") as log:
            Campaign.get_sov_campaigns_from_esi(force_refresh=False)

        self.assertIn("No campaign changes found, nothing to update.", log.output[0])

    @patch("sovtimer.models.ESIHandler.get_sovereignty_campaigns")
    def test_logs_debug_when_esi_returns_data(self, mock_get_campaigns):
        """
        Test that a debug log is generated when ESI returns data for campaigns

        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = [
            {
                "campaign_id": 5001,
                "attackers_score": 0.3,
                "defender_score": 0.7,
                "event_type": "sovhub",
                "start_time": "2023-01-01T12:00:00Z",
                "structure_id": 1001,
            }
        ]

        with self.assertLogs(logger.logger, level="DEBUG") as log:
            Campaign.get_sov_campaigns_from_esi(force_refresh=False)

        self.assertIn("Fetched 1 campaigns from ESI", log.output[0])
