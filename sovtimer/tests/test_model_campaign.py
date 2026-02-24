"""
Unit tests for the Campaign model's interaction with ESI.
"""

# Standard Library
from unittest.mock import patch

# AA Sovereignty Timer
from sovtimer.models import Campaign
from sovtimer.tests import BaseTestCase


class CampaignESITestCase(BaseTestCase):
    """
    Test suite for the Campaign model's interaction with ESI.
    """

    def test_returns_sov_campaigns_when_esi_returns_data(self):
        """
        Test that the method returns sovereignty campaigns when ESI returns data.

        :return:
        :rtype:
        """

        with patch(
            "sovtimer.models.ESIHandler.get_sovereignty_campaigns"
        ) as mock_esi_handler:
            mock_esi_handler.return_value = [{"campaign_id": 1}, {"campaign_id": 2}]

            result = Campaign.get_sov_campaigns_from_esi()

            self.assertEqual(len(result), 2)
            mock_esi_handler.assert_called_once_with(force_refresh=False)

    def test_returns_empty_list_when_esi_returns_no_data(self):
        """
        Test that the method returns an empty list when ESI returns no data.

        :return:
        :rtype:
        """

        with patch(
            "sovtimer.models.ESIHandler.get_sovereignty_campaigns"
        ) as mock_esi_handler:
            mock_esi_handler.return_value = []

            result = Campaign.get_sov_campaigns_from_esi()

            self.assertEqual(result, [])
            mock_esi_handler.assert_called_once_with(force_refresh=False)

    def test_logs_info_message_when_no_data_is_returned(self):
        """
        Test that an info message is logged when no data is returned from ESI.

        :return:
        :rtype:
        """

        with (
            patch(
                "sovtimer.models.ESIHandler.get_sovereignty_campaigns"
            ) as mock_esi_handler,
            patch("sovtimer.models.logger.info") as mock_logger,
        ):
            mock_esi_handler.return_value = []

            Campaign.get_sov_campaigns_from_esi()

            mock_logger.assert_called_once_with(
                msg="No campaign changes found, nothing to update."
            )

    def test_logs_debug_message_when_data_is_returned(self):
        """
        Test that a debug message is logged when data is returned from ESI.

        :return:
        :rtype:
        """

        with (
            patch(
                "sovtimer.models.ESIHandler.get_sovereignty_campaigns"
            ) as mock_esi_handler,
            patch("sovtimer.models.logger.debug") as mock_logger,
        ):
            mock_esi_handler.return_value = [{"campaign_id": 1}, {"campaign_id": 2}]

            Campaign.get_sov_campaigns_from_esi()

            self.assertEqual(mock_logger.call_count, 2)
            mock_logger.assert_any_call(msg="Fetched 2 campaigns from ESI.")
            mock_logger.assert_any_call(
                msg="Campaign data: [{'campaign_id': 1}, {'campaign_id': 2}]"
            )
