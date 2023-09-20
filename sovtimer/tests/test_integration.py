"""
Test basic integration
"""

# Third Party
from django_webtest import WebTest

# Django
from django.urls import reverse

# AA Sovereignty Timer
from sovtimer.tests.utils import create_fake_user


class TestSovtimerUI(WebTest):
    """
    Test Sovtimer UI
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup

        :return:
        :rtype:
        """

        super().setUpClass()

        cls.user_1001 = create_fake_user(
            character_id=1001,
            character_name="Bruce Wayne",
            permissions=["sovtimer.basic_access"],
        )
        cls.user_1002 = create_fake_user(
            character_id=1002, character_name="Peter Parker"
        )
        cls.user_1003 = create_fake_user(character_id=1003, character_name="Lex Luthor")

    def test_should_show_sovtimer_dashboard(self):
        # given
        self.app.set_user(user=self.user_1001)

        # when
        page = self.app.get(url=reverse(viewname="sovtimer:dashboard"))

        # then
        self.assertTemplateUsed(response=page, template_name="sovtimer/dashboard.html")

    def test_should_not_show_sovtimer_dashboard(self):
        # given
        self.app.set_user(user=self.user_1003)

        # when
        page = self.app.get(url=reverse(viewname="sovtimer:dashboard"))

        # then
        self.assertRedirects(
            response=page, expected_url="/account/login/?next=/sovereignty-timer/"
        )
