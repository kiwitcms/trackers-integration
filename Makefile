KIWI_INCLUDE_PATH="../Kiwi/"

.PHONY: checkout_kiwi
checkout_kiwi:
	if [ ! -d "$(KIWI_INCLUDE_PATH)/kiwi_lint" ]; then \
	    git clone --depth 1 https://github.com/kiwitcms/Kiwi.git $(KIWI_INCLUDE_PATH); \
	    pip install -U -r $(KIWI_INCLUDE_PATH)/requirements/devel.txt; \
	fi


.PHONY: pylint
pylint: checkout_kiwi
	PYTHONPATH=.:$(KIWI_INCLUDE_PATH) pylint \
	    --load-plugins=pylint.extensions.no_self_use \
	    --load-plugins=pylint_django --django-settings-module=test_project.settings \
	    --load-plugins=kiwi_lint -d similar-string \
	    -d missing-docstring -d duplicate-code -d module-in-directory-without-init \
	    --ignore migrations \
	    *.py tcms_settings_dir/ trackers_integration/ test_project/


.PHONY: flake8
flake8: checkout_kiwi
	flake8 *.py tcms_settings_dir/ trackers_integration/ test_project/


.PHONY: check
check: flake8 pylint
