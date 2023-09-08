from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.urls import reverse

from tcms.kiwi_auth.tests import __FOR_TESTING__
from tcms.tests import LoggedInTestCase
from tcms.testcases.models import BugSystem
from tcms.utils.permissions import initiate_user_with_default_setups

from trackers_integration.models import ApiToken


def initialize_permissions(user):
    initiate_user_with_default_setups(user)

    apitoken_perms = Permission.objects.filter(
        content_type__app_label__contains="trackers_integration",
        content_type__model="apitoken",
    )
    user.user_permissions.add(*apitoken_perms)


class TestApiTokenAdmin(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        initialize_permissions(cls.tester)

        BugSystem.objects.create(
            name="Mantis for kiwitcms/test-mantis-integration",
            tracker_type="trackers_integration.issuetracker.Mantis",
            base_url="https://mantis.example.com:8443/mantisbt",
            api_password=__FOR_TESTING__,
        )

        BugSystem.objects.create(
            name="OpenProject for kiwitcms/trackers-integration",
            tracker_type="trackers_integration.issuetracker.OpenProject",
            base_url="http://open-project.example.com",
            api_password=__FOR_TESTING__,
        )

    def test_adding_a_token_updates_the_owner_field_to_the_current_user(self):
        # the owner field isn't visible in the Add page
        response = self.client.get(reverse("admin:trackers_integration_apitoken_add"))
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertNotContains(response, "Owner")

        self.assertFalse(ApiToken.objects.filter(owner=self.tester).exists())
        response = self.client.post(
            reverse("admin:trackers_integration_apitoken_add"),
            {
                "base_url": "http://open-project.example.com",
                "api_username": "kiwitcms-bot",
                "api_password": __FOR_TESTING__,
            },
            follow=True,
        )
        self.assertContains(response, "kiwitcms-bot @ http://open-project.example.com")
        self.assertContains(response, "was added successfully")

        self.assertTrue(ApiToken.objects.filter(owner=self.tester).exists())
        token = ApiToken.objects.filter(owner=self.tester).first()
        self.assertEqual(token.base_url, "http://open-project.example.com")
        self.assertEqual(token.api_username, "kiwitcms-bot")
