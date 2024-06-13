# Copyright (c) 2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ApiToken",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "base_url",
                    models.CharField(
                        blank=True,
                        help_text="Base URL, for example "
                        "<strong>https://bugzilla.example.com</strong>!",
                        max_length=1024,
                        null=True,
                        verbose_name="Base URL",
                    ),
                ),
                (
                    "api_username",
                    models.CharField(
                        blank=True,
                        max_length=256,
                        null=True,
                        verbose_name="API username",
                    ),
                ),
                (
                    "api_password",
                    models.CharField(
                        blank=True,
                        max_length=256,
                        null=True,
                        verbose_name="API password or token",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
