"""
Test for the providers module.
"""

# Standard Library
import importlib
import logging
import sys
import types
import typing
from unittest.mock import MagicMock, patch

# Third Party
from aiopenapi3 import ContentTypeError, RequestError

# Alliance Auth
from esi.exceptions import HTTPClientError, HTTPNotModified

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.providers.applogger import AppLogger
from sovtimer.providers.esi import ESIHandler
from sovtimer.tests import BaseTestCase


class TestTypingTypeCheckingIfCondition(BaseTestCase):
    """
    Test the `typing.TYPE_CHECKING` if condition.
    """

    def test_when_typing_TYPE_CHECKING_true_then_stub_types_are_imported_into_module_namespace(
        self,
    ):
        """
        Test that when `typing.TYPE_CHECKING` is set to `True`, the stub types from `esi.stubs` are imported into the module namespace.

        :return:
        :rtype:
        """

        fake_stubs = types.ModuleType("esi.stubs")
        fake_stubs.AllianceDetail = type("AllianceDetail", (), {})
        fake_stubs.SovereigntyCampaignsGetItem = type(
            "SovereigntyCampaignsGetItem", (), {}
        )

        original_sys_modules = sys.modules.copy()

        try:
            sys.modules["esi.stubs"] = fake_stubs

            with patch.object(typing, "TYPE_CHECKING", True):
                providers = importlib.import_module("sovtimer.providers.esi")
                importlib.reload(providers)

                self.assertTrue(hasattr(providers, "AllianceDetail"))
                self.assertTrue(hasattr(providers, "SovereigntyCampaignsGetItem"))
        finally:
            sys.modules.clear()
            sys.modules.update(original_sys_modules)

            try:
                importlib.reload(importlib.import_module("sovtimer.providers.esi"))
            except Exception:
                pass


class TestESIHandlerResult(BaseTestCase):
    """
    Test the ESIHandler.result method.
    """

    def test_returns_result_when_operation_succeeds(self):
        """
        Test returning an ESIHandler result.

        :return:
        :rtype:
        """

        operation = MagicMock()
        operation.operation = MagicMock(operationId="GetSomething")
        operation.result.return_value = {"data": 1}

        result = ESIHandler.result(
            operation=operation,
            use_etag=True,
            return_response=False,
            force_refresh=False,
            use_cache=True,
        )

        self.assertEqual(result, {"data": 1})
        operation.result.assert_called_once_with(
            use_etag=True, return_response=False, force_refresh=False, use_cache=True
        )

    def test_returns_result_and_response_when_return_response_true(self):
        """
        Test returning an ESIHandler result along with the response when `return_response` is set to `True`.

        :return:
        :rtype:
        """

        operation = MagicMock()
        operation.operation = MagicMock(operationId="GetSomething")
        response_obj = MagicMock()
        operation.result.return_value = ([1, 2, 3], response_obj)

        result = ESIHandler.result(
            operation=operation,
            use_etag=False,
            return_response=True,
            force_refresh=True,
            use_cache=False,
        )

        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], [1, 2, 3])
        self.assertIs(result[1], response_obj)
        operation.result.assert_called_once_with(
            use_etag=False, return_response=True, force_refresh=True, use_cache=False
        )

    def test_returns_none_on_http_not_modified(self):
        """
        Test returns `None` on HTTP Not Modified.

        :return:
        :rtype:
        """

        operation = MagicMock()
        operation.operation = MagicMock(operationId="GetSomething")
        # HTTPNotModified requires status_code and headers
        operation.result.side_effect = HTTPNotModified(304, {})

        result = ESIHandler.result(operation=operation, return_response=False)

        self.assertIsNone(result)

    def test_returns_none_tuple_on_http_not_modified_when_return_response_true(self):
        """
        Test returns `None` on HTTP Not Modified when `return_response` is set to `True`.

        :return:
        :rtype:
        """

        operation = MagicMock()
        operation.operation = MagicMock(operationId="GetSomething")
        # HTTPNotModified requires status_code and headers
        operation.result.side_effect = HTTPNotModified(304, {})

        result = ESIHandler.result(operation=operation, return_response=True)

        self.assertEqual(result, (None, None))

    def test_returns_none_on_content_type_error(self):
        """
        Test returns `None` on content type error.

        :return:
        :rtype:
        """

        operation = MagicMock()
        operation.operation = MagicMock(operationId="GetSomething")
        # ContentTypeError requires operation, content_type, message and response
        operation.result.side_effect = ContentTypeError(
            None, "application/json", "invalid", None
        )

        result = ESIHandler.result(operation=operation)

        self.assertIsNone(result)

    def test_returns_none_on_client_or_request_error(self):
        """
        Test returns `None` on client or request error.

        :return:
        :rtype:
        """

        # HTTPClientError requires status_code, headers and data; construct with dummy values
        client_exc = HTTPClientError(500, {}, None)
        # RequestError requires operation, request, data and parameters
        request_exc = RequestError(None, None, None, None)

        for exc in (client_exc, request_exc):
            operation = MagicMock()
            operation.operation = MagicMock(operationId="GetSomething")
            operation.result.side_effect = exc

            result = ESIHandler.result(operation=operation)
            self.assertIsNone(result)

    def test_passes_extra_kwargs_to_operation_result(self):
        """
        Test passes extra kwargs to operation result.

        :return:
        :rtype:
        """

        operation = MagicMock()
        operation.operation = MagicMock(operationId="GetSomething")
        operation.result.return_value = "ok"

        result = ESIHandler.result(
            operation=operation,
            use_etag=False,
            return_response=False,
            force_refresh=True,
            use_cache=False,
            foo="bar",
        )

        self.assertEqual(result, "ok")
        operation.result.assert_called_once_with(
            use_etag=False,
            return_response=False,
            force_refresh=True,
            use_cache=False,
            foo="bar",
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
            patch("sovtimer.providers.esi.esi", new=MagicMock()),
            patch("sovtimer.providers.esi.ESIHandler.result") as mock_result,
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
            patch("sovtimer.providers.esi.esi", new=MagicMock()),
            patch(
                "sovtimer.providers.esi.ESIHandler.result",
                side_effect=Exception("Error"),
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
            patch("sovtimer.providers.esi.esi", new=MagicMock()),
            patch("sovtimer.providers.esi.logger.debug") as mock_logger,
            patch("sovtimer.providers.esi.ESIHandler.result") as mock_result,
        ):
            mock_result.return_value = [{"campaign_id": 1}]

            ESIHandler.get_sovereignty_campaigns()

            mock_logger.assert_any_call("Fetching sovereignty campaigns from ESI…")


class TestESIHandlerGetAlliancesAllianceId(BaseTestCase):
    """
    Test the ESIHandler.get_alliances_alliance_id method.
    """

    @patch("sovtimer.providers.esi.esi", new=MagicMock())
    @patch("sovtimer.providers.esi.ESIHandler.result")
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

    @patch("sovtimer.providers.esi.esi", new=MagicMock())
    @patch("sovtimer.providers.esi.ESIHandler.result")
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


class TestESIHandlerGetSovereigntySystems(BaseTestCase):
    """
    Test the ESIHandler.get_sovereignty_systems method.
    """

    def test_returns_systems_when_esi_returns_data(self):
        """
        Test that the ESIHandler.get_sovereignty_systems method returns a list of systems.

        :return:
        :rtype:
        """

        with (
            patch("sovtimer.providers.esi.esi", new=MagicMock()),
            patch("sovtimer.providers.esi.ESIHandler.result") as mock_result,
        ):
            mock_result.return_value = [{"system_id": 1}, {"system_id": 2}]

            result = ESIHandler.get_sovereignty_systems()

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
            patch("sovtimer.providers.esi.esi", new=MagicMock()),
            patch(
                "sovtimer.providers.esi.ESIHandler.result",
                side_effect=Exception("Error"),
            ) as mock_result,
        ):
            with self.assertRaises(Exception):
                ESIHandler.get_sovereignty_systems()

            mock_result.assert_called_once()
            _, called_kwargs = mock_result.call_args
            self.assertIn("operation", called_kwargs)
            self.assertFalse(called_kwargs.get("force_refresh"))

    def test_logs_debug_message_when_fetching_systems(self):
        """
        Test that the AppLogger provider correctly logs system information.

        :return:
        :rtype:
        """

        with (
            patch("sovtimer.providers.esi.esi", new=MagicMock()),
            patch("sovtimer.providers.esi.logger.debug") as mock_logger,
            patch("sovtimer.providers.esi.ESIHandler.result") as mock_result,
        ):
            mock_result.return_value = [{"system_id": 1}]

            ESIHandler.get_sovereignty_systems()

            mock_logger.assert_any_call("Fetching sovereignty systems from ESI…")


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
        app_logger = AppLogger(logger)

        with self.assertLogs("test_logger", level="INFO") as log:
            app_logger.info("This is a test message")

        self.assertIn(f"[{__title__}] This is a test message", log.output[0])

    def test_handles_empty_message(self):
        """
        Tests that the AppLogger handles an empty log message correctly.

        :return:
        :rtype:
        """

        logger = logging.getLogger("test_logger")
        app_logger = AppLogger(logger)

        with self.assertLogs("test_logger", level="INFO") as log:
            app_logger.info("")

        self.assertIn(f"[{__title__}] ", log.output[0])
