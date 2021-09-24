"""
Test basic integration
"""

from django_webtest import WebTest

from django.urls import reverse

from .utils import create_fake_user


class TestSovtimerUI(WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_1001 = create_fake_user(
            1001, "Bruce Wayne", permissions=["sovtimer.basic_access"]
        )
        cls.user_1002 = create_fake_user(1002, "Peter Parker")
        cls.user_1003 = create_fake_user(1003, "Lex Luthor")

    def test_should_show_sovtimer_dashboard(self):
        # given
        self.app.set_user(self.user_1001)

        # when
        page = self.app.get(reverse("sovtimer:dashboard"))

        # then
        self.assertTemplateUsed(page, "sovtimer/dashboard.html")

    def test_should_not_show_sovtimer_dashboard(self):
        # given
        self.app.set_user(self.user_1003)

        # when
        page = self.app.get(reverse("sovtimer:dashboard"))

        # then
        self.assertRedirects(page, "/account/login/?next=/sovereignty-timer/")
