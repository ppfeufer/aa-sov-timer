# Generated by Django 4.2.14 on 2024-07-16 05:58

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sovtimer", "0009_alter_campaign_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="campaign",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("ihub_defense", "Sov Hub defense"),
                    ("tcu_defense", "TCU defense"),
                ],
                max_length=12,
            ),
        ),
    ]
