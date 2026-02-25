"""
Our Models
"""

# Standard Library
from collections.abc import Iterable

# Third Party
from eve_sde.models import SolarSystem

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.providers import AppLogger, ESIHandler

logger = AppLogger(my_logger=get_extension_logger(name=__name__), prefix=__title__)


class AaSovtimer(models.Model):
    """
    Meta model for app permissions
    """

    class Meta:
        """
        Meta definitions
        """

        verbose_name = _("Sovereignty Timer")
        managed = False
        default_permissions = ()
        permissions = (("basic_access", _("Can access the Sovereignty Timer module")),)


class Alliance(models.Model):
    """
    Sovereignty holding alliance
    """

    alliance_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    name = models.CharField(max_length=255)

    class Meta:
        """
        Meta definitions
        """

        verbose_name = _("Alliance")
        verbose_name_plural = _("Alliances")
        default_permissions = ()

    @classmethod
    def bulk_get_or_create_from_esi(
        cls, alliance_ids: Iterable[int], force_refresh: bool = False
    ) -> dict[int, "Alliance"]:
        """
        Bulk get or create alliances from ESI

        :param alliance_ids: List of alliance IDs to fetch or create
        :type alliance_ids: Iterable[int]
        :param force_refresh: Whether to force refresh data from ESI, bypassing any caches
        :type force_refresh: bool
        :return: Dictionary mapping alliance IDs to Alliance instances
        :rtype: dict[int, Alliance]
        """

        existing_alliances = cls.objects.filter(alliance_id__in=alliance_ids)
        existing_alliance_ids = set(
            existing_alliances.values_list("alliance_id", flat=True)
        )
        alliances_to_create = alliance_ids - existing_alliance_ids

        # Create a list of new Alliance instances to be created in bulk
        new_alliances = []
        for alliance_id in alliances_to_create:
            alliance_data = ESIHandler.get_alliances_alliance_id(
                alliance_id=alliance_id, force_refresh=force_refresh
            )

            logger.debug(
                f"Fetched alliance data for alliance ID {alliance_id} from ESI"
            )

            if alliance_data:
                new_alliances.append(
                    cls(
                        alliance_id=alliance_id,
                        name=alliance_data.name,
                    )
                )
            else:
                logger.warning(
                    f"Failed to fetch data for alliance ID {alliance_id} from ESI. Skipping creation."
                )

        logger.debug("New Alliances to create: %s", new_alliances)

        # Bulk create new alliances and collect them in a list
        created_alliances = []
        if new_alliances:
            created_alliances = cls.objects.bulk_create(new_alliances)

        # Combine existing and newly created alliances into a single dictionary
        all_alliances = {
            alliance.alliance_id: alliance for alliance in existing_alliances
        } | {alliance.alliance_id: alliance for alliance in created_alliances}

        return all_alliances


class SovereigntyStructure(models.Model):
    """
    Sov structures
    """

    structure_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    alliance = models.ForeignKey(
        to=Alliance,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="sov_structure_alliance",
    )
    solar_system = models.ForeignKey(
        to=SolarSystem,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="sov_structure_solar_system",
    )
    structure_type_id = models.PositiveBigIntegerField()
    vulnerability_occupancy_level = models.FloatField(default=1)
    vulnerable_end_time = models.DateTimeField(null=True, blank=True)
    vulnerable_start_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        """
        Meta definitions
        """

        verbose_name = _("Sovereignty structure")
        verbose_name_plural = _("Sovereignty structures")
        default_permissions = ()

    @staticmethod
    def get_sov_structures_from_esi(force_refresh: bool = False):
        """
        Get all sov structures from ESI

        :param force_refresh:
        :type force_refresh:
        :return:
        :rtype:
        """

        sov_structures_from_esi = ESIHandler.get_sovereignty_structures(
            force_refresh=force_refresh
        )

        if sov_structures_from_esi:
            logger.debug(
                msg=f"Fetched {len(sov_structures_from_esi or [])} sovereignty structures from ESI"
            )
        else:
            logger.info(
                msg="No sovereignty structure changes found, nothing to update."
            )

        return sov_structures_from_esi


class Campaign(models.Model):
    """
    Sov campaigns
    """

    class Type(models.TextChoices):
        """
        Choices for Comment Types
        """

        SOVHUB_DEFENSE = "sovhub", _("Sov Hub defense")

    campaign_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    attackers_score = models.FloatField(default=0.4)
    defender_score = models.FloatField(default=0.6)
    event_type = models.CharField(
        max_length=12, choices=Type.choices, default=Type.SOVHUB_DEFENSE
    )
    start_time = models.DateTimeField()
    structure = models.OneToOneField(
        to=SovereigntyStructure,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="sov_capaign_structure",
    )

    progress_current = models.FloatField(default=0.6)
    progress_previous = models.FloatField(default=0.6)

    class Meta:
        """
        Meta definitions
        """

        verbose_name = _("Sovereignty campaign")
        verbose_name_plural = _("Sovereignty campaigns")
        default_permissions = ()

    @staticmethod
    def get_sov_campaigns_from_esi(force_refresh: bool = False):
        """
        Get all sov campaigns from ESI

        :return:
        """

        campaigns_from_esi = ESIHandler.get_sovereignty_campaigns(
            force_refresh=force_refresh
        )

        if campaigns_from_esi:
            logger.debug(
                msg=f"Fetched {len(campaigns_from_esi or [])} campaigns from ESI"
            )
        else:
            logger.info(msg="No campaign changes found, nothing to update.")

        return campaigns_from_esi
