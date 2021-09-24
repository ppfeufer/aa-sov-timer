"""
Test ajax calls
"""

from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from django.test import RequestFactory, TestCase
from django.urls import reverse

from allianceauth.eveonline.models import EveCharacter

from sovtimer.tests.fixtures.load_allianceauth import load_allianceauth
from sovtimer.views import dashboard_data


class TestAjaxCalls(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.factory = RequestFactory()

        # given
        cls.character_1001 = EveCharacter.objects.get(character_id=1001)
        cls.character_1002 = EveCharacter.objects.get(character_id=1002)
        cls.character_1003 = EveCharacter.objects.get(character_id=1003)
        cls.character_1004 = EveCharacter.objects.get(character_id=1004)
        cls.character_1005 = EveCharacter.objects.get(character_id=1005)
        cls.character_1101 = EveCharacter.objects.get(character_id=1101)

        cls.user_with_basic_access, _ = create_user_from_evecharacter(
            cls.character_1001.character_id,
            permissions=["sovtimer.basic_access"],
        )

        add_character_to_user(cls.user_with_basic_access, cls.character_1101)

        cls.user_without_access, _ = create_user_from_evecharacter(
            cls.character_1002.character_id
        )

        add_character_to_user(cls.user_without_access, cls.character_1003)

    def test_ajax_dashboard_data_no_campaigns(self):
        # given
        self.client.force_login(self.user_with_basic_access)
        request = self.factory.get(reverse("sovtimer:dashboard"))
        request.user = self.user_with_basic_access

        # when
        result = dashboard_data(request=request)

        # then
        self.assertEqual(result.status_code, 200)
        self.assertJSONEqual(result.content, [])
