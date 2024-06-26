# Copyright (c) 2022-2023 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=wildcard-import, unused-wildcard-import
# pylint: disable=invalid-name, protected-access, wrong-import-position

import os
import sys
import pkg_resources

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# site-packages/tcms_settings_dir/ must be before ./tcms_settings_dir/
# so we can load multi_tenant.py first!
home_dir = os.path.expanduser("~")
removed_paths = []
for path in sys.path:
    if path.startswith(home_dir) and path.find("site-packages") == -1:
        removed_paths.append(path)

for path in removed_paths:
    sys.path.remove(path)

# re add them again
sys.path.extend(removed_paths)

# pretend this is a plugin during testing & development
# IT NEEDS TO BE BEFORE the wildcard import below !!!
# .egg-info/ directory will mess up with this
dist = pkg_resources.Distribution(__file__)
entry_point = pkg_resources.EntryPoint.parse(
    "trackers_integration_devel = trackers_integration", dist=dist
)
dist._ep_map = {"kiwitcms.plugins": {"trackers_integration_devel": entry_point}}
pkg_resources.working_set.add(dist)

# only useful in CI b/c Admin pages and their tests are multi-tenant aware
if int(os.getenv("CI_USE_MULTI_TENANT", "0")):
    from tcms.settings.product import *  # noqa: E402, F403
else:
    from tcms.settings.devel import *  # noqa: E402, F403

# check for a clean devel environment
if os.path.exists(os.path.join(BASE_DIR, "kiwitcms_trackers_integration.egg-info")):
    print("ERORR: .egg-info/ directories mess up plugin loading code in devel mode")
    sys.exit(1)

# these are enabled only for testing purposes
DEBUG = TEMPLATE_DEBUG = True
LOCALE_PATHS = [os.path.join(BASE_DIR, "trackers_integration", "locale")]

DATABASES[  # pylint: disable=objects-update-used, used-before-assignment
    "default"
].update(
    {
        "NAME": "test_project",
        "USER": "kiwi",
        "PASSWORD": "kiwi",
        "HOST": "localhost",
        "OPTIONS": {},
    }
)

# import the settings which automatically get distributed with this package
openproject_settings = os.path.join(
    BASE_DIR, "tcms_settings_dir", "trackers_integration.py"
)

# Kiwi TCMS loads extra settings in the same way using exec()
exec(  # pylint: disable=exec-used
    open(openproject_settings, "rb").read(),  # pylint: disable=consider-using-with
    globals(),
)

# pylint: disable=used-before-assignment
if "test_app" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS.append("test_project.test_app")  # noqa: F405

# Allows us to hook-up kiwitcms-django-plugin at will
TEST_RUNNER = os.environ.get("DJANGO_TEST_RUNNER", "django.test.runner.DiscoverRunner")
