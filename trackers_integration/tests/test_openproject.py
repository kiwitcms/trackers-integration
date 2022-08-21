# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
#
# pylint: disable=attribute-defined-outside-init

import os
import unittest

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

        self.assertEqual("Setup conference website", result["title"])
        self.assertIn("NEW TASK", result["description"])

    def test_auto_update_bugtracker(self):
        pass

    def test_report_issue_from_test_execution_1click_works(self):
        pass

    def test_report_issue_from_test_execution_empty_baseurl_exception(self):
        pass
