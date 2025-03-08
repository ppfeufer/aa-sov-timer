"""
Test the app settings in local.py
"""

# Django
from django.test import TestCase, override_settings

# AA Sovereignty Timer
from sovtimer.app_settings import debug_enabled


class TestAppSettings(TestCase):
    """
    Tests for App Settings
    """

    @override_settings(DEBUG=True)
    def test_debug_enabled_with_debug_true(self) -> None:
        """
        Test debug_enabled with DEBUG = True

        :return:
        :rtype:
        """

        self.assertTrue(debug_enabled())

    @override_settings(DEBUG=False)
    def test_debug_enabled_with_debug_false(self) -> None:
        """
        Test debug_enabled with DEBUG = False

        :return:
        :rtype:
        """

        self.assertFalse(debug_enabled())
