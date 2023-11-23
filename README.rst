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
