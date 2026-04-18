# Copyright (c) 2022-2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

SHELL = /bin/bash
KIWI_INCLUDE_PATH="../Kiwi/"

.PHONY: checkout_kiwi
checkout_kiwi:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	    pushd $(KIWI_INCLUDE_PATH); \
	    pip install -U -r requirements/devel.txt; \
	    pushd tcms/; \
	    npm install --dev; \
	    ./node_modules/.bin/webpack; \
	    popd; \
	    popd; \
	fi


.PHONY: pylint
pylint: checkout_kiwi
	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) DJANGO_SETTINGS_MODULE="test_project.settings" pylint \
	    --load-plugins=pylint.extensions.no_self_use \
	    --load-plugins=pylint_django --django-settings-module=test_project.settings \
	    --load-plugins=kiwi_lint -d similar-string \
	    -d missing-docstring -d duplicate-code -d module-in-directory-without-init \
	    --ignore migrations \
	    *.py tcms_settings_dir/ trackers_integration/ test_project/


.PHONY: flake8
flake8: checkout_kiwi
	flake8 *.py tcms_settings_dir/ trackers_integration/


.PHONY: check
check: flake8 pylint

.PHONY: messages
messages: checkout_kiwi
	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) CI_USE_MULTI_TENANT=1 KIWI_TENANTS_DOMAIN='test.com' \
	    ./manage.py makemessages --locale en --no-obsolete --no-vinaigrette --ignore "test*.py"
	ls trackers_integration/locale/*/LC_MESSAGES/*.po | xargs -n 1 -I @ msgattrib -o @ --no-fuzzy @


.PHONY: package
package:
	rm -rf build/ dist/ kiwitcms_*.egg-info/
	python setup.py sdist
	python setup.py bdist_wheel
	twine check dist/*

.PHONY: upload
upload: package
	test -n "$(TWINE_USERNAME)" || exit 1
	test -n "$(TWINE_PASSWORD)" || exit 2
	twine upload dist/* --repository-url https://push.fury.io/kiwitcms
