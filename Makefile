KIWI_INCLUDE_PATH="../Kiwi/"

.PHONY: test
test:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	    pip install -U -r $(KIWI_INCLUDE_PATH)/requirements/base.txt; \
	fi

	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) EXECUTOR=standard PYTHONWARNINGS=d AUTO_CREATE_SCHEMA='' \
        KIWI_TENANTS_DOMAIN='test.com' \
	    coverage run --include "*/*.py" \
	                 --omit "*/tests/*.py" \
	                 ./manage.py test -v2

	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) EXECUTOR=standard PYTHONWARNINGS=d AUTO_CREATE_SCHEMA='' \
        KIWI_TENANTS_DOMAIN='' \
	    ./manage.py check 2>&1 | grep "KIWI_TENANTS_DOMAIN environment variable is not set!"


.PHONY: pylint
pylint:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	    pip install -U -r $(KIWI_INCLUDE_PATH)/requirements/base.txt; \
	fi

	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) pylint \
	    --load-plugins=pylint.extensions.no_self_use \
	    --load-plugins=pylint_django --django-settings-module=test_project.settings \
	    --load-plugins=kiwi_lint -d similar-string \
	    -d missing-docstring -d duplicate-code -d module-in-directory-without-init \
	    --ignore migrations \
	    *.py tcms_settings_dir/ tcms_openproject/ test_project/


.PHONY: flake8
flake8:
	flake8 *.py tcms_settings_dir/ tcms_openproject/ test_project/


.PHONY: check
check: flake8 pylint test_for_missing_migrations test
