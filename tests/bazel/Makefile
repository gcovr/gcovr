include $(dir $(MAKEFILE_LIST))../common.mk

BASE_OS:=$(shell uname | cut -d'-' -f1)

IS_WINDOWS := $(if $(filter $(BASE_OS),MSYS_NT MINGW64_NT),1,0)
IS_DARWIN := $(if $(filter $(BASE_OS),Darwin),1,0)

IS_LLVM := $(if $(shell $(GCOV) --version | grep -F 'LLVM'),1,0)
GCOV_JSON_FORMAT := $(if $(shell $(GCOV) --version | grep -F 'JSON format version: 2'),1,0)

BAZEL_BUILD_OPTIONS := --collect_code_coverage=True --test_output=all --test_env=VERBOSE_COVERAGE=1
BAZEL_COVERAGE_OPTIONS := --instrumentation_filter=//:lib --experimental_fetch_all_coverage_outputs --test_output=all --test_env=VERBOSE_COVERAGE=1
ifeq ($(IS_WINDOWS),0)
BAZEL_BUILD_OPTIONS += --force_pic
endif
ifeq ($(IS_LLVM),1)
BAZEL_BUILD_OPTIONS += --config=clang-gcov
BAZEL_COVERAGE_OPTIONS += --config=clang-gcov
else
endif

export USE_BAZEL_VERSION := 7.4.1

all:
	$(info BASE_OS=$(BASE_OS))
	$(info IS_WINDOWS=$(IS_WINDOWS))
	$(info IS_DARWIN=$(IS_DARWIN))
	$(info $(GCOV) --version: $(shell $(GCOV) --version))
	$(info IS_LLVM=$(IS_LLVM))
	$(info GCOV_JSON_FORMAT=$(GCOV_JSON_FORMAT))
	bazel build $(BAZEL_BUILD_OPTIONS) //test:testcase

run: json

json: coverage.json coverage_bazel.json

coverage.json:
	find $(realpath $(wildcard bazel-out/*-fastbuild/bin)) -name '*.gcda' -delete
	bazel-out/*-fastbuild/bin/test/testcase
	$(GCOVR) --gcov-keep --json-pretty --json $@ $(if $(filter 1,$(GCOV_JSON_FORMAT)),--root /proc/self/cwd,) $(wildcard bazel-out/*-fastbuild/bin)

coverage_bazel.json: coverage.json
# Coverage command isn't working with MacOS in this test
ifeq ($(IS_DARWIN),1)
	echo '"Test not working"' > $@
else
	find $(realpath $(wildcard bazel-out/*-fastbuild/bin)) -name '*.gcda' -delete
	$(if $(filter 1,$(IS_LLVM)),GCOV=$(firstword $(GCOV)),) bazel coverage $(BAZEL_COVERAGE_OPTIONS) //test:testcase
	$(GCOVR) --gcov-keep --json-pretty --json $@ $(if $(filter 1,$(GCOV_JSON_FORMAT)),--root /proc/self/cwd,) $(realpath $(wildcard bazel-out/*-fastbuild/testlogs))
endif

clean:
	rm -f *.gc*
	rm -rf bazel-*
	rm -f coverage*.json MODULE.bazel.lock
