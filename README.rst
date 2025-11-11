Extra Issue Tracker integration for Kiwi TCMS
=============================================

.. image:: https://pyup.io/repos/github/kiwitcms/trackers-integration/shield.svg
    :target: https://pyup.io/repos/github/kiwitcms/trackers-integration/
    :alt: Python updates

.. image:: https://opencollective.com/kiwitcms/tiers/sponsor/badge.svg?label=sponsors&color=brightgreen
   :target: https://opencollective.com/kiwitcms#contributors
   :alt: Become a sponsor

.. image:: https://img.shields.io/twitter/follow/KiwiTCMS.svg
    :target: https://twitter.com/KiwiTCMS
    :alt: Kiwi TCMS on Twitter


Introduction
------------

This package provides extra integration between Kiwi TCMS and
various Issue Trackers.

Changelog
---------

v1.2.1 (11 Nov 2025)
~~~~~~~~~~~~~~~~~~~~


- Add support for Trac bugtracker (Frank Sommer). Closes
  `Issue #834 <https://github.com/kiwitcms/Kiwi/issues/834>`_
- Add link to documentation for Personal API tokens admin page
- Update for Django 5.2 compatibility


v1.1.0 (08 Nov 2024)
~~~~~~~~~~~~~~~~~~~~

- Bug details integration code now returns the additional fields
  `id`, `status` and `url` alongside the existing ones
  `description` and `title`!


v1.0.0 (13 Jun 2024)
~~~~~~~~~~~~~~~~~~~~

- Relicense this package under GNU Affero General Public License v3 or later
- Prior versions are still licensed under GNU General Public License v3
- Remove the ability to set category when opening a new issue in OpenProject
  b/c of missing relicense permission


v0.7.0 (14 Jan 2024)
~~~~~~~~~~~~~~~~~~~~

- 1-click bug report will now use ``execution.build.version.product`` instead
  of ``execution.run.plan.product`` following changes in Kiwi TCMS, see:
  https://github.com/kiwitcms/Kiwi/commit/48a33a71e664c8c3ed2ceb298b5f1e19d0bddb52
  and `PR #3439 <https://github.com/kiwitcms/Kiwi/pull/3439>`_ for more details
- Fix typo in markdown
- Build & test with Python 3.11
- Test with psycopg3


v0.6.0 (23 Nov 2023)
~~~~~~~~~~~~~~~~~~~~

- Automatically set category when opening a new issue in OpenProject
  if the category matches ``execution.case.category.name`` (Stefan Weinberg)
- Use raw text instead of HTML for OpenProject bug details popover. Closes
  `Issue #38 <https://github.com/kiwitcms/trackers-integration/issues/38>`_
- Add a new ``ApiToken`` model to the database. It can be used to provide
  personal API tokens for bug-tracker integrations
- Make use of the new ``IssueTracker.rpc_credentials`` property
  introduced in Kiwi TCMS v12.6
- Start testing with Python 3.9
- Start testing against OpenProject v13
- Start testing against MantisBT 2.26.0


v0.5.0 (6 Jun 2023)
~~~~~~~~~~~~~~~~~~~

- Fix typo in module name listed in settings. Closes
  `Issue #34 <https://github.com/kiwitcms/trackers-integration/issues/34>`_
  (Stefan Weiberg)


v0.4.0 (16 Feb 2023)
~~~~~~~~~~~~~~~~~~~~

- Remove IntegrationThread classes due to refactoring in Kiwi TCMS 12.1


v0.3.0 (13 Oct 2022)
~~~~~~~~~~~~~~~~~~~~

- Add support for Mantis BT with contributions from
  `@cmbahadir <https://github.com/cmbahadir>`_


v0.2.0 (20 Sep 2022)
~~~~~~~~~~~~~~~~~~~~

- Initial release
- Support for OpenProject
