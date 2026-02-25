"""
Tests for the app settings
"""

# Django
from django.test import override_settings

# AA Sovereignty Timer
from sovtimer.app_settings import debug_enabled
from sovtimer.tests import BaseTestCase


class TestAppSettings(BaseTestCase):
    """
    Test the app settings
    """

    def test_returns_true_when_debug_is_enabled(self):
        """
        Test that the debug_enabled function returns True when DEBUG is enabled

        :return:
        :rtype:
        """

        with override_settings(DEBUG=True):
            self.assertTrue(debug_enabled())

    def test_returns_false_when_debug_is_disabled(self):
        """
        Test that the debug_enabled function returns False when DEBUG is disabled

        :return:
        :rtype:
        """

        with override_settings(DEBUG=False):
            self.assertFalse(debug_enabled())
