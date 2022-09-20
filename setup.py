# pylint: disable=missing-docstring

# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from setuptools import setup, find_packages


def get_long_description():
    with open("README.rst", "r", encoding="utf-8") as file:
        return file.read()


def get_install_requires(path):
    requires = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("-r "):
                continue
            requires.append(line.strip())
        return requires


setup(
    name="kiwitcms-trackers-integration",
    version="0.2.0",
    description="Integration between Kiwi TCMS and various Issue Trackers",
    long_description=get_long_description(),
    author="Kiwi TCMS",
    author_email="info@kiwitcms.org",
    url="https://github.com/kiwitcms/trackers-integration/",
    license="GPLv3+",
    install_requires=get_install_requires("requirements.txt"),
    include_package_data=True,
    packages=find_packages(exclude=["test_project*", "*.tests"]),
    zip_safe=False,
    entry_points={
        "kiwitcms.plugins": ["kiwitcms_trackers_integration = trackers_integration"]
    },
    classifiers=[
        "Framework :: Django",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
)
