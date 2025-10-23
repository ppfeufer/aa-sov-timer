"""
Unit tests for the SovereigntyStructure model's interaction with ESI.
"""

# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
from aiopenapi3 import ContentTypeError

# Alliance Auth
from esi.exceptions import HTTPClientError, HTTPNotModified

# AA Sovereignty Timer
from sovtimer.models import SovereigntyStructure
from sovtimer.tests import BaseTestCase


class SovereigntyStructureESITestCase(BaseTestCase):
    """
    Test suite for the SovereigntyStructure model's interaction with ESI.
    """

    def test_gets_sov_structures_from_esi_with_valid_data(self):
        """
        Test fetching sovereignty structures from ESI with valid data.

        :return:
        :rtype:
        """

        mock_esi_client = MagicMock()
        mock_esi_client.Sovereignty.GetSovereigntyStructures.return_value.result.return_value = [
            {"structure_id": 1},
            {"structure_id": 2},
        ]

        with patch("sovtimer.models.esi") as mock_esi_module:
            mock_esi_module.client = mock_esi_client
            result = SovereigntyStructure.get_sov_structures_from_esi()

            self.assertEqual(result, [{"structure_id": 1}, {"structure_id": 2}])

    def test_returns_none_when_no_changes_in_sov_structures(self):
        """
        Test handling of no changes in sovereignty structures from ESI.

        :return:
        :rtype:
        """

        mock_esi_client = MagicMock()
        mock_esi_client.Sovereignty.GetSovereigntyStructures.return_value.result.side_effect = HTTPNotModified(
            status_code=304, headers={}
        )

        with patch("sovtimer.models.esi") as mock_esi_module:
            mock_esi_module.client = mock_esi_client
            result = SovereigntyStructure.get_sov_structures_from_esi()

            self.assertIsNone(result)

    def test_handles_content_type_error_in_sov_structures(self):
        """
        Test handling of ContentTypeError when fetching sovereignty structures from ESI.

        :return:
        :rtype:
        """

        mock_esi_client = MagicMock()
        mock_esi_client.Sovereignty.GetSovereigntyStructures.return_value.result.side_effect = ContentTypeError(
            operation="dummy_op",
            content_type="application/json",
            message="dummy message",
            response=None,
        )

        with patch("sovtimer.models.esi") as mock_esi_module:
            mock_esi_module.client = mock_esi_client
            result = SovereigntyStructure.get_sov_structures_from_esi()

            self.assertIsNone(result)

    def test_handles_httpclienterror_error_in_sov_structures(self):
        """
        Test handling of HTTPClientError when fetching sovereignty structures from ESI.

        :return:
        :rtype:
        """

        mock_esi_client = MagicMock()
        mock_esi_client.Sovereignty.GetSovereigntyStructures.return_value.result.side_effect = HTTPClientError(
            "HTTPClientError", {}, {}
        )
        with patch("sovtimer.models.esi") as mock_esi_module:
            mock_esi_module.client = mock_esi_client
            result = SovereigntyStructure.get_sov_structures_from_esi()
            self.assertIsNone(result)
