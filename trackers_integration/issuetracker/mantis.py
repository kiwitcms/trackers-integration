# Copyright (c) 2022-2024 Alexander Todorov <atodorov@otb.bg>
# Copyright (c) 2022 @cmbahadir <c.mete.bahadir@gmail.com>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import requests

from django.conf import settings

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.templatetags.extra_filters import markdown2html
from tcms.issuetracker.base import IssueTrackerType


# this only needs to be changed during testing
_VERIFY_SSL = True


class MantisAPI:
    """
    Mantis Rest API interaction class.

    :meta private:
    """

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

    @staticmethod
    def _request(method, url, **kwargs):
        kwargs["verify"] = _VERIFY_SSL
        return requests.request(method, url, timeout=30, **kwargs).json()


class Mantis(IssueTrackerType):
    """
    .. versionadded:: 11.6-Enterprise

    Support for Mantis BT.

    .. warning::

        Make sure that this package is installed inside Kiwi TCMS and that
        ``EXTERNAL_BUG_TRACKERS`` setting contains a dotted path reference to
        this class! When using *Kiwi TCMS Enterprise* this is configured
        automatically.

    **Authentication**:

    :base_url: URL to Mantis BT installation - e.g. https://example.org/mantisbt/
    :api_password: Mantis BT API token
    """

    def _rpc_connection(self):
        (_, api_password) = self.rpc_credentials

        return MantisAPI(self.bug_system.base_url, api_password)

    def is_adding_testcase_to_issue_disabled(self):
        (_, api_password) = self.rpc_credentials

        return not (self.bug_system.base_url and api_password)

    def get_project_from_mantis(self, product_name):
        """
        Returns a Project from the Mantis BT database.
        Will try to match execution.build.version.product.name or
        ``MANTIS_PROJECT_NAME`` configuration setting! Otherwise will
        return the first project found!

        You may override this method if you want more control and customization,
        see https://kiwitcms.org/blog/tags/customization/
        """
        projects = self.rpc.get_projects()["projects"]
        for project in projects:
            if project["name"].lower() == product_name.lower():
                return project

        return projects[0]

    def get_category_from_mantis(
        self, category_name, project
    ):  # pylint: disable=no-self-use, unused-argument
        """
        Returns a Category from the Mantis BT database.
        Will try to match ``MANTIS_CATEGORY_NAME`` configuration setting!
        Otherwise will return "General"!

        .. warning ::

            At present Mantis BT doesn't appear to provide API methods for
            creating or listing available categories inside a project. Because
            of that this method will always return the "General" category!
        """
        return {"name": category_name}

    def _report_issue(self, execution, user):
        """
        Mantis creates the Issue with Title
        """
        try:
            project = self.get_project_from_mantis(
                getattr(
                    settings,
                    "MANTIS_PROJECT_NAME",
                    execution.build.version.product.name,
                )
            )
            category = self.get_category_from_mantis(
                getattr(settings, "MANTIS_CATEGORY_NAME", "General"),
                project,
            )

            issue = self.rpc.create_issue(
                f"Failed test: {execution.case.summary}",
                markdown2html(self._report_comment(execution, user)),
                category["name"],
                project["name"],
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

    def post_comment(self, execution, bug_id):
        self.rpc.add_comment(bug_id, markdown2html(self.text(execution)))

    def details(self, url):
        """
        Return issue details from Mantis
        """
        issue = self.rpc.get_issue(self.bug_id_from_url(url))
        return {
            "id": issue["id"],
            "description": issue["description"],
            "status": issue["status"]["name"],
            "title": issue["summary"],
            "url": url,
        }
