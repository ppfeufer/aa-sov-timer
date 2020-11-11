# Generated by Django 3.1.3 on 2020-11-11 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sovtimer", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AaSovtimerCampaigns",
            fields=[
                (
                    "campaign_id",
                    models.PositiveIntegerField(
                        db_index=True, primary_key=True, serialize=False
                    ),
                ),
                ("attackers_score", models.FloatField()),
                ("constellation_id", models.PositiveIntegerField()),
                ("defender_id", models.PositiveIntegerField()),
                ("defender_score", models.FloatField()),
                ("event_type", models.CharField(max_length=12)),
                ("solar_system_id", models.PositiveIntegerField()),
                ("start_time", models.DateTimeField()),
                ("structure_id", models.PositiveIntegerField()),
            ],
            options={
                "verbose_name": "Sovereignty Campaigns",
                "default_permissions": (),
            },
        ),
    ]
