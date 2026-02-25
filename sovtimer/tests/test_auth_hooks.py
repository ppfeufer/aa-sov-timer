# Standard Library
from http import HTTPStatus

# Django
from django.test import RequestFactory
from django.urls import reverse

# AA Sovereignty Timer
from sovtimer.auth_hooks import AaSovtimerMenuItem, register_menu
from sovtimer.tests import BaseTestCase


class TestAaSovtimerMenuItem(BaseTestCase):
    """
    Test the AaSovtimerMenuItem class
    """

    def setUp(self):
        """
        Setup the test case

        :return:
        :rtype:
        """

        self.menu_item = AaSovtimerMenuItem()
        self.factory = RequestFactory()

    @classmethod
    def setUpClass(cls) -> None:
        """
        Set up the test class by creating necessary test data, such as a fake user and expected HTML snippets for menu items and public pages.

        :return:
        :rtype:
        """

        super().setUpClass()

        # User
        cls.user_1001 = BaseTestCase.create_fake_user(
            character_id=1009, character_name="Peter Parker"
        )

        cls.html_menu = f"""
                    <li class="d-flex flex-wrap m-2 p-2 pt-0 pb-0 mt-0 mb-0 me-0 pe-0">
                        <i class="nav-link fa-regular fa-clock fa-fw align-self-center me-3"></i>
                        <a class="nav-link flex-fill align-self-center me-auto" href="{reverse('sovtimer:dashboard')}">
                            Sovereignty Timer
                        </a>
                    </li>
                """

        cls.header_public_page = '<div class="navbar-brand">Sovereignty Timer</div>'

    def test_render_hook_with_user_logged_in(self):
        """
        Test should show the link to the app in the navigation to user with access

        :return:
        :rtype:
        """

        self.client.force_login(user=self.user_1001)

        response = self.client.get(path=reverse(viewname="authentication:dashboard"))

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)
        self.assertInHTML(
            needle=self.html_menu,
            haystack=BaseTestCase.response_content_to_str(response),
        )

    def test_render_hook_with_public_page(self):
        """
        Test should show the public page

        :return:
        :rtype:
        """

        response = self.client.get(path=reverse(viewname="sovtimer:dashboard"))

        self.assertEqual(first=response.status_code, second=HTTPStatus.OK)

    def test_renders_correct_menu_item_text(self):
        """
        Test that the menu item text is correct

        :return:
        :rtype:
        """

        self.assertEqual(self.menu_item.text, "Sovereignty Timer")

    def test_renders_correct_menu_item_classes(self):
        """
        Test that the menu item classes are correct

        :return:
        :rtype:
        """

        self.assertEqual(self.menu_item.classes, "fa-regular fa-clock")


class TestRegisterMenu(BaseTestCase):
    """
    Test the register_menu function
    """

    def test_returns_menu_item_instance(self):
        """
        Test that the register_menu function returns an instance of AaSovtimerMenuItem

        :return:
        :rtype:
        """

        menu_item = register_menu()

        self.assertIsInstance(menu_item, AaSovtimerMenuItem)

    def test_menu_item_has_correct_text(self):
        """
        Test that the menu item text is correct

        :return:
        :rtype:
        """

        menu_item = register_menu()

        self.assertEqual(menu_item.text, "Sovereignty Timer")

    def test_menu_item_has_correct_classes(self):
        """
        Test that the menu item classes are correct

        :return:
        :rtype:
        """

        menu_item = register_menu()

        self.assertEqual(menu_item.classes, "fa-regular fa-clock")
