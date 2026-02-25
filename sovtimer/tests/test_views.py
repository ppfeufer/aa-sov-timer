"""
Unit tests for sovtimer views
"""

# Standard Library
from datetime import datetime
from datetime import timezone as dt_timezone
from http import HTTPStatus
from unittest.mock import MagicMock, patch

# Django
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.timezone import now

# AA Sovereignty Timer
from sovtimer.tests import BaseTestCase
from sovtimer.views import _fmt_float_to_percentage


class TestHelperFmtFloatToPercentage(BaseTestCase):
    """
    Test the _fmt_float_to_percentage helper function
    """

    def test_fmt_float_to_percentage(self):
        """
        Test the _fmt_float_to_percentage function

        :return:
        :rtype:
        """

        self.assertEqual(_fmt_float_to_percentage(0.0), "00%")
        self.assertEqual(_fmt_float_to_percentage(0.01), "01%")
        self.assertEqual(_fmt_float_to_percentage(0.1), "10%")
        self.assertEqual(_fmt_float_to_percentage(0.1234), "12%")
        self.assertEqual(_fmt_float_to_percentage(0.5678), "57%")
        self.assertEqual(_fmt_float_to_percentage(1.0), "100%")


class TestDashboard(BaseTestCase):
    """
    Test the dashboard view
    """

    @patch("sovtimer.views.logger")
    def test_dashboard_renders_correct_template(self, mock_logger):
        """
        Test that the dashboard view renders the correct template

        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        User = get_user_model()
        user = User.objects.create_user(username="testuser", password="password")

        self.client.force_login(user)

        response = self.client.get(reverse("sovtimer:dashboard"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "sovtimer/dashboard.html")
        mock_logger.info.assert_called_once_with(msg="Module called by testuser")

    @patch("sovtimer.views.logger")
    def test_dashboard_logs_anonymous_user(self, mock_logger):
        """
        Test that the dashboard view logs AnonymousUser

        :param mock_logger:
        :type mock_logger:
        :return:
        :rtype:
        """

        response = self.client.get(reverse("sovtimer:dashboard"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        mock_logger.info.assert_called_once_with(msg="Module called by AnonymousUser")


class TestDashboardData(BaseTestCase):
    """
    Test the dashboard_data view
    """

    @patch("sovtimer.views.Campaign.objects.select_related")
    def test_returns_empty_response_when_no_campaign_system_ids(
        self, mock_campaign_select_related
    ):
        """
        Test that the dashboard_data view returns an empty response when no campaign system IDs

        :param mock_campaign_select_related:
        :type mock_campaign_select_related:
        :return:
        :rtype:
        """

        qs_mock = MagicMock()
        qs_mock.values_list.return_value = []
        qs_mock.__iter__.return_value = iter([])

        mock_campaign_select_related.return_value.filter.return_value = qs_mock

        response = self.client.get(reverse("sovtimer:dashboard_data"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json(), [])

    @patch("sovtimer.views.Campaign.Type")
    @patch("sovtimer.views.Campaign.objects.select_related")
    @patch("sovtimer.views.SovereigntyStructure.objects.filter")
    def test_dashboard_data_includes_active_campaigns(
        self, mock_structure_filter, mock_campaign_select_related, mock_campaign_type
    ):
        """
        Test that the dashboard_data view includes active campaigns

        :param mock_structure_filter:
        :type mock_structure_filter:
        :param mock_campaign_select_related:
        :type mock_campaign_select_related:
        :param mock_campaign_type:
        :type mock_campaign_type:
        :return:
        :rtype:
        """

        mock_campaign_type.return_value = MagicMock(label="active")

        mock_campaign = MagicMock()
        structure = MagicMock()
        structure.solar_system_id = 1

        alliance = MagicMock()
        alliance.name = "Alliance A"
        alliance.alliance_id = 111
        structure.alliance = alliance

        solar_system = MagicMock()
        solar_system.name = "System A"

        constellation = MagicMock()
        constellation.name = "Constellation A"
        constellation.id = 7002
        region = MagicMock()
        region.name = "Region A"
        region.id = 7001
        constellation.region = region
        solar_system.constellation = constellation
        structure.solar_system = solar_system

        mock_campaign.structure = structure
        mock_campaign.start_time = now()
        mock_campaign.progress_previous = 0.2
        mock_campaign.progress_current = 0.5
        mock_campaign.event_type = 1

        qs_mock = MagicMock()
        qs_mock.__iter__.return_value = iter([mock_campaign])
        qs_mock.values_list.return_value = [1]
        mock_campaign_select_related.return_value.filter.return_value = qs_mock

        mock_structure = MagicMock()
        mock_structure.solar_system_id = 1
        mock_structure.vulnerability_occupancy_level = 1.5
        mock_structure_filter.return_value = [mock_structure]

        response = self.client.get(reverse("sovtimer:dashboard_data"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["solar_system"]["sort"], "System A")
        self.assertEqual(response.json()[0]["defender"]["sort"], "Alliance A")
        self.assertEqual(response.json()[0]["campaign_status"], "active")

    @patch("sovtimer.views.Campaign.Type")
    @patch("sovtimer.views.Campaign.objects.select_related")
    @patch("sovtimer.views.SovereigntyStructure.objects.filter")
    def test_dashboard_data_handles_missing_vulnerability_levels(
        self, mock_structure_filter, mock_campaign_select_related, mock_campaign_type
    ):
        """
        Test that the dashboard_data view handles missing vulnerability levels

        :param mock_structure_filter:
        :type mock_structure_filter:
        :param mock_campaign_select_related:
        :type mock_campaign_select_related:
        :param mock_campaign_type:
        :type mock_campaign_type:
        :return:
        :rtype:
        """

        mock_campaign_type.return_value = MagicMock(label="other")

        mock_campaign = MagicMock()
        structure = MagicMock()
        structure.solar_system_id = 1

        alliance = MagicMock()
        alliance.name = "Alliance B"
        alliance.alliance_id = 222
        structure.alliance = alliance

        solar_system = MagicMock()
        solar_system.name = "System B"

        constellation = MagicMock()
        constellation.name = "Constellation B"
        region = MagicMock()
        region.name = "Region B"
        region.id = 7003
        constellation.region = region
        solar_system.constellation = constellation
        structure.solar_system = solar_system

        mock_campaign.structure = structure
        mock_campaign.start_time = now()
        mock_campaign.progress_previous = 0.3
        mock_campaign.progress_current = 0.3
        mock_campaign.event_type = 2

        qs_mock = MagicMock()
        qs_mock.__iter__.return_value = iter([mock_campaign])
        qs_mock.values_list.return_value = [1]
        mock_campaign_select_related.return_value.filter.return_value = qs_mock

        mock_structure_filter.return_value = []

        response = self.client.get(reverse("sovtimer:dashboard_data"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["adm"], 1)

    @patch("sovtimer.views.Campaign.Type")
    @patch("sovtimer.views.timezone.now")
    @patch("sovtimer.views.Campaign.objects.select_related")
    @patch("sovtimer.views.SovereigntyStructure.objects.filter")
    def test_campaign_status_is_upcoming_when_within_timeframe(
        self,
        mock_structure_filter,
        mock_campaign_select_related,
        mock_now,
        mock_campaign_type,
    ):
        """
        Test that the campaign status is "upcoming" when the current time is within 4 hours of the campaign start time

        :param mock_structure_filter:
        :type mock_structure_filter:
        :param mock_campaign_select_related:
        :type mock_campaign_select_related:
        :param mock_now:
        :type mock_now:
        :param mock_campaign_type:
        :type mock_campaign_type:
        :return:
        :rtype:
        """

        mock_campaign_type.return_value = MagicMock(label="upcoming")
        mock_now.return_value = datetime(2023, 10, 1, 12, 0, tzinfo=dt_timezone.utc)

        mock_campaign = MagicMock()
        mock_campaign.start_time = datetime(2023, 10, 1, 15, 0, tzinfo=dt_timezone.utc)
        mock_campaign.progress_previous = 0.1
        mock_campaign.progress_current = 0.2
        mock_campaign.event_type = 1

        structure = MagicMock()
        structure.solar_system_id = 1

        alliance = MagicMock()
        alliance.name = "Alliance U"
        alliance.alliance_id = 333
        structure.alliance = alliance

        solar_system = MagicMock()
        solar_system.name = "System U"

        constellation = MagicMock()
        constellation.name = "Constellation U"
        constellation.id = 7004
        region = MagicMock()
        region.name = "Region U"
        region.id = 7005
        constellation.region = region
        solar_system.constellation = constellation
        structure.solar_system = solar_system

        mock_campaign.structure = structure

        qs_mock = MagicMock()
        qs_mock.__iter__.return_value = iter([mock_campaign])
        qs_mock.values_list.return_value = [1]
        mock_campaign_select_related.return_value.filter.return_value = qs_mock

        mock_structure = MagicMock()
        mock_structure.solar_system_id = 1
        mock_structure.vulnerability_occupancy_level = 1.5
        mock_structure_filter.return_value = [mock_structure]

        response = self.client.get(reverse("sovtimer:dashboard_data"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["campaign_status"], "upcoming")

    @patch("sovtimer.views.Campaign.Type")
    @patch("sovtimer.views.Campaign.objects.select_related")
    @patch("sovtimer.views.SovereigntyStructure.objects.filter")
    def test_sets_attackers_progress_when_previous_progress_is_higher(
        self, mock_structure_filter, mock_campaign_select_related, mock_campaign_type
    ):
        """
        Test that the dashboard_data view sets "Attackers making progress" when the previous progress is higher than the current progress

        :param mock_structure_filter:
        :type mock_structure_filter:
        :param mock_campaign_select_related:
        :type mock_campaign_select_related:
        :param mock_campaign_type:
        :type mock_campaign_type:
        :return:
        :rtype:
        """

        mock_campaign_type.return_value = MagicMock(label="active")

        mock_campaign = MagicMock()
        mock_campaign.progress_previous = 0.6
        mock_campaign.progress_current = 0.4

        structure = MagicMock()
        structure.solar_system_id = 1

        alliance = MagicMock()
        alliance.name = "Alliance X"
        alliance.alliance_id = 444
        structure.alliance = alliance

        solar_system = MagicMock()
        solar_system.name = "System X"

        constellation = MagicMock()
        constellation.name = "Constellation X"
        region = MagicMock()
        region.name = "Region X"
        region.id = 7006
        constellation.region = region
        solar_system.constellation = constellation
        structure.solar_system = solar_system

        mock_campaign.structure = structure
        mock_campaign.start_time = now()
        mock_campaign.event_type = 1

        qs_mock = MagicMock()
        qs_mock.__iter__.return_value = iter([mock_campaign])
        qs_mock.values_list.return_value = [1]
        mock_campaign_select_related.return_value.filter.return_value = qs_mock

        mock_structure_filter.return_value = []

        response = self.client.get(reverse("sovtimer:dashboard_data"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.json()), 1)
        self.assertIn(
            "Attackers making progress",
            response.json()[0]["campaign_progress"]["display"],
        )
