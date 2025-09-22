# Copyright (c) 2022-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=attribute-defined-outside-init

from django.test import override_settings, TestCase
from django.utils import timezone

from parameterized import parameterized

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem
from tcms.tests.factories import ComponentFactory, TestExecutionFactory

from trackers_integration.models import ApiToken
from trackers_integration.issuetracker import OpenProject


class TestOpenProjectIntegration(APITestCase):
    existing_bug_id = 8
    existing_bug_url = (
        "http://bugtracker.kiwitcms.org/projects/demo-project/work_packages/8/activity"
    )

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution_1 = TestExecutionFactory()
        cls.execution_1.case.summary = "Tested at " + timezone.now().isoformat()
        cls.execution_1.case.text = "Given-When-Then"
        cls.execution_1.case.save()  # will generate history object
        cls.execution_1.run.summary = (
            "Automated TR for OpenProject integration on " + timezone.now().isoformat()
        )
        cls.execution_1.run.save()

        cls.component = ComponentFactory(
            name="OpenProject integration",
            product=cls.execution_1.build.version.product,
        )
        cls.execution_1.case.add_component(cls.component)

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="OpenProject for kiwitcms/trackers-integration",
            tracker_type="trackers_integration.issuetracker.OpenProject",
            base_url="http://bugtracker.kiwitcms.org",
            api_password="26210315639327b10b56b7ef5d2f47f843c0ced3bafd1540fd4ecb30a06fa80f",
        )
        cls.integration = OpenProject(bug_system, None)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

    def test_details(self):
        result = self.integration.details(self.existing_bug_url)

        self.assertEqual(self.existing_bug_id, result["id"])
        self.assertEqual("", result["description"])
        self.assertEqual("NEW", result["status"])
        self.assertEqual("TASK: Setup conference website", result["title"])
        self.assertEqual(self.existing_bug_url, result["url"])

    def test_auto_update_bugtracker(self):
        last_comment = None
        initial_comments = self.integration.rpc.get_comments(self.existing_bug_id)

        # simulate user adding a new bug URL to a TE and clicking
        # 'Automatically update bug tracker'
        result = self.rpc_client.TestExecution.add_link(
            {
                "execution_id": self.execution_1.pk,
                "is_defect": True,
                "url": self.existing_bug_url,
            },
            True,
        )

        # making sure RPC above returned the same URL
        self.assertEqual(self.existing_bug_url, result["url"])

        # wait until comments have been refreshed b/c this seem to happen async
        initial_comments_length = initial_comments["count"]
        current_comments_length = initial_comments_length
        while current_comments_length != initial_comments_length + 1:
            comments = self.integration.rpc.get_comments(self.existing_bug_id)
            current_comments_length = comments["count"]

        last_comment = comments["_embedded"]["elements"][-1]

        # comment made by 'admin' user
        self.assertEqual(last_comment["_links"]["user"]["href"], "/api/v3/users/4")

        # assert that a comment has been added as the last one
        # and also verify its text
        for expected_string in [
            "Confirmed via test execution",
            f"TR-{self.execution_1.run_id}: {self.execution_1.run.summary}",
            self.execution_1.run.get_full_url(),
            f"TE-{self.execution_1.pk}: {self.execution_1.case.summary}",
        ]:
            self.assertIn(expected_string, last_comment["comment"]["raw"])

    def test_report_issue_from_test_execution_1click_works(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(
            self.execution_1.pk, self.integration.bug_system.pk
        )
        self.assertEqual(result["rc"], 0)
        self.assertIn(self.integration.bug_system.base_url, result["response"])
        self.assertIn("/work_packages/", result["response"])

        new_issue_id = self.integration.bug_id_from_url(result["response"])
        issue = self.integration.rpc.get_workpackage(new_issue_id)

        # new issue opened by 'admin' user
        self.assertEqual(issue["_links"]["author"]["href"], "/api/v3/users/4")
        self.assertEqual(
            f"Failed test: {self.execution_1.case.summary}",
            issue["subject"],
        )
        for expected_string in [
            f"Filed from execution {self.execution_1.get_full_url()}",
            "Reporter",
            self.execution_1.build.version.product.name,
            self.component.name,
            "Steps to reproduce",
            self.execution_1.case.text,
        ]:
            self.assertIn(expected_string, issue["description"]["raw"])

        # verify that LR has been added to TE
        self.assertTrue(
            LinkReference.objects.filter(
                execution=self.execution_1,
                url=result["response"],
                is_defect=True,
            ).exists()
        )

    def test_report_issue_with_overriden_workpackage_type_name(self):
        with override_settings(OPENPROJECT_WORKPACKAGE_TYPE_NAME="Epic"):
            # simulate user clicking the 'Report bug' button in TE widget, TR page
            result = self.rpc_client.Bug.report(
                self.execution_1.pk, self.integration.bug_system.pk
            )
            self.assertEqual(result["rc"], 0)
            self.assertIn(self.integration.bug_system.base_url, result["response"])
            self.assertIn("/work_packages/", result["response"])

            new_issue_id = self.integration.bug_id_from_url(result["response"])
            issue = self.integration.rpc.get_workpackage(new_issue_id)
            self.assertEqual(issue["_links"]["type"]["title"], "Epic")


class FakeRequest:  # pylint: disable=too-few-public-methods
    user = None


class TestOpenProjectAndIndividualApiTokens(APITestCase):
    existing_bug_id = 6
    existing_bug_url = (
        "http://bugtracker.kiwitcms.org/projects/demo-project/work_packages/6/activity"
    )

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution_1 = TestExecutionFactory()

        cls.execution_1.case.summary = "Tested at " + timezone.now().isoformat()
        cls.execution_1.case.text = "Given-When-Then"
        cls.execution_1.case.save()  # will generate history object

        cls.execution_1.run.summary = (
            "Automated TR for OpenProject and individual API token "
            + timezone.now().isoformat()
        )
        cls.execution_1.run.save()

        # 'kiwitcms-bot' user is authorized only for this project
        cls.execution_1.build.version.product.name = "Demo project"
        cls.execution_1.build.version.product.save()

        cls.component = ComponentFactory(
            name="OpenProject integration",
            product=cls.execution_1.build.version.product,
        )
        cls.execution_1.case.add_component(cls.component)

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="OpenProject for kiwitcms/trackers-integration",
            tracker_type="trackers_integration.issuetracker.OpenProject",
            base_url="http://bugtracker.kiwitcms.org",
            api_password="bogus-will-use-individual-api-tokens",
        )

        # API token for 'kiwitcms-bot' user defined in seeds.rb
        ApiToken.objects.create(
            owner=cls.api_user,
            base_url=bug_system.base_url,
            api_password="c48c60020d8f61e612241889eff79e610410f1322811d8c20df25a71f3619e25",
        )
        fake_request = FakeRequest()
        fake_request.user = cls.api_user
        cls.integration = OpenProject(bug_system, fake_request)

    def test_auto_update_bugtracker(self):
        last_comment = None
        initial_comments = self.integration.rpc.get_comments(self.existing_bug_id)

        # simulate user adding a new bug URL to a TE and clicking
        # 'Automatically update bug tracker'
        result = self.rpc_client.TestExecution.add_link(
            {
                "execution_id": self.execution_1.pk,
                "is_defect": True,
                "url": self.existing_bug_url,
            },
            True,
        )

        # making sure RPC above returned the same URL
        self.assertEqual(self.existing_bug_url, result["url"])

        # wait until comments have been refreshed b/c this seem to happen async
        initial_comments_length = initial_comments["count"]
        current_comments_length = initial_comments_length
        while current_comments_length != initial_comments_length + 1:
            comments = self.integration.rpc.get_comments(self.existing_bug_id)
            current_comments_length = comments["count"]

        last_comment = comments["_embedded"]["elements"][-1]

        # comment made by 'kiwitcms-bot' user
        self.assertEqual(last_comment["_links"]["user"]["href"], "/api/v3/users/5")

        # assert that a comment has been added as the last one
        # and also verify its text
        for expected_string in [
            "Confirmed via test execution",
            f"TR-{self.execution_1.run_id}: {self.execution_1.run.summary}",
            self.execution_1.run.get_full_url(),
            f"TE-{self.execution_1.pk}: {self.execution_1.case.summary}",
        ]:
            self.assertIn(expected_string, last_comment["comment"]["raw"])

    def test_report_issue_from_test_execution_1click_works(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(
            self.execution_1.pk, self.integration.bug_system.pk
        )
        self.assertEqual(result["rc"], 0)
        self.assertIn(self.integration.bug_system.base_url, result["response"])
        self.assertIn("/work_packages/", result["response"])

        new_issue_id = self.integration.bug_id_from_url(result["response"])
        issue = self.integration.rpc.get_workpackage(new_issue_id)

        # new issue opened by 'kiwitcms-bot' user
        self.assertEqual(issue["_links"]["author"]["href"], "/api/v3/users/5")
        self.assertEqual(
            f"Failed test: {self.execution_1.case.summary}",
            issue["subject"],
        )
        for expected_string in [
            f"Filed from execution {self.execution_1.get_full_url()}",
            "Reporter",
            self.execution_1.build.version.product.name,
            self.component.name,
            "Steps to reproduce",
            self.execution_1.case.text,
        ]:
            self.assertIn(expected_string, issue["description"]["raw"])

        # verify that LR has been added to TE
        self.assertTrue(
            LinkReference.objects.filter(
                execution=self.execution_1,
                url=result["response"],
                is_defect=True,
            ).exists()
        )


class TestOpenProjectInternalImplementation(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="OpenProject for kiwitcms/trackers-integration",
            tracker_type="trackers_integration.issuetracker.OpenProject",
            base_url="http://bugtracker.kiwitcms.org",
            api_password="26210315639327b10b56b7ef5d2f47f843c0ced3bafd1540fd4ecb30a06fa80f",
        )
        cls.openproject = OpenProject(bug_system, None)

    @parameterized.expand(
        [
            (
                "no_project_prefix_no_activity_suffix",
                "http://bugtracker.kiwitcms.org/work_packages/8",
            ),
            (
                "no_project_prefix_yes_activity_suffix",
                "http://bugtracker.kiwitcms.org/work_packages/8/activity",
            ),
            (
                "yes_project_prefix_no_activity_suffix",
                "http://bugtracker.kiwitcms.org/projects/demo-project/work_packages/8",
            ),
            (
                "yes_project_prefix_yes_activity_suffix",
                "http://bugtracker.kiwitcms.org/projects/demo-project/work_packages/8/activity",
            ),
        ]
    )
    def test_bug_id_from_url(self, _name, existing_bug_url):
        result = self.openproject.bug_id_from_url(existing_bug_url)
        self.assertEqual(result, 8)

    def test_workpackage_type_with_name_match(self):
        project = self.openproject.get_project_by_name("Scrum project")
        result = self.openproject.get_workpackage_type(project["id"], "Bug")
        # Scrum project has Bug
        self.assertEqual(result["name"], "Bug")

    def test_workpackage_type_fallback_to_first(self):
        project = self.openproject.get_project_by_name("Demo project")
        result = self.openproject.get_workpackage_type(project["id"], "Bug")
        # Demo project doesn't have Bug, but has Task
        self.assertEqual(result["name"], "Task")

    def test_workpackage_type_exception(self):
        with self.assertRaisesRegex(RuntimeError, "WorkPackage Type not found"):
            self.openproject.get_workpackage_type(-1, "Bug")

    def test_get_project_by_name_match(self):
        result = self.openproject.get_project_by_name("Scrum project")
        self.assertEqual(result["name"], "Scrum project")

    def test_get_project_by_name_search_identifier(self):
        result = self.openproject.get_project_by_name("demo-project")
        self.assertEqual(result["name"], "Demo project")

    def test_get_project_by_name_fallback_to_first(self):
        result = self.openproject.get_project_by_name("Non Existent Project")
        self.assertEqual(result["name"], "Scrum project")
