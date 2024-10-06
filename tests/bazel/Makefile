include $(dir $(MAKEFILE_LIST))../common.mk

IS_LLVM := $(if $(shell $(GCOV) --version | grep -F 'LLVM'),1,0)
GCOV_JSON_FORMAT := $(if $(shell $(GCOV) --version | grep -F 'JSON format version: 2'),1,0)

all:
	bazel build $(if $(filter $(BASE_OS),MSYS_NT MINGW64_NT),,--force_pic) $(if $(filter 1,$(IS_LLVM)),--config=clang-gcov,) --collect_code_coverage=True --test_output=all --test_env=VERBOSE_COVERAGE=1 //test:testcase

run: json

json: coverage.json coverage_bazel.json

coverage.json:
	find $(realpath $(wildcard bazel-out/*-fastbuild/bin)) -name '*.gcda' -delete
	bazel-out/*-fastbuild/bin/test/testcase
	$(GCOVR) -v --gcov-keep --json-pretty --json $@ $(if $(filter 1,$(GCOV_JSON_FORMAT)),--root /proc/self/cwd,) $(wildcard bazel-out/*-fastbuild/bin)

coverage_bazel.json: coverage.json
	find $(realpath $(wildcard bazel-out/*-fastbuild/bin)) -name '*.gcda' -delete
	$(if $(filter 1,$(IS_LLVM)),GCOV=$(word 1,$(GCOV)),) bazel coverage --instrumentation_filter=//:lib --experimental_fetch_all_coverage_outputs --test_output=all --test_env=VERBOSE_COVERAGE=1 //test:testcase
	$(GCOVR) -v --gcov-keep --json-pretty --json $@ $(if $(filter 1,$(GCOV_JSON_FORMAT)),--root /proc/self/cwd,) $(realpath $(wildcard bazel-out/*-fastbuild/testlogs))

clean:
	rm -rf bazel-*
	rm -f coverage*.json MODULE.bazel.lock
