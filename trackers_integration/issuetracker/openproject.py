# Copyright (c) 2022-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import json
import re
from urllib.parse import urlencode

import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker import base


RE_MATCH_INT = re.compile(r"work_packages/([\d]+)(/activity)*$")


class API:
    """
    :meta private:
    """

    def __init__(self, base_url=None, password=None):
        self.auth = HTTPBasicAuth("apikey", password)
        self.base_url = f"{base_url}/api/v3"

    def get_workpackage(self, issue_id):
        url = f"{self.base_url}/work_packages/{issue_id}"
        return self._request("GET", url, auth=self.auth)

    def create_workpackage(self, project_id, body):
        headers = {"Content-type": "application/json"}
        url = f"{self.base_url}/projects/{project_id}/work_packages"
        return self._request("POST", url, headers=headers, auth=self.auth, json=body)

    def get_comments(self, issue_id):
        url = f"{self.base_url}/work_packages/{issue_id}/activities"
        return self._request("GET", url, auth=self.auth)

    def add_comment(self, issue_id, body):
        headers = {"Content-type": "application/json"}
        url = f"{self.base_url}/work_packages/{issue_id}/activities"
        return self._request("POST", url, headers=headers, auth=self.auth, json=body)

    @staticmethod
    def _request(method, url, **kwargs):
        result = requests.request(method, url, timeout=30, **kwargs).json()
        if result.get("_type", "not-an-error").lower() == "error":
            raise RuntimeError(result.get("message", "API error"))

        return result

    def get_projects(self, name=None):
        url = f"{self.base_url}/projects"
        if name:
            params = urlencode(
                {
                    "filters": json.dumps(
                        [
                            {
                                "name_and_identifier": {
                                    "operator": "~",
                                    "values": [name],
                                }
                            }
                        ]
                    )
                },
                True,
            )
            url += f"?{params}"
        return self._request("GET", url, auth=self.auth)

    def get_workpackage_types(self, project_id):
        url = f"{self.base_url}/projects/{project_id}/types"
        return self._request("GET", url, auth=self.auth)


class OpenProject(base.IssueTrackerType):
    """
    .. versionadded:: 11.6-Enterprise

    Support for `OpenProject <https://www.openproject.org/>`_ - open source
    project management software.

    .. warning::

        Make sure that this package is installed inside Kiwi TCMS and that
        ``EXTERNAL_BUG_TRACKERS`` setting contains a dotted path reference to
        this class! When using *Kiwi TCMS Enterprise* this is configured
        automatically.

    **Authentication**:

    :base_url: URL to OpenProject instance - e.g. https://kiwitcms.openproject.com/
    :api_password: API token
    """

    def _rpc_connection(self):
        (_, api_password) = self.rpc_credentials

        return API(self.bug_system.base_url, api_password)

    def is_adding_testcase_to_issue_disabled(self):
        """
        :meta private:
        """
        (_, api_password) = self.rpc_credentials

        return not (self.bug_system.base_url and api_password)

    @classmethod
    def bug_id_from_url(cls, url):
        """
        Returns a WorkPackage ID from a URL of the form
        ``[projects/short-identifier]/work_packages/1234[/activity]``
        """
        return int(RE_MATCH_INT.search(url.strip()).group(1))

    def get_project_by_name(self, name):
        """
        Return a Project which matches the product name from Kiwi TCMS
        for which we're reporting bugs!

        .. important::

            Name search is done via the OpenProject API and will try to match
            either name or project identifier. In case multiple matches were found
            the first one will be returned!

            If there is no match by name return the first of all projects in the
            OpenProject database!
        """
        try:
            projects = self.rpc.get_projects(name)

            # nothing would be found, default to 1st project
            if not projects["_embedded"]["elements"]:
                projects = self.rpc.get_projects()

            return projects["_embedded"]["elements"][0]
        except Exception as err:
            raise RuntimeError("Project not found") from err

    def get_workpackage_type(self, project_id, name):
        """
        Return a WorkPackage type matching by name, defaults to ``Bug``.
        If there is no match then return the first one!

        Can be controlled via the ``OPENPROJECT_WORKPACKAGE_TYPE_NAME``
        configuration setting!
        """
        try:
            types = self.rpc.get_workpackage_types(project_id)
            for _type in types["_embedded"]["elements"]:
                if _type["name"].lower() == name.lower():
                    return _type

            return types["_embedded"]["elements"][0]
        except Exception as err:
            raise RuntimeError("WorkPackage Type not found") from err

    def _report_issue(self, execution, user):
        project = self.get_project_by_name(execution.build.version.product.name)
        project_id = project["id"]
        project_identifier = project["identifier"]

        _type = self.get_workpackage_type(
            project_id, getattr(settings, "OPENPROJECT_WORKPACKAGE_TYPE_NAME", "Bug")
        )

        arguments = {
            "subject": f"Failed test: {execution.case.summary}",
            "description": {"raw": self._report_comment(execution, user)},
            "_links": {
                "type": _type["_links"]["self"],
            },
        }

        new_issue = self.rpc.create_workpackage(project_id, arguments)
        _id = new_issue["id"]
        new_url = f"{self.bug_system.base_url}/projects/{project_identifier}/work_packages/{_id}"

        # and also add a link reference that will be shown in the UI
        LinkReference.objects.get_or_create(
            execution=execution,
            url=new_url,
            is_defect=True,
        )

        return (new_issue, new_url)

    def post_comment(self, execution, bug_id):
        comment_body = {"comment": {"raw": self.text(execution)}}
        self.rpc.add_comment(bug_id, comment_body)

    def details(self, url):
        """
        Fetches WorkPackage details from OpenProject to be displayed in tooltips.
        """
        issue_id = self.bug_id_from_url(url)
        issue = self.rpc.get_workpackage(issue_id)
        issue_type = issue["_embedded"]["type"]["name"].upper()
        status = issue["_embedded"]["status"]["name"].upper()
        return {
            "id": issue_id,
            "description": issue["description"]["raw"],
            "status": status,
            "title": f"{issue_type}: " + issue["subject"],
            "url": url,
        }
