# pylint: disable=no-self-use

from django.contrib import admin

from trackers_integration.models import ApiToken


admin.site.register(ApiToken)
