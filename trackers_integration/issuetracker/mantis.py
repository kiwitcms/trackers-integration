# -*- coding: utf-8 -*-
import requests

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.templatetags.extra_filters import markdown2html
from tcms.issuetracker.base import IntegrationThread, IssueTrackerType


class MantisAPI:
    """
    Mantis Rest API interaction class.

    :meta private:
    """

    _verify_ssl = True

    def __init__(self, base_url=None, api_token=None):
        self.headers = {
            "Accept": "application/json-patch+json",
            "Content-type": "application/json-patch+json",
            "Authorization": api_token,
        }
        self.base_url = f"{base_url}/api/rest"

    def get_projects(self):
        url = f"{self.base_url}/projects"
        return self._request("GET", url, headers=self.headers)

    def create_project(
        self, name, description="", status="development", is_public=True
    ):
        url = f"{self.base_url}/projects"

        # these seem to be hard-coded and API docs don't show any methods
        # related to Project Status
        statuses = {
            "development": {"id": 10, "name": "development", "label": "development"},
            "release": {"id": 30, "name": "release", "label": "release"},
            "stable": {"id": 50, "name": "stable", "label": "stable"},
            "obsolete": {"id": 70, "name": "obsolete", "label": "obsolete"},
        }

        # these seem to be hard-coded and API docs don't show any methods
        # related to Project View State
        view_states = {
            True: {"id": 10, "name": "public", "label": "public"},
            False: {"id": 50, "name": "private", "label": "private"},
        }

        payload = {
            "name": name,
            "status": statuses[status],
            "description": description,
            "enabled": True,
            "view_state": view_states[is_public],
        }
        return self._request("POST", url, headers=self.headers, json=payload)["project"]

    def get_issue(self, issue_id):
        url = f"{self.base_url}/issues/{issue_id}"
        return self._request("GET", url, headers=self.headers)["issues"][0]

    def create_issue(self, summary, description, category_name, project_name):
        url = f"{self.base_url}/issues/"
        body = {
            "summary": summary,
            "description": description,
            "category": {"name": category_name},
            "project": {"name": project_name},
        }
        return self._request("POST", url, headers=self.headers, json=body)["issue"]

    def update_issue(self, issue_id, body):
        url = f"{self.base_url}/issues/{issue_id}"
        return self._request("PATCH", url, headers=self.headers, json=body)

    def close_issue(self, issue_id):
        self.update_issue(issue_id, {"status": {"name": "closed"}})

    def get_comments(self, issue_id):
        issue = self.get_issue(issue_id)
        if "notes" in issue:
            return issue["notes"]

        return []

    def add_comment(self, issue_id, text):
        url = f"{self.base_url}/issues/{issue_id}/notes"
        body = {
            "text": text,
        }
        return self._request("POST", url, headers=self.headers, json=body)

    def delete_comment(self, issue_id, note_id):
        url = f"{self.base_url}/issues/{issue_id}/notes/{note_id}"
        return self._request("DELETE", url, headers=self.headers)

    def _request(self, method, url, **kwargs):
        kwargs["verify"] = self._verify_ssl
        return requests.request(method, url, timeout=30, **kwargs).json()


class MantisThread(IntegrationThread):
    """
    Execute Mantis code in a thread!

    Executed from the IssueTracker interface methods.

    :meta private:
    """

    def post_comment(self):
        self.rpc.add_comment(self.bug_id, markdown2html(self.text()))


class Mantis(IssueTrackerType):
    """
    .. versionadded:: 11.6-Enterprise

    Support for Mantis. Requires:

    :base_url: URL to Mantis Server - e.g. https://mantisbt.org
    :api_password: Mantis API token

    .. note::
        You can leave the ``api_username`` field blank since
        those are not used by issue tracker!
    """

    it_class = MantisThread

    def _rpc_connection(self):
        return MantisAPI(self.bug_system.base_url, self.bug_system.api_password)

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.bug_system.base_url and self.bug_system.api_password)

    def get_project_from_mantis(self, execution):
        """
        Returns the project from the actual Mantis instance.
        Will try to match execution.run.plan.product.name, otherwise will
        return the first found!

        You may override this method if you want more control and customization,
        see https://kiwitcms.org/blog/tags/customization/
        """
        projects = self.rpc.get_projects()["projects"]
        try:
            project = next(
                project
                for project in projects
                if project["name"] == execution.run.plan.product.name
            )
            return project["name"]
        except StopIteration:
            return projects[0]["name"]

    def _report_issue(self, execution, user):
        """
        Mantis creates the Issue with Title
        """
        try:
            project_name = self.get_project_from_mantis(execution)

            issue = self.rpc.create_issue(
                f"Failed test: {execution.case.summary}",
                markdown2html(self._report_comment(execution, user)),
                "General",
                project_name,
            )

            issue_url = f"{self.bug_system.base_url}/view.php?id={issue['id']}"
            # add a link reference that will be shown in the UI
            LinkReference.objects.get_or_create(
                execution=execution,
                url=issue_url,
                is_defect=True,
            )

            return (issue, issue_url)
        except Exception:  # pylint: disable=broad-except
            # something above didn't work so return a link for manually
            # entering issue details with info pre-filled
            url = self.bug_system.base_url
            if not url.endswith("/"):
                url += "/"

            return (None, f"{url}bug_report_page.php")

    def details(self, url):
        """
        Return issue details from Mantis
        """
        issue = self.rpc.get_issue(self.bug_id_from_url(url))
        return {
            "title": issue["summary"],
            "description": issue["description"],
        }
