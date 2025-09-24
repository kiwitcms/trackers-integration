# Copyright (c) 2022-2024 Alexander Todorov <atodorov@otb.bg>
# Copyright (c) 2025 Frank Sommer <Frank.Sommer@sherpa-software.de>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import http
import time
from requests import Session
from requests.auth import HTTPBasicAuth

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker.base import IssueTrackerType

# pylint: disable=too-few-public-methods
class TracAPI:
    """
    :meta private:
    Proxy class for Trac ticket JSON-RPC interface.
    Trac server must have plugin trac-ticketrpc installed (https://pypi.org/project/trac-ticketrpc)
    """

    def __init__(self, base_url: str = None, api_username: str = None, api_password: str = None):
        """
        Constructor.
        :param base_url: base URL to Trac server from Kiwi settings
        :param api_username: username for Trac login
        :param api_password: password for Trac login
        """
        self.__base_url = base_url
        self.__headers = {
            'Accept': 'application/json',
            'Content-type': 'application/json',
        }
        self.__auth = HTTPBasicAuth(api_username, api_password)

    def invoke_method(self, method: str, args: dict) -> dict:
        """
        Send request to Trac server and return response.
        As advised by JSON-RPC specification all calls are made using HTTP method 'POST'.
        :param method: JSON-RPC method to call
        :param args: arguments for JSON-RPC method
        :return: response from Trac server
        """
        project = args.get('project')
        session = Session()
        # visit Trac project's login URL first to get session cookie, otherwise JSON-RPC plugin
        # in Trac cannot determine permissions
        url = f'{self.__base_url}/{project}/login'
        resp = session.get(url, timeout=30, auth=self.__auth)
        if resp.status_code != http.HTTPStatus.OK:
            return {'error': f'{resp.status_code}: {resp.reason}'}
        # now invoke RPC method on Trac server
        url = f'{self.__base_url}/{project}/ticketrpc'
        req = {'jsonrpc': '2.0', 'method': method, 'params': args, 'id': str(time.time_ns())}
        resp = session.post(url, timeout=30, headers=self.__headers, auth=self.__auth, json=req)
        rc = resp.status_code
        return resp.json() if rc == http.HTTPStatus.OK else {'error': f'{rc}: {resp.reason}'}


class Trac(IssueTrackerType):
    """
    .. versionadded:: 14.5-Enterprise

    Support for `Trac <https://trac.edgewall.org/>`_ - open source
    issue tracking system, version 1.6 and above.
    Project name in Trac must match product name in Kiwi TCMS.

    .. warning::

        Make sure that this package is installed inside Kiwi TCMS and that
        ``EXTERNAL_BUG_TRACKERS`` setting contains a dotted path reference to
        this class! When using *Kiwi TCMS Enterprise* this is configured
        automatically.

    **Authentication**:

    :base_url: URL to Trac instance - e.g. https://trac.myserver.local/
    :api_username: Trac Username - needs Trac permissions TICKET_CREATE, TICKET_APPEND, TICKET_VIEW
    :api_password: Trac Password
    """

    def _rpc_connection(self):
        user, password = self.rpc_credentials
        return TracAPI(self.bug_system.base_url, user, password)

    def is_adding_testcase_to_issue_disabled(self):
        user, password = self.rpc_credentials
        return not (self.bug_system.base_url and user and password)

    def _report_issue(self, execution, _user):
        """
        Create Trac ticket.
        :param execution: test execution data
        :param _user: current TCMS user
        :return: Response from Trac server, issue ID
        """
        product = execution.build.version.product.name
        try:
            version = execution.build.version.value
            summary = f'Failed test: {execution.case.summary}'
            description = execution.case.get_text_with_version(execution.case_text_version)
            ticket = {
                'type': 'defect',
                'priority': 'major',
                'summary': summary,
                'description': description,
                'project': product,
                'version': version,
                'component': product,
            }
            result = self.rpc.invoke_method('ticket.create', ticket)
            issue = result.get('result')
            if issue is None:
                raise RuntimeError(result.get('error'))
            issue_id = issue.get('id')
            issue_url = f'{self.bug_system.base_url}/{product}/ticket/{issue_id}'
            # add a link reference that will be shown in the UI
            LinkReference.objects.get_or_create(
                execution=execution,
                url=issue_url,
                is_defect=True,
            )
            return Trac._filtered_trac_ticket_data(issue, issue_url), issue_url
        except Exception:  # pylint: disable=broad-except
            # something above didn't work so return a link for manually
            # entering issue details with info pre-filled
            return None, f'{self.bug_system.base_url}/{product}/newticket'

    def post_comment(self, execution, bug_id):
        try:
            params = {
                'text': self.text(execution),
                'id': bug_id,
                'project': execution.build.version.product.name,
            }
            result = self.rpc.invoke_method('ticket.add_comment', params)
            comment = result.get('result')
            if comment is None:
                raise RuntimeError(result.get('error'))
            return comment
        except Exception as _e:  # pylint: disable=broad-except
            return {'error': str(_e)}

    def details(self, url: str) -> dict:
        """
        Return issue details from Trac.
        :param url: Trac ticket URL, e.g. https://trac.myserver.local/myproject/ticket/123
        :return: issue details
        """
        try:
            ticket_id, project = Trac._bug_info_from_url(url)
            params = {
                'id': ticket_id,
                'project': project
            }
            result = self.rpc.invoke_method('ticket.details', params)
            details = result.get('result')
            if details is None:
                raise RuntimeError(result.get('error'))
            return Trac._filtered_trac_ticket_data(details, url)
        except Exception as _e:  # pylint: disable=broad-except
            return {'error': str(_e)}

    @classmethod
    def _filtered_trac_ticket_data(cls, ticket_data: dict, url: str) -> dict:
        """
        :param ticket_data: Trac ticket data as returned from Trac server
        :param url: Trac ticket URL
        :return: essential Trac ticket data
        """
        return {
            'id': ticket_data.get('id'),
            'title': ticket_data.get('summary'),
            'description': ticket_data.get('description'),
            'status': ticket_data.get('status'),
            'url': url,
        }

    @classmethod
    def _bug_info_from_url(cls, url: str) -> tuple[str, str]:
        """
        Extracts project and ticket id from Trac URL.
        :param url: Trac ticket URL, e.g. https://trac.myserver.local/myproject/ticket/123
        :return: project (e.g. myproject) and ticket id (e.g. 123)
        """
        url_parts = url.rstrip('/').split('/')
        if len(url_parts) < 3:
            raise RuntimeError(f'Invalid Trac ticket URL: {url}')
        return url_parts[-1], url_parts[-3]
