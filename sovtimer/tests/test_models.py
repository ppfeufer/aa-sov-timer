"""
Tests for the models in the sovtimer app.
"""

# Standard Library
from unittest.mock import MagicMock, patch

# Django
from django.test import TestCase

# AA Sovereignty Timer
from sovtimer.handler.etag import NotModifiedError
from sovtimer.models import Campaign, SovereigntyStructure


class TestSovereigntyStructure(TestCase):
    """
    Test SovereigntyStructure model methods
    """

    @patch("sovtimer.models.etag")
    def test_structures_are_returned_when_esi_call_succeeds(self, mock_etag):
        """
        Test that structures are returned when the ESI call is successful.

        :param mock_esi:
        :type mock_esi:
        :return:
        :rtype:
        """

        mock_structures = [
            {"structure_id": 1, "alliance_id": 123},
            {"structure_id": 2, "alliance_id": 456},
        ]
        mock_etag.etag_result.return_value = mock_structures

        result = SovereigntyStructure.get_sov_structures_from_esi()

        self.assertEqual(result, mock_structures)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        mock_etag.etag_result.assert_called_once()

    @patch("sovtimer.models.etag")
    def test_empty_list_is_returned_when_esi_returns_empty_results(self, mock_etag):
        """
        Test that an empty list is returned when ESI returns no structures.

        :param mock_etag:
        :type mock_etag:
        :return:
        :rtype:
        """

        mock_etag.etag_result.return_value = []

        result = SovereigntyStructure.get_sov_structures_from_esi()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        mock_etag.etag_result.assert_called_once()


class TestCampaign(TestCase):
    """
    Test Campaign model methods
    """

    @patch("sovtimer.models.etag")
    def test_successfully_fetches_campaigns_from_esi(self, mock_etag):
        """
        Test that campaigns are successfully fetched from ESI.

        :param mock_esi:
        :type mock_esi:
        :return:
        :rtype:
        """

        mock_campaigns = [
            {"campaign_id": 1, "event_type": "ihub_defense"},
            {"campaign_id": 2, "event_type": "ihub_defense"},
        ]
        mock_etag.etag_result.return_value = mock_campaigns

        result = Campaign.get_sov_campaigns_from_esi()

        self.assertEqual(result, mock_campaigns)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        mock_etag.etag_result.assert_called_once()

    @patch("sovtimer.models.etag")
    def test_returns_empty_list_when_no_campaigns_exist(self, mock_etag):
        """
        Test that an empty list is returned when no campaigns exist.

        :param mock_esi:
        :type mock_esi:
        :return:
        :rtype:
        """

        mock_etag.etag_result.return_value = []

        result = Campaign.get_sov_campaigns_from_esi()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    @patch("sovtimer.models.esi.client.Sovereignty.GetSovereigntyCampaigns")
    @patch("sovtimer.models.etag.etag_result")
    def test_raises_not_modified_error_when_esi_returns_not_modified(
        self, mock_etag_result, mock_get_campaigns
    ):
        """
        Test that NotModifiedError is raised when ESI indicates no changes.

        :param mock_etag_result:
        :type mock_etag_result:
        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = MagicMock()
        mock_etag_result.side_effect = NotModifiedError

        with self.assertRaises(NotModifiedError):
            Campaign.get_sov_campaigns_from_esi()
