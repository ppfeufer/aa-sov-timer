# Generated by Django 3.2.11 on 2022-01-29 16:21

# Django
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("eveuniverse", "0005_type_materials_and_sections"),
        ("sovtimer", "0005_auto_20201114_0720"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="AaSovtimerStructures",
            new_name="SovereigntyStructure",
        ),
        migrations.RenameModel(
            old_name="AaSovtimerCampaigns",
            new_name="Campaign",
        ),
    ]
