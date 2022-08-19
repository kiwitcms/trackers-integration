# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import requests
from django.conf import settings
from requests.auth import HTTPBasicAuth

from tcms.issuetracker import base


class API:
    def __init__(self, base_url=None, password=None):
        self.headers = {
            "Accept": "application/json-patch+json",
            "Content-type": "application/json-patch+json",
        }
        self.auth = HTTPBasicAuth("apikey", password)
        self.base_url = base_url + "/_apis/"

    def get_issue(self, issue_id):
        url = f"{self.base_url}....."
        return self._request("GET", url, headers=self.headers, auth=self.auth)

    def create_issue(self, body):
        raise NotImplementedError

    def update_issue(self, issue_id, body):
        raise NotImplementedError

    def get_comments(self, issue_id):
        raise NotImplementedError

    def add_comment(self, issue_id, body):
        raise NotImplementedError

    def delete_comment(self, issue_id, comment_id):
        raise NotImplementedError

    @staticmethod
    def _request(method, url, **kwargs):
        return requests.request(method, url, **kwargs).json()


class ThreadRunner(base.IntegrationThread):
    def post_comment(self):
        comment_body = {"text": markdown2html(self.text())}
        self.rpc.add_comment(self.bug_id, comment_body)


class OpenProject(base.IssueTrackerType):
    """
    Support for OpenProject. Requires:

    :base_url: URL to OpenProject instance - e.g. https://kiwitcms.openproject.com/
    :api_password: API token

    .. note::

        You can leave the ``api_url`` and ``api_username`` fields blank because
        the integration code doesn't use them!
    """

    it_class = ThreadRunner

    def _rpc_connection(self):
        return API(self.bug_system.base_url, self.bug_system.api_password)

    def is_adding_testcase_to_issue_disabled(self):
        return not (self.bug_system.base_url and self.bug_system.api_password)

    def _report_issue(self, execution, user):
        raise NotImplementedError

    def details(self, url):
        raise NotImplementedError