"""
Unit tests for the SovereigntyStructure model's interaction with ESI.
"""

# Standard Library
from unittest.mock import patch

# AA Sovereignty Timer
from sovtimer.models import SovereigntyStructure
from sovtimer.tests import BaseTestCase


class SovereigntyStructureESITestCase(BaseTestCase):
    """
    Test suite for the SovereigntyStructure model's interaction with ESI.
    """

    def test_returns_sov_structures_when_esi_returns_data(self):
        """
        Test that sovereignty structures are returned when ESI provides data.

        :return:
        :rtype:
        """

        with patch(
            "sovtimer.models.ESIHandler.get_sovereignty_structures"
        ) as mock_esi_handler:
            mock_esi_handler.return_value = [{"structure_id": 1}, {"structure_id": 2}]

            result = SovereigntyStructure.get_sov_structures_from_esi()

            self.assertEqual(len(result), 2)
            mock_esi_handler.assert_called_once_with(force_refresh=False)

    def test_returns_empty_list_when_esi_returns_no_data(self):
        """
        Test that an empty list is returned when ESI provides no data.

        :return:
        :rtype:
        """

        with patch(
            "sovtimer.models.ESIHandler.get_sovereignty_structures"
        ) as mock_esi_handler:
            mock_esi_handler.return_value = []

            result = SovereigntyStructure.get_sov_structures_from_esi()

            self.assertEqual(result, [])
            mock_esi_handler.assert_called_once_with(force_refresh=False)

    def test_logs_info_message_when_no_data_is_returned(self):
        """
        Test that an info message is logged when ESI returns no data.

        :return:
        :rtype:
        """

        with (
            patch(
                "sovtimer.models.ESIHandler.get_sovereignty_structures"
            ) as mock_esi_handler,
            patch("sovtimer.models.logger.info") as mock_logger,
        ):
            mock_esi_handler.return_value = []

            SovereigntyStructure.get_sov_structures_from_esi()

            mock_logger.assert_called_once_with(
                msg="No sovereignty structure changes found, nothing to update."
            )

    def test_logs_debug_message_when_data_is_returned(self):
        """
        Test that a debug message is logged when ESI returns data.

        :return:
        :rtype:
        """

        with (
            patch(
                "sovtimer.models.ESIHandler.get_sovereignty_structures"
            ) as mock_esi_handler,
            patch("sovtimer.models.logger.debug") as mock_logger,
        ):
            mock_esi_handler.return_value = [{"structure_id": 1}, {"structure_id": 2}]

            SovereigntyStructure.get_sov_structures_from_esi()

            self.assertEqual(mock_logger.call_count, 2)
            mock_logger.assert_any_call(
                msg="Fetched 2 sovereignty structures from ESI."
            )
            mock_logger.assert_any_call(
                msg="Sovereignty structure data: [{'structure_id': 1}, {'structure_id': 2}]"
            )
