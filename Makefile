MODULE := asyncio_channel
MIN_COVERAGE := 90
PYTEST_COV_ARGS := \
	--cov=$(MODULE) \
	--cov-fail-under=$(MIN_COVERAGE) \
	--no-cov-on-fail

.PHONY: install test test-cov test-cov-html test-cov-xml lint


# Install asyncio_channel module and test dependencies.
install:
	pip install --upgrade flit
	flit install --symlink --deps all

# Shortcut for running tests, just for consistency.
test:
	pytest

# Run tests and report code coverage to stdout.
test-cov:
	pytest $(PYTEST_COV_ARGS)

# Run tests and generate an html report.
test-cov-html:
	pytest $(PYTEST_COV_ARGS) --cov-report=html

# Run tests and generate an xml report.
test-cov-xml:
	pytest $(PYTEST_COV_ARGS) --cov-report=xml

lint:
	python -m flake8 $(MODULE)

