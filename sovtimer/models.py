# coding=utf-8

"""
Our Models
"""

from django.db import models


class AaSovtimer(models.Model):
    """
    Meta model for app permissions
    """

    class Meta:
        verbose_name = "Sovereignty Timer"
        managed = False
        default_permissions = ()
        permissions = (("basic_access", "Can access the Sovereignty Timer module"),)
