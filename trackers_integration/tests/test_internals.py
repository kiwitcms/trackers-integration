from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.urls import reverse

from tcms.kiwi_auth.tests import __FOR_TESTING__
from tcms.tests.factories import UserFactory
from tcms.testcases.models import BugSystem
from tcms.utils.permissions import initiate_user_with_default_setups

from tcms_tenants.tests import LoggedInTestCase  # pylint: disable=import-error
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
    def setUpClass(cls):  # pylint: disable=invalid-name
        super().setUpClass()

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

        cls.alice = UserFactory(username="Alice")
        cls.alices_token = ApiToken.objects.create(
            owner=cls.alice,
            base_url="http://example.com",
            api_username="alice@redmine",
            api_password=__FOR_TESTING__,
        )

        cls.testers_token = ApiToken.objects.create(
            owner=cls.tester,
            base_url="http://bugzilla.example.com",
            api_username="tester@bugzilla.org",
            api_password=__FOR_TESTING__,
        )

    def test_adding_a_token_updates_the_owner_field_to_the_current_user(self):
        initial_count = ApiToken.objects.filter(owner=self.tester).count()

        # the owner field isn't visible in the Add page
        response = self.client.get(reverse("admin:trackers_integration_apitoken_add"))
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertNotContains(response, "Owner")

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

        self.assertEqual(
            ApiToken.objects.filter(owner=self.tester).count(), initial_count + 1
        )
        token = ApiToken.objects.filter(owner=self.tester).last()
        self.assertEqual(token.base_url, "http://open-project.example.com")
        self.assertEqual(token.api_username, "kiwitcms-bot")

    def test_add_view_shows_dropdown_select_of_existing_bug_trackers(self):
        response = self.client.get(reverse("admin:trackers_integration_apitoken_add"))
        # warning: can't assert on the select tag b/c order of its attribute change
        # but html=True expects a closed <select> tag with everything in between
        self.assertContains(
            response,
            '<option value="https://mantis.example.com:8443/mantisbt">'
            "https://mantis.example.com:8443/mantisbt</option>",
            html=True,
        )
        self.assertContains(
            response,
            '<option value="http://open-project.example.com">'
            "http://open-project.example.com</option>",
            html=True,
        )

        # POSTing an invalid base_url will trigger an error
        response = self.client.post(
            reverse("admin:trackers_integration_apitoken_add"),
            {
                "base_url": "http://invalid.com",
                "api_username": "kiwitcms-bot",
                "api_password": __FOR_TESTING__,
            },
            follow=True,
        )
        self.assertNotContains(response, "kiwitcms-bot @ http://invalid.com")
        self.assertNotContains(response, "was added successfully")
        self.assertContains(response, "Please correct the error below")
        self.assertContains(
            response,
            "Select a valid choice. http://invalid.com is not one of the available choices.",
        )

    def test_changelist_view_doesnt_show_records_from_other_users(self):
        response = self.client.get(
            reverse("admin:trackers_integration_apitoken_changelist")
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertNotContains(response, "alice@redmine")
        self.assertNotContains(
            response,
            f"/admin/trackers_integration/apitoken/{self.alices_token.pk}/change/",
        )

    def test_changelist_view_shows_records_from_myself(self):
        response = self.client.get(
            reverse("admin:trackers_integration_apitoken_changelist")
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, "tester@bugzilla.org")
        self.assertContains(
            response,
            f"/admin/trackers_integration/apitoken/{self.testers_token.pk}/change/",
        )

    def test_change_view_doesnt_show_records_from_other_users(self):
        response = self.client.get(
            reverse(
                "admin:trackers_integration_apitoken_change",
                args=[self.alices_token.pk],
            ),
            follow=True,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(
            response, f"api token with ID “{self.alices_token.pk}” doesn’t exist"
        )
        self.assertContains(response, "Site administration")

    def test_change_view_shows_records_from_myself(self):
        response = self.client.get(
            reverse(
                "admin:trackers_integration_apitoken_change",
                args=[self.testers_token.pk],
            ),
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, "Change api token")
        self.assertContains(
            response,
            f"/admin/trackers_integration/apitoken/{self.testers_token.pk}/delete/",
        )

    def test_delete_view_doesnt_show_records_from_other_users(self):
        response = self.client.get(
            reverse(
                "admin:trackers_integration_apitoken_delete",
                args=[self.alices_token.pk],
            ),
            follow=True,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(
            response, f"api token with ID “{self.alices_token.pk}” doesn’t exist"
        )
        self.assertContains(response, "Site administration")

        # retry with a POST request
        response = self.client.post(
            reverse(
                "admin:trackers_integration_apitoken_delete",
                args=[self.alices_token.pk],
            ),
            {"post": "yes"},
            follow=True,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(
            response, f"api token with ID “{self.alices_token.pk}” doesn’t exist"
        )
        self.assertContains(response, "Site administration")

    def test_delete_view_shows_records_from_myself(self):
        self_token = ApiToken.objects.create(
            owner=self.tester,
            base_url="http://self.example.com",
            api_username="self@example.com",
            api_password=__FOR_TESTING__,
        )

        response = self.client.get(
            reverse(
                "admin:trackers_integration_apitoken_delete",
                args=[self_token.pk],
            ),
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, "Are you sure")
        self.assertContains(
            response, f"/admin/trackers_integration/apitoken/{self_token.pk}/change/"
        )

        # retry with a POST request
        response = self.client.post(
            reverse(
                "admin:trackers_integration_apitoken_delete",
                args=[self_token.pk],
            ),
            {"post": "yes"},
            follow=True,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(
            response, f"The api token “{self_token}” was deleted successfully."
        )
        self.assertContains(response, "Api tokens")
