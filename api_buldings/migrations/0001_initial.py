# Generated by Django 5.0.4 on 2024-05-07 09:20

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Building",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("address", models.CharField(max_length=255)),
                (
                    "coordinates",
                    django.contrib.gis.db.models.fields.PolygonField(srid=4326),
                ),
            ],
        ),
    ]
