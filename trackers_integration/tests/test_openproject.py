# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
#
# pylint: disable=attribute-defined-outside-init

from django.utils import timezone

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem
from tcms.tests.factories import ComponentFactory, TestExecutionFactory

from trackers_integration.issuetracker import OpenProject


class TestOpenProjectIntegration(APITestCase):
    existing_bug_id = 8
    existing_bug_url = (
        "http://bugtracker.kiwitcms.org/projects/demo-project/work_packages/8/activity"
    )

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_1.case.summary = "Tested at " + timezone.now().isoformat()
        self.execution_1.case.text = "Given-When-Then"
        self.execution_1.case.save()  # will generate history object
        self.execution_1.run.summary = (
            "Automated TR for OpenProject integration on " + timezone.now().isoformat()
        )
        self.execution_1.run.save()

        self.component = ComponentFactory(
            name="OpenProject integration", product=self.execution_1.run.plan.product
        )
        self.execution_1.case.add_component(self.component)

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="OpenProject for kiwitcms/trackers-integration",
            tracker_type="trackers_integration.issuetracker.OpenProject",
            base_url="http://bugtracker.kiwitcms.org",
            api_password="26210315639327b10b56b7ef5d2f47f843c0ced3bafd1540fd4ecb30a06fa80f",
        )
        self.integration = OpenProject(bug_system, None)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

    def test_details(self):
        result = self.integration.details(self.existing_bug_url)

        self.assertEqual("NEW TASK: Setup conference website", result["title"])
        self.assertEqual("", result["description"])

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

        self.assertEqual(
            f"Failed test: {self.execution_1.case.summary}",
            issue["subject"],
        )
        for expected_string in [
            f"Filed from execution {self.execution_1.get_full_url()}",
            "Reporter",
            self.execution_1.run.plan.product.name,
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

    def test_report_issue_from_test_execution_empty_baseurl_exception(self):
        pass
