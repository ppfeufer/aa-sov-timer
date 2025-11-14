"""
Test basic integration
"""

# Third Party
from django_webtest import WebTest

# Django
from django.urls import reverse


class TestSovtimerUI(WebTest):
    """
    Test Sovtimer UI
    """

    def test_should_show_sovtimer_dashboard(self):
        # when
        page = self.app.get(url=reverse(viewname="sovtimer:dashboard"))

        # then
        self.assertTemplateUsed(response=page, template_name="sovtimer/dashboard.html")
