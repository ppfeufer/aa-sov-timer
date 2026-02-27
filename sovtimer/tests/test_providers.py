"""
Test for the providers module.
"""

# Standard Library
import logging
from http import HTTPStatus
from unittest.mock import MagicMock, patch

# Third Party
from aiopenapi3 import ContentTypeError

# Alliance Auth
from esi.exceptions import HTTPClientError, HTTPNotModified

# AA Sovereignty Timer
from sovtimer.providers import AppLogger, ESIHandler
from sovtimer.tests import BaseTestCase


class TestESIHandlerResult(BaseTestCase):
    """
    Test the ESIHandler.result method.
    """

    def test_handles_successful_operation(self):
        """
        Test that a successful ESI operation returns the expected result.

        :return:
        :rtype:
        """

        mock_operation = MagicMock()
        mock_operation.result.return_value = "success"

        response = ESIHandler.result(mock_operation)

        self.assertEqual(response, "success")
        mock_operation.result.assert_called_once()

    def test_handles_http_not_modified_exception(self):
        """
        Test that an HTTPNotModified exception is handled correctly.

        :return:
        :rtype:
        """

        mock_operation = MagicMock()
        mock_operation.result.side_effect = HTTPNotModified(
            status_code=HTTPStatus.NOT_MODIFIED, headers={}
        )

        response = ESIHandler.result(mock_operation)

        self.assertIsNone(response)
        mock_operation.result.assert_called_once()

    def test_handles_content_type_error(self):
        """
        Test that a ContentTypeError exception is handled correctly.

        :return:
        :rtype:
        """

        mock_operation = MagicMock()
        mock_response = MagicMock()
        mock_operation.result.side_effect = ContentTypeError(
            operation=mock_operation,
            content_type="application/json",
            message="Invalid content type",
            response=mock_response,
        )

        response = ESIHandler.result(mock_operation)

        self.assertIsNone(response)
        mock_operation.result.assert_called_once()

    def test_returns_none_when_http_client_error_occurs(self):
        """
        Test that an HTTPClientError exception is raised correctly.

        :return:
        :rtype:
        """

        mock_operation = MagicMock()
        mock_operation.result.side_effect = HTTPClientError(
            HTTPStatus.BAD_REQUEST, headers={}, data={}
        )

        response = ESIHandler.result(mock_operation)

        self.assertIsNone(response)
        mock_operation.result.assert_called_once()

    def test_passes_extra_parameters_to_operation(self):
        """
        Test that extra parameters are passed correctly to the ESI operation.

        :return:
        :rtype:
        """

        mock_operation = MagicMock()
        mock_operation.result.return_value = "success"

        response = ESIHandler.result(
            mock_operation, use_etag=False, extra_param="value"
        )

        self.assertEqual(response, "success")
        mock_operation.result.assert_called_once_with(
            use_etag=False,
            return_response=False,
            force_refresh=False,
            use_cache=True,
            extra_param="value",
        )


class TestESIHandlerGetSovereigntyCampaigns(BaseTestCase):
    """
    Test the ESIHandler.get_sovereignty_campaigns method.
    """

    def test_returns_campaigns_when_esi_returns_data(self):
        """
        Test that the method returns sovereignty campaigns when ESI returns data.

        :return:
        :rtype:
        """

        with (
            patch("sovtimer.providers.esi", new=MagicMock()),
            patch("sovtimer.providers.ESIHandler.result") as mock_result,
        ):
            mock_result.return_value = [{"campaign_id": 1}, {"campaign_id": 2}]

            result = ESIHandler.get_sovereignty_campaigns()

            self.assertEqual(len(result), 2)
            mock_result.assert_called_once()

            _, called_kwargs = mock_result.call_args

            self.assertIn("operation", called_kwargs)
            self.assertFalse(called_kwargs.get("force_refresh"))

    def test_raises_exception_when_result_raises(self):
        """
        Test that an exception is raised when the ESIHandler.result method raises an exception.

        :return:
        :rtype:
        """

        with (
            patch("sovtimer.providers.esi", new=MagicMock()),
            patch(
                "sovtimer.providers.ESIHandler.result", side_effect=Exception("Error")
            ) as mock_result,
        ):
            with self.assertRaises(Exception):
                ESIHandler.get_sovereignty_campaigns()

            mock_result.assert_called_once()

            _, called_kwargs = mock_result.call_args

            self.assertIn("operation", called_kwargs)
            self.assertFalse(called_kwargs.get("force_refresh"))

    def test_logs_debug_message_when_fetching_campaigns(self):
        """
        Test that a debug message is logged when fetching sovereignty campaigns from ESI.

        :return:
        :rtype:
        """

        with (
            patch("sovtimer.providers.esi", new=MagicMock()),
            patch("sovtimer.providers.logger.debug") as mock_logger,
            patch("sovtimer.providers.ESIHandler.result") as mock_result,
        ):
            mock_result.return_value = [{"campaign_id": 1}]

            ESIHandler.get_sovereignty_campaigns()

            mock_logger.assert_any_call("Fetching sovereignty campaigns from ESI...")


class TestESIHandlerGetSovereigntyStructures(BaseTestCase):
    """
    Test the ESIHandler.get_sovereignty_structures method.
    """

    def test_returns_structures_when_esi_returns_data(self):
        """
        Test that the method returns sovereignty structures when ESI returns data.

        :return:
        :rtype:
        """

        with (
            patch("sovtimer.providers.esi", new=MagicMock()),
            patch("sovtimer.providers.ESIHandler.result") as mock_result,
        ):
            mock_result.return_value = [{"structure_id": 1}, {"structure_id": 2}]

            result = ESIHandler.get_sovereignty_structures()

            self.assertEqual(len(result), 2)
            mock_result.assert_called_once()

            _, called_kwargs = mock_result.call_args

            self.assertIn("operation", called_kwargs)
            self.assertFalse(called_kwargs.get("force_refresh"))

    def test_raises_exception_when_result_raises(self):
        """
        Test that an exception is raised when the ESIHandler.result method raises an exception.

        :return:
        :rtype:
        """

        with (
            patch("sovtimer.providers.esi", new=MagicMock()),
            patch(
                "sovtimer.providers.ESIHandler.result", side_effect=Exception("Error")
            ) as mock_result,
        ):
            with self.assertRaises(Exception):
                ESIHandler.get_sovereignty_structures()

            mock_result.assert_called_once()

            _, called_kwargs = mock_result.call_args

            self.assertIn("operation", called_kwargs)
            self.assertFalse(called_kwargs.get("force_refresh"))

    def test_logs_debug_message_when_fetching_structures(self):
        """
        Test that a debug message is logged when fetching sovereignty structures from ESI.

        :return:
        :rtype:
        """

        with (
            patch("sovtimer.providers.esi", new=MagicMock()),
            patch("sovtimer.providers.logger.debug") as mock_logger,
            patch("sovtimer.providers.ESIHandler.result") as mock_result,
        ):
            mock_result.return_value = [{"structure_id": 1}]

            ESIHandler.get_sovereignty_structures()

            mock_logger.assert_any_call("Fetching sovereignty structures from ESI...")


class TestESIHandlerGetAlliancesAllianceId(BaseTestCase):
    """
    Test the ESIHandler.get_alliances_alliance_id method.
    """

    @patch("sovtimer.providers.esi", new=MagicMock())
    @patch("sovtimer.providers.ESIHandler.result")
    def test_returns_alliance_data_when_operation_succeeds(self, mock_result):
        """
        Test that the method returns alliance data when the ESI operation succeeds.

        :param mock_result:
        :type mock_result:
        :return:
        :rtype:
        """

        mock_response = {"alliance_id": 12345, "name": "Test Alliance"}
        mock_result.return_value = mock_response

        result = ESIHandler.get_alliances_alliance_id(alliance_id=12345)

        self.assertEqual(result, mock_response)
        mock_result.assert_called_once()
        _, called_kwargs = mock_result.call_args
        self.assertIn("operation", called_kwargs)
        self.assertFalse(called_kwargs.get("force_refresh"))

    @patch("sovtimer.providers.esi", new=MagicMock())
    @patch("sovtimer.providers.ESIHandler.result")
    def test_passes_force_refresh_to_result_operation(self, mock_result):
        """
        Test that the force_refresh parameter is passed correctly to the ESIHandler.result method.

        :param mock_result:
        :type mock_result:
        :return:
        :rtype:
        """

        mock_response = {"alliance_id": 12345, "name": "Test Alliance"}
        mock_result.return_value = mock_response

        result = ESIHandler.get_alliances_alliance_id(
            alliance_id=12345, force_refresh=True
        )

        self.assertEqual(result, mock_response)
        mock_result.assert_called_once()
        _, called_kwargs = mock_result.call_args
        self.assertIn("operation", called_kwargs)
        self.assertTrue(called_kwargs.get("force_refresh"))


class TestAppLogger(BaseTestCase):
    """
    Test the AppLogger provider.
    """

    def test_adds_prefix_to_log_message(self):
        """
        Tests that the AppLogger correctly adds a prefix to log messages.

        :return:
        :rtype:
        """

        logger = logging.getLogger("test_logger")
        app_logger = AppLogger(logger, "PREFIX")

        with self.assertLogs("test_logger", level="INFO") as log:
            app_logger.info("This is a test message")

        self.assertIn("[PREFIX] This is a test message", log.output[0])

    def test_handles_empty_prefix(self):
        """
        Tests that the AppLogger handles an empty prefix correctly.

        :return:
        :rtype:
        """

        logger = logging.getLogger("test_logger")
        app_logger = AppLogger(logger, "")

        with self.assertLogs("test_logger", level="INFO") as log:
            app_logger.info("Message without prefix")

        self.assertIn("Message without prefix", log.output[0])

    def test_handles_non_string_prefix(self):
        """
        Tests that the AppLogger handles a non-string prefix correctly.

        :return:
        :rtype:
        """

        logger = logging.getLogger("test_logger")
        app_logger = AppLogger(logger, 123)

        with self.assertLogs("test_logger", level="INFO") as log:
            app_logger.info("Message with numeric prefix")

        self.assertIn("[123] Message with numeric prefix", log.output[0])

    def test_handles_special_characters_in_prefix(self):
        """
        Tests that the AppLogger handles special characters in the prefix correctly.

        :return:
        :rtype:
        """

        logger = logging.getLogger("test_logger")
        app_logger = AppLogger(logger, "!@#$%^&*()")

        with self.assertLogs("test_logger", level="INFO") as log:
            app_logger.info("Message with special characters in prefix")

        self.assertIn(
            "[!@#$%^&*()] Message with special characters in prefix", log.output[0]
        )

    def test_handles_empty_message(self):
        """
        Tests that the AppLogger handles an empty log message correctly.

        :return:
        :rtype:
        """

        logger = logging.getLogger("test_logger")
        app_logger = AppLogger(logger, "PREFIX")

        with self.assertLogs("test_logger", level="INFO") as log:
            app_logger.info("")

        self.assertIn("[PREFIX] ", log.output[0])
