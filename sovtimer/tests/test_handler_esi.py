# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock

# Third Party
from aiopenapi3 import ContentTypeError

# Alliance Auth
from esi.exceptions import HTTPClientError, HTTPNotModified

# AA Sovereignty Timer
from sovtimer.handler.esi_handler import result
from sovtimer.tests import BaseTestCase


class TestHandlerEsi(BaseTestCase):
    """
    Test ESI handler functions
    """

    def test_returns_operation_result_when_operation_succeeds(self):
        """
        Test that the result function returns the operation result when it succeeds.

        :return:
        :rtype:
        """

        op = MagicMock()
        op.operation = "op"
        op.result.return_value = {"data": "success"}

        res = result(op)

        self.assertEqual(res, {"data": "success"})

    def test_returns_cached_data_when_esi_not_modified_and_return_cached_true(self):
        """
        Test that the result function returns cached data when ESI returns 304 Not Modified
        and return_cached_for_304 is True.

        :return:
        :rtype:
        """

        op = MagicMock()
        op.operation = "op"
        op.result.side_effect = [
            HTTPNotModified(HTTPStatus.NOT_MODIFIED, {}),
            {"fleet": [{"fleet_id": 12345}]},
        ]

        res = result(op, return_cached_for_304=True)

        self.assertEqual(res, {"fleet": [{"fleet_id": 12345}]})

    def test_returns_none_when_esi_not_modified_and_return_cached_false(self):
        """
        Test that the result function returns None when ESI returns 304 Not Modified
        and return_cached_for_304 is False.

        :return:
        :rtype:
        """

        op = MagicMock()
        op.operation = "op"
        op.result.side_effect = HTTPNotModified(HTTPStatus.NOT_MODIFIED, {})

        res = result(op, return_cached_for_304=False)

        self.assertIsNone(res)

    def test_handles_content_type_error_and_returns_none(self):
        """
        Test that the result function handles ContentTypeError and returns None.

        :return:
        :rtype:
        """

        op = MagicMock()
        op.operation = "op"
        op.result.side_effect = ContentTypeError(
            op.operation, "text/plain", "Invalid content type", MagicMock()
        )

        res = result(op)

        self.assertIsNone(res)

    def test_handles_http_client_error_and_returns_none(self):
        """
        Test that the result function handles HTTPClientError and returns None.

        :return:
        :rtype:
        """

        op = MagicMock()
        op.operation = "op"
        op.result.side_effect = HTTPClientError(
            HTTPStatus.BAD_REQUEST, {}, b"Client error"
        )

        res = result(op)

        self.assertIsNone(res)
