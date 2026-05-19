# Standard Library
from unittest.mock import MagicMock, patch

# Third Party
from eve_sde.models import SolarSystem

# AA Sovereignty Timer
from sovtimer.constants import Constants
from sovtimer.models import Alliance
from sovtimer.tasks import (
    run_sov_campaign_updates,
    update_sov_campaigns,
    update_sov_structures,
)
from sovtimer.tests import BaseTestCase


class TestUpdateSovStructures(BaseTestCase):
    """
    Test the update_sov_structures task
    """

    @patch("sovtimer.tasks.cache.get")
    @patch("sovtimer.tasks.cache.set")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.tasks.SolarSystem.objects.filter")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    def test_returns_early_and_makes_no_db_calls_when_esi_returns_none(
        self,
        mock_get_sov_structures,
        mock_bulk_get_or_create,
        mock_solar_system_filter,
        mock_exclude,
        mock_bulk_create,
        mock_cache_set,
        mock_cache_get,
    ):
        """
        Test returns early and makes no db calls.

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_cache_get:
        :type mock_cache_get:
        :return:
        :rtype:
        """

        mock_cache_get.return_value = False
        mock_cache_set.return_value = None

        mock_get_sov_structures.return_value = None

        result = update_sov_structures(force_refresh=False)

        self.assertIsNone(result)
        mock_cache_get.assert_called_once_with(Constants.TASK_STRUCTURE_CACHE_KEY)
        mock_get_sov_structures.assert_called_once_with(
            use_etags=True, force_refresh=False
        )
        mock_bulk_get_or_create.assert_not_called()
        mock_solar_system_filter.assert_not_called()
        mock_bulk_create.assert_not_called()
        mock_exclude.assert_not_called()

    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    @patch("sovtimer.tasks.cache.get")
    def test_skips_update_when_cache_not_expired(
        self, mock_cache_get, mock_get_sov_structures
    ):
        mock_cache_get.return_value = True

        update_sov_structures(force_refresh=False)

        mock_cache_get.assert_called_once_with(Constants.TASK_STRUCTURE_CACHE_KEY)
        mock_get_sov_structures.assert_not_called()

    @patch("sovtimer.tasks.cache.get")
    @patch("sovtimer.tasks.cache.set")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.tasks.SolarSystem.objects.filter")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    def test_processes_structure_with_default_vulnerability(
        self,
        mock_get_sov_structures,
        mock_bulk_get_or_create,
        mock_solar_system_filter,
        mock_exclude,
        mock_bulk_create,
        mock_cache_set,
        mock_cache_get,
    ):
        """
        Test processes structure with default vulnerability.

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_cache_get:
        :type mock_cache_get:
        :return:
        :rtype:
        """

        mock_cache_get.return_value = False
        mock_cache_set.return_value = None

        mock_get_sov_structures.return_value = [
            {
                "solar_system_id": 3001,
                "alliance_id": 2001,
                "sovereignty_hub": {
                    "id": 1001,
                    "vulnerability_window": {
                        "start": "2023-01-01T12:00:00Z",
                        "end": "2023-01-01T18:00:00Z",
                    },
                },
                "development": {"activity_defense_multiplier": None},
            }
        ]

        mock_bulk_get_or_create.return_value = {
            2001: Alliance(alliance_id=2001, name="Alliance 2001")
        }
        mock_solar_system_filter.return_value = [SolarSystem(id=3001)]
        mock_bulk_create.return_value = None
        mock_exclude.return_value.delete = MagicMock()

        update_sov_structures(force_refresh=False)

        mock_cache_get.assert_called_once_with(Constants.TASK_STRUCTURE_CACHE_KEY)
        mock_get_sov_structures.assert_called_once()
        mock_bulk_get_or_create.assert_called_once_with(
            alliance_ids={2001}, force_refresh=False
        )
        mock_solar_system_filter.assert_called_once_with(id__in={3001})
        mock_bulk_create.assert_called_once()
        created = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].structure_id, 1001)
        self.assertEqual(created[0].vulnerability_occupancy_level, 1)

    @patch("sovtimer.tasks.cache.get")
    @patch("sovtimer.tasks.cache.set")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.tasks.SolarSystem.objects.filter")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    def test_skips_structure_if_hub_id_missing(
        self,
        mock_get_sov_structures,
        mock_bulk_get_or_create,
        mock_solar_system_filter,
        mock_exclude,
        mock_bulk_create,
        mock_cache_set,
        mock_cache_get,
    ):
        """
        Test skips structure if hub_id is missing.

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_cache_get:
        :type mock_cache_get:
        :return:
        :rtype:
        """

        mock_cache_get.return_value = False
        mock_cache_set.return_value = None

        # first structure missing sovereignty_hub id, second is valid
        mock_get_sov_structures.return_value = [
            {
                "solar_system_id": 3001,
                "alliance_id": 2001,
                "sovereignty_hub": {"id": None},
            },
            {
                "solar_system_id": 3002,
                "alliance_id": 2002,
                "sovereignty_hub": {"id": 1002},
                "development": {"activity_defense_multiplier": 0.5},
            },
        ]

        mock_bulk_get_or_create.return_value = {
            2002: Alliance(alliance_id=2002, name="Alliance 2002")
        }
        mock_solar_system_filter.return_value = [SolarSystem(id=3002)]
        mock_bulk_create.return_value = None
        mock_exclude.return_value.delete = MagicMock()

        update_sov_structures(force_refresh=False)

        # only the valid structure should be created
        mock_bulk_create.assert_called_once()
        created = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].structure_id, 1002)

    @patch("sovtimer.tasks.cache.get")
    @patch("sovtimer.tasks.cache.set")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.tasks.SolarSystem.objects.filter")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    def test_skips_duplicate_structure_ids(
        self,
        mock_get_sov_structures,
        mock_bulk_get_or_create,
        mock_solar_system_filter,
        mock_exclude,
        mock_bulk_create,
        mock_cache_set,
        mock_cache_get,
    ):
        """
        Test skips duplicate structure IDs.

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_cache_get:
        :type mock_cache_get:
        :return:
        :rtype:
        """

        mock_cache_get.return_value = False
        mock_cache_set.return_value = None

        # two structures with same sovereignty_hub id -> second should be skipped
        mock_get_sov_structures.return_value = [
            {
                "solar_system_id": 3003,
                "alliance_id": 2003,
                "sovereignty_hub": {"id": 1003},
                "development": {"activity_defense_multiplier": 0.7},
            },
            {
                "solar_system_id": 3004,
                "alliance_id": 2003,
                "sovereignty_hub": {"id": 1003},
                "development": {"activity_defense_multiplier": 0.9},
            },
        ]

        mock_bulk_get_or_create.return_value = {
            2003: Alliance(alliance_id=2003, name="Alliance 2003")
        }
        mock_solar_system_filter.return_value = [
            SolarSystem(id=3003),
            SolarSystem(id=3004),
        ]
        mock_bulk_create.return_value = None
        mock_exclude.return_value.delete = MagicMock()

        update_sov_structures(force_refresh=False)

        # only one structure should be created due to duplicate id
        mock_bulk_create.assert_called_once()
        created = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].structure_id, 1003)

    @patch("sovtimer.tasks.cache.get")
    @patch("sovtimer.tasks.cache.set")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.tasks.SolarSystem.objects.filter")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    def test_development_getitem_raises_attribute_error_defaults_to_one(
        self,
        mock_get_sov_structures,
        mock_bulk_get_or_create,
        mock_solar_system_filter,
        mock_exclude,
        mock_bulk_create,
        mock_cache_set,
        mock_cache_get,
    ):
        """
        Test ADM is missing and defaults to 1.

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_cache_get:
        :type mock_cache_get:
        :return:
        :rtype:
        """

        mock_cache_get.return_value = False
        mock_cache_set.return_value = None

        class DevRaiser:
            def __getitem__(self, key):
                raise AttributeError("simulated attribute error")

        mock_get_sov_structures.return_value = [
            {
                "solar_system_id": 3020,
                "alliance_id": 2020,
                "sovereignty_hub": {"id": 1200},
                "development": DevRaiser(),
            }
        ]

        mock_bulk_get_or_create.return_value = {
            2020: Alliance(alliance_id=2020, name="A2020")
        }
        mock_solar_system_filter.return_value = [SolarSystem(id=3020)]
        mock_bulk_create.return_value = None
        mock_exclude.return_value.delete = MagicMock()

        update_sov_structures(force_refresh=False)

        mock_bulk_create.assert_called_once()
        created = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].vulnerability_occupancy_level, 1)

    @patch("sovtimer.tasks.cache.get")
    @patch("sovtimer.tasks.cache.set")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.tasks.SolarSystem.objects.filter")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    def test_development_multiplier_value_is_used_when_present(
        self,
        mock_get_sov_structures,
        mock_bulk_get_or_create,
        mock_solar_system_filter,
        mock_exclude,
        mock_bulk_create,
        mock_cache_set,
        mock_cache_get,
    ):
        """
        Test ADM is used when present.

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_cache_get:
        :type mock_cache_get:
        :return:
        :rtype:
        """

        mock_cache_get.return_value = False
        mock_cache_set.return_value = None

        mock_get_sov_structures.return_value = [
            {
                "solar_system_id": 3021,
                "alliance_id": 2021,
                "sovereignty_hub": {"id": 1201},
                "development": {"activity_defense_multiplier": 0.33},
            }
        ]

        mock_bulk_get_or_create.return_value = {
            2021: Alliance(alliance_id=2021, name="A2021")
        }
        mock_solar_system_filter.return_value = [SolarSystem(id=3021)]
        mock_bulk_create.return_value = None
        mock_exclude.return_value.delete = MagicMock()

        update_sov_structures(force_refresh=False)

        mock_bulk_create.assert_called_once()
        created = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].vulnerability_occupancy_level, 0.33)

    @patch("sovtimer.tasks.cache.get")
    @patch("sovtimer.tasks.cache.set")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.bulk_create")
    @patch("sovtimer.tasks.SovereigntyStructure.objects.exclude")
    @patch("sovtimer.tasks.SolarSystem.objects.filter")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.tasks.SovereigntyStructure.get_sov_structures_from_esi")
    def test_sovereignty_hub_not_dict_results_in_no_vulnerability_window(
        self,
        mock_get_sov_structures,
        mock_bulk_get_or_create,
        mock_solar_system_filter,
        mock_exclude,
        mock_bulk_create,
        mock_cache_set,
        mock_cache_get,
    ):
        """
        Test sovereignty_hub is not dict results in no vulnerability_window being set.

        :param mock_get_sov_structures:
        :type mock_get_sov_structures:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_solar_system_filter:
        :type mock_solar_system_filter:
        :param mock_exclude:
        :type mock_exclude:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_cache_set:
        :type mock_cache_set:
        :param mock_cache_get:
        :type mock_cache_get:
        :return:
        :rtype:
        """

        mock_cache_get.return_value = False
        mock_cache_set.return_value = None

        class HubLike:
            def __getitem__(self, key):
                if key == "id":
                    return 3040
                raise KeyError(key)

        # sovereignty_hub is subscriptable but not a dict -> isinstance(sov_hub, dict) is False
        mock_get_sov_structures.return_value = [
            {
                "solar_system_id": 3040,
                "alliance_id": 2040,
                "sovereignty_hub": HubLike(),
                "development": {"activity_defense_multiplier": 0.55},
            }
        ]

        mock_bulk_get_or_create.return_value = {
            2040: Alliance(alliance_id=2040, name="A2040")
        }
        mock_solar_system_filter.return_value = [SolarSystem(id=3040)]
        mock_bulk_create.return_value = None
        mock_exclude.return_value.delete = MagicMock()

        update_sov_structures(force_refresh=False)

        mock_bulk_create.assert_called_once()
        created = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(created), 1)
        self.assertIsNone(created[0].vulnerable_start_time)
        self.assertIsNone(created[0].vulnerable_end_time)


class TestUpdateSovCampaigns(BaseTestCase):
    """
    Test the update_sov_campaigns task
    """

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.bulk_create")
    @patch("sovtimer.tasks.Campaign.objects.all")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    def test_progress_previous_uses_previous_progress_when_scores_equal(
        self,
        mock_bulk_get_or_create,
        mock_campaign_all,
        mock_bulk_create,
        mock_get_sov_campaigns,
    ):
        """
        Test that the progress function is called when scores are equal.

        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_campaign_all:
        :type mock_campaign_all:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.return_value = [
            MagicMock(
                campaign_id=1001,
                defender_id=2001,
                attackers_score=0.3,
                defender_score=0.7,
                event_type="type1",
                start_time="2023-01-01T12:00:00Z",
                structure_id=3001,
            )
        ]

        existing = MagicMock(
            campaign_id=1001, defender_score=0.7, progress_previous=0.55
        )
        existing_qs = MagicMock()
        existing_qs.__iter__.return_value = iter([existing])
        existing_qs.delete = MagicMock()
        mock_campaign_all.return_value = existing_qs

        mock_bulk_get_or_create.return_value = {2001: MagicMock()}
        mock_bulk_create.return_value = None

        update_sov_campaigns(force_refresh=False)

        mock_bulk_create.assert_called_once()
        created = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].progress_previous, 0.55)

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.bulk_create")
    @patch("sovtimer.tasks.Campaign.objects.all")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    def test_progress_previous_uses_previous_defender_score_when_scores_differ(
        self,
        mock_bulk_get_or_create,
        mock_campaign_all,
        mock_bulk_create,
        mock_get_sov_campaigns,
    ):
        """
        Test that the progress function is called when scores are different.

        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_campaign_all:
        :type mock_campaign_all:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.return_value = [
            MagicMock(
                campaign_id=1002,
                defender_id=2002,
                attackers_score=0.2,
                defender_score=0.8,
                event_type="type1",
                start_time="2023-01-02T12:00:00Z",
                structure_id=3002,
            )
        ]

        existing = MagicMock(
            campaign_id=1002, defender_score=0.75, progress_previous=0.4
        )
        existing_qs = MagicMock()
        existing_qs.__iter__.return_value = iter([existing])
        existing_qs.delete = MagicMock()
        mock_campaign_all.return_value = existing_qs

        mock_bulk_get_or_create.return_value = {2002: MagicMock()}
        mock_bulk_create.return_value = None

        update_sov_campaigns(force_refresh=False)

        mock_bulk_create.assert_called_once()
        created = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(created), 1)
        # progress_previous should equal the existing defender_score (0.75)
        self.assertEqual(created[0].progress_previous, 0.75)

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.bulk_create")
    @patch("sovtimer.tasks.Campaign.objects.all")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    def test_progress_previous_defaults_to_campaign_defender_score_when_no_previous(
        self,
        mock_bulk_get_or_create,
        mock_campaign_all,
        mock_bulk_create,
        mock_get_sov_campaigns,
    ):
        """
        Test progress_previous defaults to the campaign defender score when no previous progress.

        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_campaign_all:
        :type mock_campaign_all:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.return_value = [
            MagicMock(
                campaign_id=1003,
                defender_id=2003,
                attackers_score=0.1,
                defender_score=0.65,
                event_type="type1",
                start_time="2023-01-03T12:00:00Z",
                structure_id=3003,
            )
        ]

        empty_qs = MagicMock()
        empty_qs.__iter__.return_value = iter([])
        empty_qs.delete = MagicMock()
        mock_campaign_all.return_value = empty_qs

        mock_bulk_get_or_create.return_value = {2003: MagicMock()}
        mock_bulk_create.return_value = None

        update_sov_campaigns(force_refresh=False)

        mock_bulk_create.assert_called_once()
        created = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].progress_previous, 0.65)

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.bulk_create")
    @patch("sovtimer.tasks.Campaign.objects.all")
    def test_returns_early_and_makes_no_db_calls_when_esi_returns_none(
        self,
        mock_campaign_all,
        mock_bulk_create,
        mock_bulk_get_or_create,
        mock_get_sov_campaigns,
    ):
        """
        Test returns early and makes no db calls when ESI returns None.

        :param mock_campaign_all:
        :type mock_campaign_all:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.return_value = None

        result = update_sov_campaigns(force_refresh=False)

        # Function should return None and not attempt any DB/cache operations
        self.assertIsNone(result)
        mock_get_sov_campaigns.assert_called_once_with(
            use_etags=True, force_refresh=False
        )
        mock_bulk_get_or_create.assert_not_called()
        mock_campaign_all.assert_not_called()
        mock_bulk_create.assert_not_called()

    @patch("sovtimer.tasks.Campaign.get_sov_campaigns_from_esi")
    @patch("sovtimer.tasks.Alliance.bulk_get_or_create_from_esi")
    @patch("sovtimer.tasks.Campaign.objects.bulk_create")
    @patch("sovtimer.tasks.Campaign.objects.all")
    def test_handles_empty_list_from_esi_and_performs_empty_bulk_create(
        self,
        mock_campaign_all,
        mock_bulk_create,
        mock_bulk_get_or_create,
        mock_get_sov_campaigns,
    ):
        """
        Test handles empty list from ESI and performs bulk create.

        :param mock_campaign_all:
        :type mock_campaign_all:
        :param mock_bulk_create:
        :type mock_bulk_create:
        :param mock_bulk_get_or_create:
        :type mock_bulk_get_or_create:
        :param mock_get_sov_campaigns:
        :type mock_get_sov_campaigns:
        :return:
        :rtype:
        """

        mock_get_sov_campaigns.return_value = []
        empty_qs = MagicMock()
        empty_qs.__iter__.return_value = iter([])
        empty_qs.delete = MagicMock()
        mock_campaign_all.return_value = empty_qs
        mock_bulk_get_or_create.return_value = {}

        update_sov_campaigns(force_refresh=False)

        mock_get_sov_campaigns.assert_called_once_with(
            use_etags=True, force_refresh=False
        )
        mock_bulk_get_or_create.assert_called_once_with(
            alliance_ids=set(), force_refresh=False
        )
        # Campaign.objects.all() is invoked once to read existing campaigns and
        # once to delete them, so expect two calls.
        self.assertEqual(mock_campaign_all.call_count, 2)
        # bulk_create should be called with an empty list
        mock_bulk_create.assert_called_once()
        created_arg = mock_bulk_create.call_args[0][0]
        self.assertIsInstance(created_arg, list)
        self.assertEqual(len(created_arg), 0)


class TestRunSovCampaignUpdates(BaseTestCase):
    """
    Test the run_sov_campaign_updates task
    """

    @patch("sovtimer.tasks.chain")
    @patch("sovtimer.tasks.update_sov_structures.si")
    @patch("sovtimer.tasks.update_sov_campaigns.si")
    def test_runs_both_tasks_in_sequence(
        self, mock_update_campaigns, mock_update_structures, mock_chain
    ):
        """
        Test that the task runs both update tasks in sequence with the correct priority

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :param mock_chain:
        :type mock_chain:
        :return:
        :rtype:
        """

        run_sov_campaign_updates()

        mock_update_structures.assert_called_once_with(
            use_etags=True, force_refresh=False
        )
        mock_update_campaigns.assert_called_once_with(
            use_etags=True, force_refresh=False
        )
        mock_update_structures.return_value.set.assert_called_once_with(priority=6)
        mock_update_campaigns.return_value.set.assert_called_once_with(priority=6)
        mock_chain.return_value.apply_async.assert_called_once()

    @patch("sovtimer.tasks.chain")
    @patch("sovtimer.tasks.update_sov_structures.si")
    @patch("sovtimer.tasks.update_sov_campaigns.si")
    def test_handles_no_priority_set(
        self, mock_update_campaigns, mock_update_structures, mock_chain
    ):
        """
        Test that the task runs both update tasks in sequence even if no priority is set

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :param mock_chain:
        :type mock_chain:
        :return:
        :rtype:
        """

        run_sov_campaign_updates()

        mock_update_structures.return_value.set.assert_called_once_with(priority=6)
        mock_update_campaigns.return_value.set.assert_called_once_with(priority=6)
        mock_chain.return_value.apply_async.assert_called_once()

    @patch("sovtimer.tasks.logger.info")
    @patch("sovtimer.tasks.chain")
    @patch("sovtimer.tasks.update_sov_structures.si")
    @patch("sovtimer.tasks.update_sov_campaigns.si")
    def test_logs_start_of_update_process(
        self,
        mock_update_campaigns,
        mock_update_structures,
        mock_chain,
        mock_logger_info,
    ):
        """
        Test that the task logs the start of the update process

        :param mock_update_campaigns:
        :type mock_update_campaigns:
        :param mock_update_structures:
        :type mock_update_structures:
        :param mock_chain:
        :type mock_chain:
        :param mock_logger_info:
        :type mock_logger_info:
        :return:
        :rtype:
        """

        run_sov_campaign_updates()

        mock_logger_info.assert_called_once_with(
            msg="Updating sovereignty structures and campaigns from ESI…"
        )
        mock_chain.return_value.apply_async.assert_called_once()
