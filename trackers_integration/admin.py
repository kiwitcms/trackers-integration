# pylint: disable=no-self-use

from django import forms
from django.contrib import admin

from trackers_integration.models import ApiToken


class ApiTokenAdminForm(forms.ModelForm):
    # make password show asterisks
    api_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True), required=False
    )

    class Meta:
        model = ApiToken
        fields = ("base_url", "api_username", "api_password")


class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "base_url", "api_username")
    form = ApiTokenAdminForm

    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """View, change & delete only tokens which you own!"""
        return super().get_queryset(request).filter(owner=request.user)


admin.site.register(ApiToken, ApiTokenAdmin)
