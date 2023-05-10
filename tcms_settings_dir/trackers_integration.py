# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=undefined-variable

for module_name in (
    "trackers_integration.issuetracker.OpenProject",
    "trackers_integration.issuetracker.Mantis",
):
    if module_name not in EXTERNAL_BUG_TRACKERS:  # noqa: F821
        EXTERNAL_BUG_TRACKERS.append(module_name)  # noqa: F821
