"""
Test ajax calls
"""

# Standard Library
from http import HTTPStatus

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# Alliance Auth (External Libs)
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

# AA Sovereignty Timer
from sovtimer.tests.fixtures.load_allianceauth import load_allianceauth
from sovtimer.tests.fixtures.load_sovtimer import load_sovtimer
from sovtimer.views import dashboard_data


class TestAjaxCalls(TestCase):
    """
    Test the ajax calls
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup

        :return:
        :rtype:
        """

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
            character_id=cls.character_1001.character_id,
            permissions=["sovtimer.basic_access"],
        )

        add_character_to_user(
            user=cls.user_with_basic_access, character=cls.character_1101
        )

        cls.user_without_access, _ = create_user_from_evecharacter(
            character_id=cls.character_1002.character_id
        )

        add_character_to_user(
            user=cls.user_without_access, character=cls.character_1003
        )

    def test_ajax_dashboard_data_no_campaigns(self):
        # given
        self.client.force_login(user=self.user_with_basic_access)
        request = self.factory.get(path=reverse(viewname="sovtimer:dashboard"))
        request.user = self.user_with_basic_access

        # when
        result = dashboard_data(request=request)

        # then
        self.assertEqual(first=result.status_code, second=HTTPStatus.OK)
        self.assertJSONEqual(raw=result.content, expected_data=[])

    def test_ajax_dashboard_data_with_campaigns(self):
        self.maxDiff = None
        # given
        load_sovtimer()
        self.client.force_login(user=self.user_with_basic_access)
        request = self.factory.get(path=reverse(viewname="sovtimer:dashboard"))
        request.user = self.user_with_basic_access

        # when
        result = dashboard_data(request=request)

        # then
        self.assertEqual(first=result.status_code, second=HTTPStatus.OK)
        # self.assertJSONEqual(
        #     result.content,
        #     [
        #         {
        #             "event_type": "TCU",
        #             "solar_system_name": "0-O6XF",
        #             "solar_system_name_html": '<a href="http://evemaps.dotlan.net/map/Esoteria/0-O6XF" target="_blank" rel="noopener noreferer">0-O6XF</a>',
        #             "constellation_name": "Q-2BI6",
        #             "constellation_name_html": '<a href="//evemaps.dotlan.net/search?q=Q-2BI6" target="_blank" rel="noopener noreferer">Q-2BI6</a>',
        #             "region_name": "Esoteria",
        #             "region_name_html": '<a href="http://evemaps.dotlan.net/map/Esoteria" target="_blank" rel="noopener noreferer">Esoteria</a>',
        #             "defender_name": "Wayne Enterprises",
        #             "defender_name_html": '<a href="http://evemaps.dotlan.net/alliance/Wayne_Enterprises" target="_blank" rel="noopener noreferer"><img class="aa-sovtimer-entity-logo-left me-2" src="https://images.evetech.net/alliances/3001/logo?size=32" alt="Wayne Enterprises">Wayne Enterprises</a>',
        #             "adm": 6.0,
        #             "start_time": "2021-10-14T11:38:37Z",
        #             "remaining_time": "",
        #             "remaining_time_in_seconds": 5734.00943,
        #             "campaign_progress": "60%",
        #             "active_campaign": "No",
        #         }
        #     ],
        # )
