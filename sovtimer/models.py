# coding=utf-8

"""
Our Models
"""

from django.db import models

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


class AaSovtimerCampaigns(models.Model):
    """
    sov campaigns
    """

    campaign_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    attackers_score = models.FloatField()
    constellation_id = models.PositiveBigIntegerField()
    defender_id = models.PositiveBigIntegerField()
    defender_score = models.FloatField()
    event_type = models.CharField(max_length=12)
    solar_system_id = models.PositiveBigIntegerField()
    start_time = models.DateTimeField()
    structure_id = models.PositiveBigIntegerField()

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
    alliance_id = models.PositiveBigIntegerField()
    solar_system_id = models.PositiveBigIntegerField()
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
