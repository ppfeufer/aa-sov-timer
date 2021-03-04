"""
Our Models
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from eveuniverse.models import EveEntity, EveSolarSystem

from sovtimer.providers import esi


class AaSovtimer(models.Model):
    """
    Meta model for app permissions
    """

    class Meta:
        verbose_name = "Sovereignty Timer"
        managed = False
        default_permissions = ()
        permissions = (("basic_access", "Can access the Sovereignty Timer module"),)


class AaSovtimerCampaignType(models.TextChoices):
    """
    Choices for Comment Types
    """

    IHUB_DEFENSE = "ihub_defense", _("IHub Defense")
    TCU_DEFENSE = "tcu_defense", _("TCU Defense")


class AaSovtimerCampaigns(models.Model):
    """
    sov campaigns
    """

    campaign_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    attackers_score = models.FloatField(default=0.6)
    defender = models.ForeignKey(
        EveEntity,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="sov_campaign_defender",
    )

    defender_score = models.FloatField(default=0.6)
    event_type = models.CharField(max_length=12, choices=AaSovtimerCampaignType.choices)
    solar_system = models.ForeignKey(
        EveSolarSystem,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="sov_capaign_solar_system",
    )

    start_time = models.DateTimeField()
    structure_id = models.PositiveBigIntegerField()

    progress_current = models.FloatField(default=0.6)
    progress_previous = models.FloatField(default=0.6)

    @classmethod
    def sov_campaigns_from_esi(cls):
        """
        get all sov campaigns from ESI
        :return:
        """

        sovereignty_campaigns_esi = (
            esi.client.Sovereignty.get_sovereignty_campaigns().results()
        )

        return sovereignty_campaigns_esi

    class Meta:
        """
        meta definitions
        """

        verbose_name = "Sovereignty Campaign"
        verbose_name_plural = "Sovereignty Campaigns"
        default_permissions = ()


class AaSovtimerStructures(models.Model):
    """
    sov structures
    """

    structure_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    alliance = models.ForeignKey(
        EveEntity,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="sov_structure_alliance",
    )
    solar_system = models.ForeignKey(
        EveSolarSystem,
        on_delete=models.SET_DEFAULT,
        default=None,
        null=True,
        blank=True,
        related_name="sov_structure_solar_system",
    )
    structure_type_id = models.PositiveBigIntegerField()
    vulnerability_occupancy_level = models.FloatField(null=True)
    vulnerable_end_time = models.DateTimeField(null=True)
    vulnerable_start_time = models.DateTimeField(null=True)

    @classmethod
    def sov_structures_from_esi(cls):
        """
        get all sov structures from ESI
        :return:
        """

        sovereignty_structures_esi = (
            esi.client.Sovereignty.get_sovereignty_structures().results()
        )

        return sovereignty_structures_esi

    class Meta:
        """
        meta definitions
        """

        verbose_name = "Sovereignty Structure"
        verbose_name_plural = "Sovereignty Structures"
        default_permissions = ()
