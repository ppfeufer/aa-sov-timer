"""
Test the ETag helper
"""

# Standard Library
from http import HTTPStatus
from unittest.mock import MagicMock, patch

# Django
from django.test import TestCase

# Alliance Auth
from esi.exceptions import HTTPNotModified

# AA Sovereignty Timer
from sovtimer import __package_name__
from sovtimer.constants import ETAG_TTL
from sovtimer.handler.etag import NotModifiedError
from sovtimer.providers import etag


class TestEtagResult(TestCase):
    """
    Test the etag_result method of the Etag class.
    """

    @patch("sovtimer.handler.etag.logger")
    @patch("sovtimer.handler.etag.Etag.single_page")
    @patch("sovtimer.handler.etag.Etag.get_total_pages")
    @patch("sovtimer.handler.etag.Etag.update_page_num")
    def test_returns_combined_data_for_paginated_operation(
        self, mock_update_page_num, mock_get_total_pages, mock_single_page, mock_logger
    ):
        """
        Test that etag_result correctly handles paginated operations by combining results from all pages.

        :param mock_update_page_num:
        :type mock_update_page_num:
        :param mock_get_total_pages:
        :type mock_get_total_pages:
        :param mock_single_page:
        :type mock_single_page:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        operation = MagicMock()
        operation._has_page_param.return_value = True
        mock_get_total_pages.return_value = 3
        mock_single_page.side_effect = [
            (["data_page_1"], MagicMock(headers={"X-Pages": "3"})),
            (["data_page_2"], MagicMock()),
            (["data_page_3"], MagicMock()),
        ]

        result = etag.etag_result(operation=operation)

        self.assertEqual(result, ["data_page_1", "data_page_2", "data_page_3"])
        self.assertEqual(mock_single_page.call_count, 3)
        mock_update_page_num.assert_called_with(operation=operation, page_number=3)
        mock_logger.info.assert_called()

    @patch("sovtimer.handler.etag.logger")
    @patch("sovtimer.handler.etag.Etag.single_page")
    def test_returns_data_for_non_paginated_operation(
        self, mock_single_page, mock_logger
    ):
        """
        Test that etag_result correctly handles non-paginated operations by returning the single page result.

        :param mock_single_page:
        :type mock_single_page:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        mock_single_page.return_value = ([{"id": 1}], None)

        operation = MagicMock()
        operation._has_page_param.return_value = False

        result = etag.etag_result(operation=operation)

        self.assertEqual(result, [{"id": 1}])
        mock_logger.info.assert_not_called()

    @patch("sovtimer.handler.etag.Etag.single_page")
    def test_forces_refresh_when_flag_is_set(self, mock_single_page):
        """
        Test that etag_result forces a refresh when the force_refresh flag is set.

        :param mock_single_page:
        :type mock_single_page:
        :return:
        :rtype:
        """

        operation = MagicMock()
        operation._has_page_param.return_value = False
        mock_response = MagicMock()
        mock_response.headers = {"ETag": "test-etag"}
        mock_single_page.return_value = (["data_page"], mock_response)

        result = etag.etag_result(operation=operation, force_refresh=True)

        self.assertEqual(result, ["data_page"])
        mock_single_page.assert_called_once_with(
            operation=operation, force_refresh=True
        )

    @patch("sovtimer.handler.etag.Etag.single_page")
    @patch("sovtimer.handler.etag.Etag.get_total_pages")
    def test_handles_no_data_in_pages(self, mock_get_total_pages, mock_single_page):
        """
        Test that etag_result handles the case where no data is returned from any page.

        :param mock_get_total_pages:
        :type mock_get_total_pages:
        :param mock_single_page:
        :type mock_single_page:
        :return:
        :rtype:
        """

        operation = MagicMock()
        operation._has_page_param.return_value = True
        mock_get_total_pages.return_value = 2
        mock_single_page.side_effect = [
            ([], MagicMock(headers={"X-Pages": "2"})),
            ([], MagicMock()),
        ]

        result = etag.etag_result(operation=operation)

        self.assertEqual(result, [])
        self.assertEqual(mock_single_page.call_count, 2)


class TestSinglePage(TestCase):
    """
    Test the single_page method of the Etag class.
    """

    @patch("sovtimer.handler.etag.logger")
    @patch("sovtimer.handler.etag.Etag.del_etag_header")
    @patch("sovtimer.handler.etag.Etag.get_etag_header")
    def test_returns_data_and_response_when_operation_succeeds(
        self, mock_get_etag_header, mock_del_etag_header, mock_logger
    ):
        """
        Test that single_page returns data and response when the operation succeeds.

        :param mock_get_etag_header:
        :type mock_get_etag_header:
        :param mock_del_etag_header:
        :type mock_del_etag_header:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """
        mock_get_etag_header.return_value = "test-etag"
        operation = MagicMock()
        operation.result.return_value = (
            {"key": "value"},
            MagicMock(headers={"ETag": "new-etag"}),
        )

        data, res = etag.single_page(operation=operation, force_refresh=False)

        self.assertEqual(data, {"key": "value"})
        self.assertEqual(res.headers["ETag"], "new-etag")
        mock_get_etag_header.assert_called_once_with(operation)
        mock_del_etag_header.assert_not_called()

    @patch("sovtimer.handler.etag.logger")
    @patch("sovtimer.handler.etag.Etag.del_etag_header")
    @patch("sovtimer.handler.etag.Etag.get_etag_header")
    def test_raises_not_modified_error_when_http_not_modified(
        self, mock_get_etag_header, mock_del_etag_header, mock_logger
    ):
        """
        Test that single_page raises NotModifiedError when HTTPNotModified is raised.

        :param mock_get_etag_header:
        :type mock_get_etag_header:
        :param mock_del_etag_header:
        :type mock_del_etag_header:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        mock_get_etag_header.return_value = "test-etag"
        operation = MagicMock()
        operation.result.side_effect = HTTPNotModified(
            status_code=HTTPStatus.NOT_MODIFIED, headers={"ETag": "test-etag"}
        )

        with self.assertRaises(NotModifiedError):
            etag.single_page(operation=operation, force_refresh=False)

        mock_get_etag_header.assert_called_once_with(operation)
        mock_logger.debug.assert_called()

    @patch("sovtimer.handler.etag.logger")
    @patch("sovtimer.handler.etag.Etag.del_etag_header")
    @patch("sovtimer.handler.etag.Etag.get_etag_header")
    def test_raises_not_modified_error_when_etag_matches_response(
        self, mock_get_etag_header, mock_del_etag_header, mock_logger
    ):
        """
        Test that single_page raises NotModifiedError when the ETag matches the cached ETag.

        :param mock_get_etag_header:
        :type mock_get_etag_header:
        :param mock_del_etag_header:
        :type mock_del_etag_header:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        mock_get_etag_header.return_value = "test-etag"
        operation = MagicMock()
        operation.result.return_value = (
            {"key": "value"},
            MagicMock(headers={"ETag": "test-etag"}),
        )

        with self.assertRaises(NotModifiedError):
            etag.single_page(operation=operation, force_refresh=False)

        mock_get_etag_header.assert_called_once_with(operation)
        mock_logger.debug.assert_called()

    @patch("sovtimer.handler.etag.logger")
    @patch("sovtimer.handler.etag.Etag.del_etag_header")
    @patch("sovtimer.handler.etag.Etag.get_etag_header")
    def test_deletes_etag_header_when_force_refresh_is_true(
        self, mock_get_etag_header, mock_del_etag_header, mock_logger
    ):
        """
        Test that single_page deletes the ETag header when force_refresh is True.

        :param mock_get_etag_header:
        :type mock_get_etag_header:
        :param mock_del_etag_header:
        :type mock_del_etag_header:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        mock_get_etag_header.return_value = "test-etag"
        operation = MagicMock()
        operation.result.return_value = (
            {"key": "value"},
            MagicMock(headers={"ETag": "new-etag"}),
        )

        data, res = etag.single_page(operation=operation, force_refresh=True)

        self.assertEqual(data, {"key": "value"})
        self.assertEqual(res.headers["ETag"], "new-etag")
        mock_del_etag_header.assert_called_once_with(operation)
        mock_get_etag_header.assert_called_once_with(operation)


class TestGetTotalPages(TestCase):
    """
    Test the get_total_pages method of the Etag class.
    """

    @patch("sovtimer.handler.etag.logger")
    def test_returns_total_pages_from_response_headers(self, mock_logger):
        """
        Test that get_total_pages returns the total number of pages from the response headers.

        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        response = MagicMock(headers={"X-Pages": "5"})

        result = etag.get_total_pages(res=response)

        self.assertEqual(result, 5)

    @patch("sovtimer.handler.etag.logger")
    def test_returns_one_when_x_pages_header_is_missing(self, mock_logger):
        """
        Test that get_total_pages returns 1 when the X-Pages header is missing.

        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        response = MagicMock(headers={})

        result = etag.get_total_pages(res=response)

        self.assertEqual(result, 1)

    @patch("sovtimer.handler.etag.logger")
    def test_returns_one_when_response_is_none(self, mock_logger):
        """
        Test that get_total_pages returns 1 when the response is None.

        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        result = etag.get_total_pages(res=None)

        self.assertEqual(result, 1)

    @patch("sovtimer.handler.etag.logger")
    def test_raises_value_error_when_x_pages_is_not_an_integer(self, mock_logger):
        """
        Test that get_total_pages raises ValueError when the X-Pages header is not an integer.

        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        response = MagicMock(headers={"X-Pages": "invalid"})

        with self.assertRaises(ValueError):
            etag.get_total_pages(res=response)


class testUpdatePageNum(TestCase):
    """
    Test the update_page_num method of the Etag class.
    """

    def test_updates_page_number_for_paginated_operation(self):
        """
        Test that update_page_num updates the page number parameter for operations that support pagination.

        :return:
        :rtype:
        """

        operation = MagicMock()
        operation._has_page_param.return_value = True
        operation._kwargs = {}

        etag.update_page_num(operation=operation, page_number=3)

        self.assertIn("page", operation._kwargs)
        self.assertEqual(operation._kwargs["page"], 3)

    def test_does_not_update_page_number_for_non_paginated_operation(self):
        """
        Test that update_page_num does not update the page number parameter for operations that do not support pagination.

        :return:
        :rtype:
        """

        operation = MagicMock()
        operation._has_page_param.return_value = False
        operation._kwargs = {}

        etag.update_page_num(operation=operation, page_number=3)

        self.assertNotIn("page", operation._kwargs)


class TestSetEtagHeader(TestCase):
    """
    Test the set_etag_header method of the Etag class.
    """

    @patch("sovtimer.handler.etag.logger")
    @patch("sovtimer.handler.etag.cache.set")
    @patch("sovtimer.handler.etag.Etag.get_etag_key")
    def test_stores_etag_in_cache_when_etag_is_present(
        self, mock_get_etag_key, mock_cache_set, mock_logger
    ):
        """
        Test that set_etag_header stores the ETag in the cache when the ETag is present in the response.

        :param mock_get_etag_key:
        :type mock_get_etag_key:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        mock_get_etag_key.return_value = "etag-key"
        mock_cache_set.return_value = True
        response = MagicMock(headers={"ETag": "test-etag"})

        etag.set_etag_header(operation=MagicMock(), response=response)

        mock_cache_set.assert_called_once_with(
            key="etag-key", value="test-etag", timeout=ETAG_TTL
        )
        mock_logger.debug.assert_called()

    @patch("sovtimer.handler.etag.logger")
    @patch("sovtimer.handler.etag.cache.set")
    @patch("sovtimer.handler.etag.Etag.get_etag_key")
    def test_does_not_store_etag_in_cache_when_etag_is_missing(
        self, mock_get_etag_key, mock_cache_set, mock_logger
    ):
        """
        Test that set_etag_header does not store the ETag in the cache when the ETag is missing from the response.

        :param mock_get_etag_key:
        :type mock_get_etag_key:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        mock_get_etag_key.return_value = "etag-key"
        response = MagicMock(headers={})

        etag.set_etag_header(operation=MagicMock(), response=response)

        mock_cache_set.assert_not_called()
        mock_logger.debug.assert_not_called()

    @patch("sovtimer.handler.etag.logger")
    @patch("sovtimer.handler.etag.cache.set")
    @patch("sovtimer.handler.etag.Etag.get_etag_key")
    def test_does_not_store_etag_in_cache_when_response_is_none(
        self, mock_get_etag_key, mock_cache_set, mock_logger
    ):
        """
        Test that set_etag_header does not store the ETag in the cache when the response is None.

        :param mock_get_etag_key:
        :type mock_get_etag_key:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        mock_get_etag_key.return_value = "etag-key"

        etag.set_etag_header(operation=MagicMock(), response=None)

        mock_cache_set.assert_not_called()
        mock_logger.debug.assert_not_called()


class TestDelEtagHeader(TestCase):
    """
    Test the del_etag_header method of the Etag class.
    """

    @patch("sovtimer.handler.etag.cache.delete")
    @patch("sovtimer.handler.etag.Etag.get_etag_key")
    def test_deletes_etag_from_cache_successfully(
        self, mock_get_etag_key, mock_cache_delete
    ):
        """
        Test that del_etag_header deletes the ETag from the cache and returns True when deletion is successful.

        :param mock_get_etag_key:
        :type mock_get_etag_key:
        :param mock_cache_delete:
        :type mock_cache_delete:
        :return:
        :rtype:
        """

        mock_get_etag_key.return_value = "etag-key"
        mock_cache_delete.return_value = True

        result = etag.del_etag_header(operation=MagicMock())

        self.assertTrue(result)
        mock_cache_delete.assert_called_once_with(key="etag-key", version=False)

    @patch("sovtimer.handler.etag.cache.delete")
    @patch("sovtimer.handler.etag.Etag.get_etag_key")
    def test_returns_false_when_deletion_is_unsuccessful(
        self, mock_get_etag_key, mock_cache_delete
    ):
        """
        Test that del_etag_header returns False when deletion is unsuccessful.

        :param mock_get_etag_key:
        :type mock_get_etag_key:
        :param mock_cache_delete:
        :type mock_cache_delete:
        :return:
        :rtype:
        """

        mock_get_etag_key.return_value = "etag-key"
        mock_cache_delete.return_value = False

        result = etag.del_etag_header(operation=MagicMock())

        self.assertFalse(result)
        mock_cache_delete.assert_called_once_with(key="etag-key", version=False)


class TestGetEtagHeader(TestCase):
    """
    Test the get_etag_header method of the Etag class.
    """

    @patch("sovtimer.handler.etag.cache.get")
    @patch("sovtimer.handler.etag.Etag.get_etag_key")
    def test_retrieves_etag_from_cache(self, mock_get_etag_key, mock_cache_get):
        """
        Test that get_etag_header retrieves the ETag from the cache when it exists.

        :param mock_get_etag_key:
        :type mock_get_etag_key:
        :param mock_cache_get:
        :type mock_cache_get:
        :return:
        :rtype:
        """

        mock_get_etag_key.return_value = "etag-key"
        mock_cache_get.return_value = "test-etag"

        result = etag.get_etag_header(operation=MagicMock())

        self.assertEqual(result, "test-etag")
        mock_cache_get.assert_called_once_with(key="etag-key", default=False)

    @patch("sovtimer.handler.etag.cache.get")
    @patch("sovtimer.handler.etag.Etag.get_etag_key")
    def test_returns_false_when_etag_not_in_cache(
        self, mock_get_etag_key, mock_cache_get
    ):
        """
        Test that get_etag_header returns False when the ETag does not exist in the cache.

        :param mock_get_etag_key:
        :type mock_get_etag_key:
        :param mock_cache_get:
        :type mock_cache_get:
        :return:
        :rtype:
        """

        mock_get_etag_key.return_value = "etag-key"
        mock_cache_get.return_value = False

        result = etag.get_etag_header(operation=MagicMock())

        self.assertFalse(result)
        mock_cache_get.assert_called_once_with(key="etag-key", default=False)


class TestGetEtagKey(TestCase):
    """
    Test the get_etag_key method of the Etag class.
    """

    @patch("sovtimer.handler.etag.EsiOperation._cache_key", create=True)
    def test_returns_correct_etag_key_for_operation(self, mock_cache_key):
        """
        Test that get_etag_key returns the correct ETag key for a given operation.

        :param mock_cache_key:
        :type mock_cache_key:
        :return:
        :rtype:
        """

        operation = MagicMock()
        operation._cache_key.return_value = "operation-key"

        etag_prefix = f"etag-{__package_name__}"
        expected_key = f"{etag_prefix}-operation-key"

        result = etag.get_etag_key(operation=operation)

        self.assertEqual(result, expected_key)
        operation._cache_key.assert_called_once()

    @patch("sovtimer.handler.etag.EsiOperation._cache_key")
    def test_raises_attribute_error_when_operation_has_no_cache_key(
        self, mock_cache_key
    ):
        """
        Test that get_etag_key raises AttributeError when the operation does not have a _cache_key method.

        :param mock_cache_key:
        :type mock_cache_key:
        :return:
        :rtype:
        """

        class NoCacheKey:
            pass

        with self.assertRaises(AttributeError):
            etag.get_etag_key(operation=NoCacheKey())
