"""
Test ajax calls
"""

# Standard Library
import json
from http import HTTPStatus

# Django
from django.test import RequestFactory
from django.urls import reverse

# Alliance Auth
from allianceauth.eveonline.models import EveCharacter

# Alliance Auth (External Libs)
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

# AA Sovereignty Timer
from sovtimer.tests import BaseTestCase
from sovtimer.tests.fixtures.load_allianceauth import load_allianceauth
from sovtimer.tests.fixtures.load_sovtimer import load_sovtimer
from sovtimer.views import dashboard_data


class TestAjaxCalls(BaseTestCase):
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
        """
        Test the ajax call to get the dashboard data with campaigns

        :return:
        :rtype:
        """

        # given
        load_sovtimer()
        self.client.force_login(user=self.user_with_basic_access)
        request = self.factory.get(path=reverse(viewname="sovtimer:dashboard"))
        request.user = self.user_with_basic_access

        # when
        result = dashboard_data(request=request)
        response_data = json.loads(result.content)

        # Check structure and types separately
        self.assertEqual(first=result.status_code, second=HTTPStatus.OK)
        self.assertEqual(len(response_data), 3)

        # Check first campaign has positive remaining time
        self.assertIsInstance(
            response_data[0]["remaining_time_in_seconds"], (int, float)
        )
        self.assertGreater(response_data[0]["remaining_time_in_seconds"], 0)
        self.assertEqual(response_data[0]["campaign_progress"], "60%")

        # Check second campaign (attackers making progress) has negative remaining time (past event)
        self.assertIsInstance(
            response_data[1]["remaining_time_in_seconds"], (int, float)
        )
        self.assertLess(response_data[1]["remaining_time_in_seconds"], 0)
        self.assertIn(
            '13%<i class="material-icons aa-sovtimer-trend aa-sovtimer-trend-down" title="Attackers making progress" data-bs-tooltip="aa-sovtimer">trending_down</i>04%',
            response_data[1]["campaign_progress"],
        )

        # Check third campaign has (defenders making progress) negative remaining time (past event)
        self.assertIsInstance(
            response_data[2]["remaining_time_in_seconds"], (int, float)
        )
        self.assertLess(response_data[2]["remaining_time_in_seconds"], 0)
        self.assertIn(
            '04%<i class="material-icons aa-sovtimer-trend aa-sovtimer-trend-up" title="Defenders making progress" data-bs-tooltip="aa-sovtimer">trending_up</i>13%',
            response_data[2]["campaign_progress"],
        )

        # Check other fields remain exact
        expected_fields = {
            "event_type": "TCU defense",
            "solar_system_name": "0-O6XF",
            "defender_name": "Wayne Enterprises",
            "adm": 6.0,
        }

        for field, value in expected_fields.items():
            self.assertEqual(response_data[0][field], value)
            self.assertEqual(response_data[1][field], value)
            self.assertEqual(response_data[2][field], value)
