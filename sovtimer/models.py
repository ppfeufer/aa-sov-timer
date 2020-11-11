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

    campaign_id = models.PositiveIntegerField(primary_key=True, db_index=True)
    attackers_score = models.FloatField()
    constellation_id = models.PositiveIntegerField()
    defender_id = models.PositiveIntegerField()
    defender_score = models.FloatField()
    event_type = models.CharField(max_length=12)
    solar_system_id = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    structure_id = models.PositiveIntegerField()

    def sov_campaigns_from_esi(self):
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
        verbose_name = "Sovereignty Campaigns"
        default_permissions = ()
