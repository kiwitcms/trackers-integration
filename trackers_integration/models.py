# Copyright (c) 2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from django.conf import settings
from django.db import models


class ApiToken(models.Model):
    """
    .. important::

        This model needs to be only on the main tenant, not shared across
        all tenants !

    This model represents a personalized username/token used for
    integration with 3rd party Issue Tracking systems. The actual credentials will be
    substituted at runtime in order for automatically created bugs and comments
    to appear as if they came from the currently logged in user.

    #. **owner:** - a foreign key to a User instance!

    #. **base_url:** base URL to match an Issue Tracker definition.

    #. **api_username, api_password:** configuration for an internal RPC object
       that communicate to the issue tracking system when necessary. Depending on the
       actual type of IT we're interfacing with some of these values may not be necessary.
       Refer to :mod:`tcms.issuetracker.types` for more information!

       .. warning::

            This is saved as plain-text in the database because it needs to be passed
            to the internal RPC object!
    """

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    base_url = models.CharField(  # pylint:disable=form-field-help-text-used
        max_length=1024,
        null=True,
        blank=True,
        verbose_name="Base URL",
        help_text="Base URL, for example <strong>https://bugzilla.example.com</strong>!",
    )

    api_username = models.CharField(
        max_length=256, null=True, blank=True, verbose_name="API username"
    )

    api_password = models.CharField(
        max_length=256, null=True, blank=True, verbose_name="API password or token"
    )

    def __str__(self):
        return f"{self.api_username} @ {self.base_url}"
