"""
Unit tests for the models in sovtimer
"""

# Standard Library
import importlib
import sys
import types
import typing
from unittest.mock import MagicMock, patch

# AA Sovereignty Timer
from sovtimer.models import Alliance, Campaign, SovereigntyStructure, logger
from sovtimer.tests import BaseTestCase


class TypeCheckingImportBehavior(BaseTestCase):
    """
    Test the TYPE_CHECKING import behavior in sovtimer.models to ensure that type
    checking symbols are only imported when TYPE_CHECKING is True
    """

    def test_imports_type_checking_symbols_when_flag_is_true(self):
        """
        Test imports TYPE_CHECKING symbols when flag is true

        :return:
        :rtype:
        """

        # Preserve any existing modules to restore later
        orig_httpx = sys.modules.get("httpx")
        orig_esi = sys.modules.get("esi")
        orig_esi_stubs = sys.modules.get("esi.stubs")

        # Inject placeholder modules so the imports inside TYPE_CHECKING succeed
        sys.modules["httpx"] = types.ModuleType("httpx")
        sys.modules["esi"] = types.ModuleType("esi")
        sys.modules["esi.stubs"] = types.ModuleType("esi.stubs")
        sys.modules["httpx"].Response = object()
        sys.modules["esi.stubs"].SovereigntyCampaignsGetItem = object()

        with patch.object(typing, "TYPE_CHECKING", True):
            models = importlib.reload(importlib.import_module("sovtimer.models"))

            self.assertIn("Response", models.__dict__)
            self.assertIn("SovereigntyCampaignsGetItem", models.__dict__)
            self.assertIs(models.__dict__["Response"], sys.modules["httpx"].Response)
            self.assertIs(
                models.__dict__["SovereigntyCampaignsGetItem"],
                sys.modules["esi.stubs"].SovereigntyCampaignsGetItem,
            )

        # Restore original modules and reload the module to leave global state unchanged
        if orig_httpx is None:
            del sys.modules["httpx"]
        else:
            sys.modules["httpx"] = orig_httpx

        if orig_esi_stubs is None:
            del sys.modules["esi.stubs"]
        else:
            sys.modules["esi.stubs"] = orig_esi_stubs

        if orig_esi is None:
            del sys.modules["esi"]
        else:
            sys.modules["esi"] = orig_esi

        importlib.reload(importlib.import_module("sovtimer.models"))

    def test_does_not_import_type_checking_symbols_when_flag_is_false(self):
        """
        Test does not import TYPE_CHECKING symbols when flag is false

        :return:
        :rtype:
        """

        # Preserve any existing modules to restore later
        orig_httpx = sys.modules.get("httpx")
        orig_esi = sys.modules.get("esi")
        orig_esi_stubs = sys.modules.get("esi.stubs")

        # Inject placeholder modules so imports would succeed if executed
        sys.modules["httpx"] = types.ModuleType("httpx")
        sys.modules["esi"] = types.ModuleType("esi")
        sys.modules["esi.stubs"] = types.ModuleType("esi.stubs")
        sys.modules["httpx"].Response = object()
        sys.modules["esi.stubs"].SovereigntyCampaignsGetItem = object()

        with patch.object(typing, "TYPE_CHECKING", False):
            models = importlib.reload(importlib.import_module("sovtimer.models"))

            self.assertNotIn("Response", models.__dict__)
            self.assertNotIn("SovereigntyCampaignsGetItem", models.__dict__)

        # Restore original modules and reload the module to leave global state unchanged
        if orig_httpx is None:
            del sys.modules["httpx"]
        else:
            sys.modules["httpx"] = orig_httpx

        if orig_esi_stubs is None:
            del sys.modules["esi.stubs"]
        else:
            sys.modules["esi.stubs"] = orig_esi_stubs

        if orig_esi is None:
            del sys.modules["esi"]
        else:
            sys.modules["esi"] = orig_esi

        importlib.reload(importlib.import_module("sovtimer.models"))


class TestAlliance(BaseTestCase):
    """
    Test cases for the Alliance model
    """

    @patch("sovtimer.models.ESIHandler.get_alliances_alliance_id")
    @patch("sovtimer.models.Alliance.objects.bulk_create")
    @patch("sovtimer.models.Alliance.objects.filter")
    def test_returns_all_alliances_when_all_ids_exist(
        self, mock_filter, mock_bulk_create, mock_get_alliance
    ):
        """
        Test that all alliances are returned when all IDs exist in the database

        :param mock_filter:
        :type mock_filter:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_alliance:
        :type mock_get_alliance:
        :return:
        :rtype:
        """

        mock_existing_alliances = [
            Alliance(alliance_id=1, name="Alliance 1"),
            Alliance(alliance_id=2, name="Alliance 2"),
        ]
        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = iter(mock_existing_alliances)
        mock_qs.values_list.return_value = [1, 2]
        mock_filter.return_value = mock_qs

        result = Alliance.bulk_get_or_create_from_esi(
            alliance_ids={1, 2}, force_refresh=False
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[1].name, "Alliance 1")
        self.assertEqual(result[2].name, "Alliance 2")
        mock_filter.assert_called_once_with(alliance_id__in={1, 2})
        mock_bulk_create.assert_not_called()
        mock_get_alliance.assert_not_called()

    @patch("sovtimer.models.ESIHandler.get_alliances_alliance_id")
    @patch("sovtimer.models.Alliance.objects.bulk_create")
    @patch("sovtimer.models.Alliance.objects.filter")
    def test_creates_new_alliances_when_some_ids_do_not_exist(
        self, mock_filter, mock_bulk_create, mock_get_alliance
    ):
        """
        Test that new alliances are created when some IDs do not exist in the database

        :param mock_filter:
        :type mock_filter:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_alliance:
        :type mock_get_alliance:
        :return:
        :rtype:
        """

        mock_existing_alliances = [
            Alliance(alliance_id=1, name="Alliance 1"),
        ]
        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = iter(mock_existing_alliances)
        mock_qs.values_list.return_value = [1]
        mock_filter.return_value = mock_qs

        a2 = MagicMock()
        a2.name = "Alliance 2"
        a3 = MagicMock()
        a3.name = "Alliance 3"
        mock_get_alliance.side_effect = [a2, a3]

        mock_bulk_create.return_value = [
            Alliance(alliance_id=2, name="Alliance 2"),
            Alliance(alliance_id=3, name="Alliance 3"),
        ]

        result = Alliance.bulk_get_or_create_from_esi(
            alliance_ids={1, 2, 3}, force_refresh=False
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(result[1].name, "Alliance 1")
        self.assertEqual(result[2].name, "Alliance 2")
        self.assertEqual(result[3].name, "Alliance 3")
        mock_filter.assert_called_once_with(alliance_id__in={1, 2, 3})
        mock_get_alliance.assert_any_call(alliance_id=2, force_refresh=False)
        mock_get_alliance.assert_any_call(alliance_id=3, force_refresh=False)
        mock_bulk_create.assert_called_once()

    @patch("sovtimer.models.ESIHandler.get_alliances_alliance_id")
    @patch("sovtimer.models.Alliance.objects.bulk_create")
    @patch("sovtimer.models.Alliance.objects.filter")
    def test_skips_creation_when_esi_returns_no_data(
        self, mock_filter, mock_bulk_create, mock_get_alliance
    ):
        """
        Test that creation is skipped when ESI returns no data for an alliance ID

        :param mock_filter:
        :type mock_filter:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_alliance:
        :type mock_get_alliance:
        :return:
        :rtype:
        """

        mock_qs = MagicMock()
        mock_qs.__iter__.return_value = iter([])
        mock_qs.values_list.return_value = []
        mock_filter.return_value = mock_qs
        mock_get_alliance.return_value = None

        result = Alliance.bulk_get_or_create_from_esi(
            alliance_ids={1}, force_refresh=False
        )

        self.assertEqual(len(result), 0)
        mock_filter.assert_called_once_with(alliance_id__in={1})
        mock_get_alliance.assert_called_once_with(alliance_id=1, force_refresh=False)
        mock_bulk_create.assert_not_called()


class TestSovereigntyStructure(BaseTestCase):
    """
    Test cases for the SovereigntyStructure model
    """

    @patch("sovtimer.models.ESIHandler.get_sovereignty_systems")
    def test_returns_none_when_esihandler_returns_none(self, mock_get):
        """
        Test that none is returned when ESI returns None

        :param mock_get:
        :type mock_get:
        :return:
        :rtype:
        """

        mock_get.return_value = None

        result = SovereigntyStructure.get_sov_structures_from_esi(
            use_etags=False, force_refresh=False
        )

        self.assertIsNone(result)
        mock_get.assert_called_once_with(use_etags=False, force_refresh=False)

    @patch("sovtimer.models.ESIHandler.get_sovereignty_systems")
    def test_returns_parsed_structure_list_when_esihandler_returns_data(self, mock_get):
        """
        Test that data is returned when ESI returns parsed data

        :param mock_get:
        :type mock_get:
        :return:
        :rtype:
        """

        sovereignty_hub = MagicMock()
        sovereignty_hub.id = 12345
        vulnerability_window = MagicMock()
        vulnerability_window.start = "2023-01-01T12:00:00Z"
        vulnerability_window.end = "2023-01-01T18:00:00Z"
        sovereignty_hub.vulnerability_window = vulnerability_window

        development = MagicMock()
        development.activity_defense_multiplier = 0.5
        development.military_level = 1
        development.industrial_level = 2
        development.strategic_level = 3

        claim_obj = MagicMock()
        claim_obj.alliance_id = 2001
        claim_obj.corporation_id = 4001
        claim_obj.claimed_since = "2023-01-01T00:00:00Z"
        claim_obj.sovereignty_hub = sovereignty_hub
        claim_obj.is_capital_system = True
        claim_obj.development = development

        root = MagicMock()
        root.alliance = claim_obj

        sov_system = MagicMock()
        sov_system.solar_system_id = 3001
        sov_system.claim = MagicMock(root=root)

        mock_get.return_value = MagicMock(solar_systems=[sov_system])

        result = SovereigntyStructure.get_sov_structures_from_esi(
            use_etags=True, force_refresh=True
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        structure = result[0]
        self.assertIn("solar_system_id", structure)
        self.assertIn("alliance_id", structure)
        self.assertIn("sovereignty_hub", structure)
        self.assertEqual(structure["solar_system_id"], 3001)
        self.assertEqual(structure["alliance_id"], 2001)
        self.assertEqual(structure["sovereignty_hub"]["id"], 12345)
        self.assertIn("vulnerability_window", structure["sovereignty_hub"])
        self.assertEqual(structure["development"]["activity_defense_multiplier"], 0.5)
        mock_get.assert_called_once_with(use_etags=True, force_refresh=True)

    @patch("sovtimer.models.ESIHandler.get_sovereignty_systems")
    def test_skips_systems_without_alliance_and_continues_processing_others(
        self, mock_get
    ):
        """
        Test skips system without alliance and continues processing

        :param mock_get:
        :type mock_get:
        :return:
        :rtype:
        """

        class BadClaim:
            """
            Bad Claim
            """

            @property
            def root(self):
                """
                Raise AttributeError

                :return:
                :rtype:
                """

                raise AttributeError

        bad_system = MagicMock()
        bad_system.solar_system_id = 1111
        bad_system.claim = BadClaim()

        sovereignty_hub = MagicMock()
        sovereignty_hub.id = 22222
        sovereignty_hub.vulnerability_window = None

        development = MagicMock()
        development.activity_defense_multiplier = None
        development.military_level = 0
        development.industrial_level = 0
        development.strategic_level = 0

        claim_obj = MagicMock()
        claim_obj.alliance_id = 3001
        claim_obj.corporation_id = 5001
        claim_obj.claimed_since = None
        claim_obj.sovereignty_hub = sovereignty_hub
        claim_obj.is_capital_system = False
        claim_obj.development = development

        root = MagicMock()
        root.alliance = claim_obj

        good_system = MagicMock()
        good_system.solar_system_id = 4001
        good_system.claim = MagicMock(root=root)

        mock_get.return_value = MagicMock(solar_systems=[bad_system, good_system])

        result = SovereigntyStructure.get_sov_structures_from_esi()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["solar_system_id"], 4001)
        mock_get.assert_called_once_with(use_etags=True, force_refresh=False)

    @patch("sovtimer.models.ESIHandler.get_sovereignty_systems")
    def test_skips_system_when_development_raises_attribute_error(self, mock_get):
        """
        Test skips system when system development is raises AttributeError and continues processing others

        :param mock_get:
        :type mock_get:
        :return:
        :rtype:
        """

        sovereignty_hub = MagicMock()
        sovereignty_hub.id = 99999
        claim_obj = MagicMock()
        claim_obj.alliance_id = 7001
        claim_obj.corporation_id = 8001
        claim_obj.claimed_since = None
        claim_obj.sovereignty_hub = sovereignty_hub
        claim_obj.is_capital_system = False

        class BadDevelopment:
            """
            Bad Development
            """

            @property
            def activity_defense_multiplier(self):
                """
                Raise AttributeError

                :return:
                :rtype:
                """

                raise AttributeError

            @property
            def military_level(self):
                """
                Raise AttributeError

                :return:
                :rtype:
                """

                raise AttributeError

            @property
            def industrial_level(self):
                """
                Raise AttributeError

                :return:
                :rtype:
                """

                raise AttributeError

            @property
            def strategic_level(self):
                """
                Raise AttributeError

                :return:
                :rtype:
                """

                raise AttributeError

        claim_obj.development = BadDevelopment()

        root = MagicMock()
        root.alliance = claim_obj

        bad_system = MagicMock()
        bad_system.solar_system_id = 7777
        bad_system.claim = MagicMock(root=root)

        mock_get.return_value = MagicMock(solar_systems=[bad_system])

        result = SovereigntyStructure.get_sov_structures_from_esi()

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        mock_get.assert_called_once_with(use_etags=True, force_refresh=False)

    @patch("sovtimer.models.ESIHandler.get_sovereignty_systems")
    def test_handles_system_with_no_alliance_field_gracefully(self, mock_get):
        """
        Test handles system with no alliance field gracefully

        :param mock_get:
        :type mock_get:
        :return:
        :rtype:
        """
        # sov_system.claim.root.alliance is None -> should be skipped and result empty list
        root = MagicMock()
        root.alliance = None

        sov_system = MagicMock()
        sov_system.solar_system_id = 1010
        sov_system.claim = MagicMock(root=root)

        mock_get.return_value = MagicMock(solar_systems=[sov_system])

        result = SovereigntyStructure.get_sov_structures_from_esi(
            use_etags=True, force_refresh=True
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)
        mock_get.assert_called_once_with(use_etags=True, force_refresh=True)


class TestCampaign(BaseTestCase):
    """
    Test cases for the Campaign model
    """

    @patch("sovtimer.models.ESIHandler.get_sovereignty_campaigns")
    def test_returns_campaigns_when_esi_returns_data(self, mock_get_campaigns):
        """
        Test that campaigns are returned when ESI returns data

        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = [
            {
                "campaign_id": 5001,
                "attackers_score": 0.3,
                "defender_score": 0.7,
                "event_type": "sovhub",
                "start_time": "2023-01-01T12:00:00Z",
                "structure_id": 1001,
            }
        ]

        result = Campaign.get_sov_campaigns_from_esi(force_refresh=False)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["campaign_id"], 5001)
        mock_get_campaigns.assert_called_once_with(
            use_etags=True, force_refresh=False, return_response=False
        )

    @patch("sovtimer.models.ESIHandler.get_sovereignty_campaigns")
    def test_returns_empty_list_when_esi_returns_no_data(self, mock_get_campaigns):
        """
        Test that an empty list is returned when ESI returns no data for campaigns

        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = []

        result = Campaign.get_sov_campaigns_from_esi(force_refresh=False)

        self.assertEqual(len(result), 0)
        mock_get_campaigns.assert_called_once_with(
            use_etags=True, force_refresh=False, return_response=False
        )

    @patch("sovtimer.models.ESIHandler.get_sovereignty_campaigns")
    def test_logs_info_when_esi_returns_no_data(self, mock_get_campaigns):
        """
        Test that an info log is generated when ESI returns no data for campaigns

        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = []

        with self.assertLogs(logger.logger, level="INFO") as log:
            Campaign.get_sov_campaigns_from_esi(force_refresh=False)

        self.assertIn("No campaign changes found, nothing to update.", log.output[0])

    @patch("sovtimer.models.ESIHandler.get_sovereignty_campaigns")
    def test_logs_debug_when_esi_returns_data(self, mock_get_campaigns):
        """
        Test that a debug log is generated when ESI returns data for campaigns

        :param mock_get_campaigns:
        :type mock_get_campaigns:
        :return:
        :rtype:
        """

        mock_get_campaigns.return_value = [
            {
                "campaign_id": 5001,
                "attackers_score": 0.3,
                "defender_score": 0.7,
                "event_type": "sovhub",
                "start_time": "2023-01-01T12:00:00Z",
                "structure_id": 1001,
            }
        ]

        with self.assertLogs(logger.logger, level="DEBUG") as log:
            Campaign.get_sov_campaigns_from_esi(force_refresh=False)

        self.assertIn("Fetched 1 campaigns from ESI", log.output[0])
