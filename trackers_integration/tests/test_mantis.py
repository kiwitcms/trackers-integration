# Copyright (c) 2022-2025 Alexander Todorov <atodorov@otb.bg>
# Copyright (c) 2022 @cmbahadir <c.mete.bahadir@gmail.com>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=attribute-defined-outside-init, protected-access
import os

from django.utils import timezone

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem
from tcms.tests.factories import ComponentFactory, TestExecutionFactory

from trackers_integration.issuetracker import mantis
from trackers_integration.issuetracker.mantis import Mantis


class TestMantisIntegration(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution_1 = TestExecutionFactory()
        cls.execution_1.case.summary = "Tested at " + timezone.now().isoformat()
        cls.execution_1.case.text = "Given-When-Then"
        cls.execution_1.case.save()  # will generate history object
        cls.execution_1.run.summary = (
            "Automated TR for Mantis integration on " + timezone.now().isoformat()
        )
        cls.execution_1.run.save()

        cls.component = ComponentFactory(
            name="Mantis integration", product=cls.execution_1.build.version.product
        )
        cls.execution_1.case.add_component(cls.component)

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="Mantis for kiwitcms/test-mantis-integration",
            tracker_type="trackers_integration.issuetracker.Mantis",
            base_url=os.getenv(
                "MANTIS_URL", "https://bugtracker.kiwitcms.org:8443/mantisbt"
            ),
            api_password=os.getenv("MANTIS_API_TOKEN"),
        )
        cls.integration = Mantis(bug_system, None)

        # WARNING: container's certificate is self-signed
        mantis._VERIFY_SSL = False

        # create more data in Mantis BT
        public_project = cls.integration.rpc.create_project(
            cls.execution_1.run.plan.product.name
        )
        private_project = cls.integration.rpc.create_project(
            f"Private-Product-{cls.execution_1.run.plan.product_id}",
            status="stable",
            is_public=False,
        )
        # WARNING: Need to add global & local categories !!!!

        public_issue = cls.integration.rpc.create_issue(
            "Hello World", "First public bug here", "General", public_project["name"]
        )
        cls.private_issue = cls.integration.rpc.create_issue(
            "Hello Private",
            "Not everyone can read this",
            "General",
            private_project["name"],
        )

        cls.existing_bug_id = public_issue["id"]
        cls.existing_bug_url = (
            f"{bug_system.base_url}/view.php?id={cls.existing_bug_id}"
        )

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

    def test_details(self):
        result = self.integration.details(self.existing_bug_url)

        self.assertEqual(self.existing_bug_id, result["id"])
        self.assertIn("First public bug here", result["description"])
        self.assertEqual("new", result["status"])
        self.assertEqual("Hello World", result["title"])
        self.assertEqual(self.existing_bug_url, result["url"])

    def test_details_for_issue_in_private_project(self):
        target_url = f"{self.integration.bug_system.base_url}/view.php?id={self.private_issue['id']}"
        result = self.integration.details(target_url)

        self.assertEqual(self.private_issue["id"], result["id"])
        self.assertIn("Not everyone can read this", result["description"])
        self.assertEqual("new", result["status"])
        self.assertEqual("Hello Private", result["title"])
        self.assertEqual(target_url, result["url"])

    def test_auto_update_bugtracker(self):
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
        initial_comments_length = len(initial_comments)
        current_comments_length = initial_comments_length
        while current_comments_length != initial_comments_length + 1:
            comments = self.integration.rpc.get_comments(self.existing_bug_id)
            current_comments_length = len(comments)

        last_comment = comments[-1]

        # assert that a comment has been added as the last one
        # and also verify its text
        for expected_string in [
            "Confirmed via test execution",
            f"TR-{self.execution_1.run_id}: {self.execution_1.run.summary}",
            self.execution_1.run.get_full_url(),
            f"TE-{self.execution_1.pk}: {self.execution_1.case.summary}",
        ]:
            self.assertIn(expected_string, last_comment["text"])

        self.integration.rpc.delete_comment(self.existing_bug_id, last_comment["id"])

    def test_report_issue_from_test_execution_1click_works(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(
            self.execution_1.pk, self.integration.bug_system.pk
        )
        self.assertEqual(result["rc"], 0)
        self.assertIn(self.integration.bug_system.base_url, result["response"])
        self.assertIn("view.php?id=", result["response"])

        new_issue_id = self.integration.bug_id_from_url(result["response"])
        issue = self.integration.rpc.get_issue(new_issue_id)

        self.assertEqual(
            f"Failed test: {self.execution_1.case.summary}", issue["summary"]
        )
        for expected_string in [
            f"Filed from execution {self.execution_1.get_full_url()}",
            "Reporter",
            self.execution_1.build.version.product.name,
            self.component.name,
            "Steps to reproduce",
            self.execution_1.case.text,
        ]:
            self.assertIn(expected_string, issue["description"])

        # verify that LR has been added to TE
        self.assertTrue(
            LinkReference.objects.filter(
                execution=self.execution_1,
                url=result["response"],
                is_defect=True,
            ).exists()
        )

        # Close issue after test is finised.
        self.integration.rpc.close_issue(new_issue_id)

    def test_report_issue_from_test_execution_fallback_to_manual(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="Mantis for kiwitcms/test-mantis-integration Exception",
            tracker_type="trackers_integration.issuetracker.Mantis",
            base_url="https://mantisbt.example.com",
            api_password="an-invalid-token",
        )
        integration = Mantis(bug_system, None)

        result = self.rpc_client.Bug.report(
            self.execution_1.pk, integration.bug_system.pk
        )
        self.assertIn("bug_report_page.php", result["response"])
