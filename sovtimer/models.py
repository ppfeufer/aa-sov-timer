"""
Our Models
"""

# Third Party
from aiopenapi3 import ContentTypeError

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth.services.hooks import get_extension_logger
from esi.exceptions import HTTPClientError, HTTPNotModified

# Alliance Auth (External Libs)
from app_utils.logging import LoggerAddTag
from eveuniverse.models import EveEntity, EveSolarSystem

# AA Sovereignty Timer
from sovtimer import __title__
from sovtimer.providers import esi

logger = LoggerAddTag(my_logger=get_extension_logger(name=__name__), prefix=__title__)


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


class SovereigntyStructure(models.Model):
    """
    Sov structures
    """

    structure_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    alliance = models.ForeignKey(
        to=EveEntity,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        related_name="sov_structure_alliance",
    )
    solar_system = models.ForeignKey(
        to=EveSolarSystem,
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

    @classmethod
    def get_sov_structures_from_esi(cls, force_refresh: bool = False):
        """
        Get all sov structures from ESI

        :param force_refresh:
        :type force_refresh:
        :return:
        :rtype:
        """

        try:
            sov_structures_from_esi = (
                esi.client.Sovereignty.GetSovereigntyStructures().result(
                    force_refresh=force_refresh
                )
            )

            logger.debug(
                msg=f"Fetched {len(sov_structures_from_esi or [])} sovereignty structures from ESI."
            )
            logger.debug(msg=f"Sovereignty structure data: {sov_structures_from_esi}")
        except HTTPNotModified:
            logger.info(
                msg="No sovereignty structure changes found, nothing to update."
            )

            return None
        except ContentTypeError:
            logger.warning(
                msg="ESI returned gibberish (ContentTypeError), skipping sovereignty structure update."
            )

            return None
        except HTTPClientError as exc:
            logger.error(
                msg=f"Error while fetching sovereignty structures from ESI: {str(exc)}"
            )

            return None

        return sov_structures_from_esi


class Campaign(models.Model):
    """
    Sov campaigns
    """

    class Type(models.TextChoices):
        """
        Choices for Comment Types
        """

        SOVHUB_DEFENSE = "ihub_defense", _("Sov Hub defense")
        TCU_DEFENSE = "tcu_defense", _("TCU defense")

    campaign_id = models.PositiveBigIntegerField(
        primary_key=True, db_index=True, unique=True
    )
    attackers_score = models.FloatField(default=0.4)
    defender_score = models.FloatField(default=0.6)
    event_type = models.CharField(max_length=12, choices=Type.choices)
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

    @classmethod
    def get_sov_campaigns_from_esi(cls, force_refresh: bool = False):
        """
        Get all sov campaigns from ESI

        :return:
        """

        try:
            campaigns_from_esi = (
                esi.client.Sovereignty.GetSovereigntyCampaigns().result(
                    force_refresh=force_refresh
                )
            )

            logger.debug(
                msg=f"Fetched {len(campaigns_from_esi or [])} campaigns from ESI."
            )
            logger.debug(msg=f"Campaign data: {campaigns_from_esi}")
        except HTTPNotModified:
            logger.info(msg="No campaign changes found, nothing to update.")

            return None
        except ContentTypeError:
            logger.warning(
                msg="ESI returned gibberish (ContentTypeError), skipping campaign update."
            )

            return None
        except HTTPClientError as exc:
            logger.error(msg=f"Error while fetching campaigns from ESI: {str(exc)}")

            return None

        return campaigns_from_esi
