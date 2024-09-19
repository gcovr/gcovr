
CFLAGS := -fPIC -fprofile-arcs -ftest-coverage $(if $(shell $(CC) --help --verbose 2>&1 | grep -F "condition-coverage"),-fcondition-coverage,)
CXXFLAGS := $(CFLAGS)

GCOV ?= gcov
