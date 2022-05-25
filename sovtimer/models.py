"""
Our Models
"""

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveEntity, EveSolarSystem

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.providers import esi

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


class AaSovtimer(models.Model):
    """
    Meta model for app permissions
    """

    class Meta:
        verbose_name = "Sovereignty Timer"
        managed = False
        default_permissions = ()
        permissions = (("basic_access", "Can access the Sovereignty Timer module"),)


class SovereigntyStructure(models.Model):
    """
    sov structures
    """

    structure_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    alliance = models.ForeignKey(
        EveEntity,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="sov_structure_alliance",
    )
    solar_system = models.ForeignKey(
        EveSolarSystem,
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
        meta definitions
        """

        verbose_name = "Sovereignty Structure"
        verbose_name_plural = "Sovereignty Structures"
        default_permissions = ()

    @classmethod
    def sov_structures_from_esi(cls):
        """
        get all sov structures from ESI
        :return:
        """

        try:
            sovereignty_structures_esi = (
                esi.client.Sovereignty.get_sovereignty_structures().results()
            )
        except OSError as ex:
            logger.info(
                f"Something went wrong while trying to fetch sov structures from ESI: {ex}"
            )
            sovereignty_structures_esi = None

        return sovereignty_structures_esi


class Campaign(models.Model):
    """
    sov campaigns
    """

    class Type(models.TextChoices):
        """
        Choices for Comment Types
        """

        IHUB_DEFENSE = "ihub_defense", _("IHub Defense")
        TCU_DEFENSE = "tcu_defense", _("TCU Defense")

    campaign_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    attackers_score = models.FloatField(default=0.4)
    defender_score = models.FloatField(default=0.6)
    event_type = models.CharField(max_length=12, choices=Type.choices)
    start_time = models.DateTimeField()
    structure = models.OneToOneField(
        SovereigntyStructure,
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
        meta definitions
        """

        verbose_name = "Sovereignty Campaign"
        verbose_name_plural = "Sovereignty Campaigns"
        default_permissions = ()

    @classmethod
    def sov_campaigns_from_esi(cls):
        """
        get all sov campaigns from ESI
        :return:
        """

        try:
            sovereignty_campaigns_esi = (
                esi.client.Sovereignty.get_sovereignty_campaigns().results()
            )
        except OSError as ex:
            logger.info(
                f"Something went wrong while trying to fetch sov campaigns from ESI: {ex}"
            )
            sovereignty_campaigns_esi = None

        return sovereignty_campaigns_esi
