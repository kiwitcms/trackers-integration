# Copyright (c) 2023-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=no-self-use

from contextlib import ContextDecorator
from django import forms
from django.contrib import admin

try:
    from django_tenants.utils import tenant_context
except ModuleNotFoundError:

    class tenant_context(
        ContextDecorator
    ):  # pylint: disable=invalid-name,remove-empty-class,nested-class-found,too-few-public-methods
        pass


from tcms.testcases.models import BugSystem
from trackers_integration.models import ApiToken


class ApiTokenAdminForm(forms.ModelForm):
    # display a drop-down of filtered URLs of defined Issue Trackers
    base_url = forms.ChoiceField(required=True)

    # make password show asterisks
    api_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True), required=True
    )

    class Meta:
        model = ApiToken
        fields = ("base_url", "api_username", "api_password")


class ApiTokenAdmin(admin.ModelAdmin):
    _for_more_info = """WARNING: read
<a href="https://kiwitcms.org/blog/kiwi-tcms-team/2023/12/06/feature-showcase-personal-api-tokens/">
the documentation</a> before editting the values below!"""
    fieldsets = [
        (
            "",
            {
                "fields": ("base_url", "api_username", "api_password"),
                "description": f"<h1>{_for_more_info}</h1>",
            },
        ),
    ]

    list_display = ("id", "owner", "base_url", "api_username")
    form = ApiTokenAdminForm

    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """View, change & delete only tokens which you own!"""
        return super().get_queryset(request).filter(owner=request.user)

    def get_issuetracker_urls(self, request):
        """
        Return a list of drop-down choices which represent all of the
        defined external Issue Tracker records accessible to the current user
        across all tenants they are authorized for!
        """
        choices = []

        for tenant in request.user.tenant_set.all():
            with tenant_context(tenant):
                for base_url in BugSystem.objects.all().values_list(
                    "base_url", flat=True
                ):
                    # note: (<actual value>, <display value>)
                    choices.append((base_url, base_url))

        return list(set(choices))

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)

        form.base_fields["base_url"].choices = self.get_issuetracker_urls(request)
        return form


admin.site.register(ApiToken, ApiTokenAdmin)
