# This Makefile helps perform some developer tasks, like linting or testing.
# Run `make` or `make help` to see a list of tasks.

# Set a variable if it's empty or provided by `make`.
# usage: $(call set_sensible_default, NAME, value)
set_sensible_default = $(if $(filter undefined default,$(origin $(1))),$(2),$(value $(1)))

PYTHON := $(call set_sensible_default,PYTHON,python3)
CC := $(call set_sensible_default,CC,gcc-5)
CXX := $(call set_sensible_default,CXX,g++-5)
GCOV := $(call set_sensible_default,GCOV,gcov-5)
QA_CONTAINER ?= gcovr-qa
TEST_OPTS ?=

.PHONY: help setup-dev qa lint test doc docker-qa docker-qa-build

help:
	@echo "select one of the following targets:"
	@echo "  help       print this message"
	@echo "  setup-dev  prepare a development environment"
	@echo "  qa         run all QA tasks (lint, test, doc)"
	@echo "  lint       run the flake8 linter"
	@echo "  test       run all tests"
	@echo "  doc        render the docs"
	@echo "  docker-qa  run qa in the docker container"
	@echo "  docker-qa-build"
	@echo "             build the qa docker container"
	@echo ""
	@echo "environment variables:"
	@echo "  PYTHON     Python executable to use [current: $(PYTHON)]"
	@echo "  CC, CXX, GCOV"
	@echo "             the gcc version to use [current: CC=$(CC) CXX=$(CXX) GCOV=$(GCOV)]"
	@echo "  TEST_OPTS  additional flags for pytest [current: $(TEST_OPTS)]"
	@echo "  QA_CONTAINER"
	@echo "             tag for the qa docker container [current: $(QA_CONTAINER)]"

setup-dev:
	$(PYTHON) -m pip install -r requirements.txt -r doc/requirements.txt
	$(PYTHON) -m pip install -e .

qa: lint test doc

lint:
	find ./* -type f -name '*.py' -exec $(PYTHON) -m flake8 --ignore=E501,W503 -- {} +

test:
	CC=$(CC) CXX=$(CXX) GCOV=$(GCOV) $(PYTHON) -m pytest -v --doctest-modules $(TEST_OPTS) -- gcovr doc/examples

doc:
	cd doc && make html O=-W

docker-qa: export TEST_OPTS := $(TEST_OPTS)

docker-qa: | docker-qa-build
	docker run --rm -e TEST_OPTS -v `pwd`:/gcovr $(QA_CONTAINER)

docker-qa-build: admin/Dockerfile.qa requirements.txt doc/requirements.txt
	docker build --tag $(QA_CONTAINER) --file admin/Dockerfile.qa .
