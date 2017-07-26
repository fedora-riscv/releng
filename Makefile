PYTHON=python3
PEP8=$(PYTHON)-pep8
COVERAGE=coverage
ifeq ($(PYTHON),python3)
  COVERAGE=coverage3
endif

TEST_DEPENDENCIES = python3-pep8 python3-pocketlint
TEST_DEPENDENCIES += python3-koji fedora-cert packagedb-cli
TEST_DEPENDENCIES += python3-fedmsg-core python3-configparser
TEST_DEPENDENCIES := $(shell echo $(sort $(TEST_DEPENDENCIES)) | uniq)

check-requires:
	@echo "*** Checking if the dependencies required for testing and analysis are available ***"
	@status=0 ; \
	for pkg in $(TEST_DEPENDENCIES) ; do \
		test_output="$$(rpm -q --whatprovides "$$pkg")" ; \
		if [ $$? != 0 ]; then \
			echo "$$test_output" ; \
			status=1 ; \
		fi ; \
	done ; \
	exit $$status

install-requires:
	@echo "*** Installing the dependencies required for testing and analysis ***"
	dnf install -y $(TEST_DEPENDENCIES)

test: check-requires
	@echo "*** Running unittests with $(PYTHON) ***"
	PYTHONPATH=.:scripts/:$(PYTHONPATH) $(PYTHON) -m unittest discover -v -s tests/ -p '*_test.py'

coverage: check-requires
	@echo "*** Running unittests with $(COVERAGE) for $(PYTHON) ***"
	PYTHONPATH=.:tests/ $(COVERAGE) run --branch -m unittest discover -v -s tests/ -p '*_test.py'
	$(COVERAGE) report --include="scripts/*" --show-missing
	$(COVERAGE) report --include="scripts/*" > coverage-report.log

pylint: check-requires
	@echo "*** Running pylint ***"
	PYTHONPATH=.:tests/:$(PYTHONPATH) tests/pylint/runpylint.py

pep8: check-requires
	@echo "*** Running pep8 compliance check ***"
	$(PEP8) --ignore=E501,E402,E731 tests/ scripts/ > pep8.log

check:
	@status=0; \
	$(MAKE) pylint || status=1; \
	$(MAKE) pep8 || status=1; \
	exit $$status

flake8:
	@echo "*** Running flake8 against push-two-week-atomic only ***"
	flake8-2 --ignore=W503,E131,E501,E226,E302,E265,E303 scripts/push-two-week-atomic.py

ci: check coverage

.PHONY: check pylint pep8 test
