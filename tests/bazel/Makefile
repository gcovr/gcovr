include $(dir $(MAKEFILE_LIST))../common.mk

all:
	bazel build $(if $(filter $(BASE_OS),MSYS_NT MINGW64_NT),,--force_pic) --collect_code_coverage=True --test_output=all --test_env=VERBOSE_COVERAGE=1 //test:testcase

run: json

json: coverage.json

# No LLVM based gcov
ifeq ($(filter $(shell $(GCOV) --version),LLVM),)
json: coverage_bazel.json
endif

coverage.json:
	find $(realpath $(wildcard bazel-out/*-fastbuild/bin)) -name '*.gcda' -delete
	bazel-out/*-fastbuild/bin/test/testcase
	$(GCOVR) -v --gcov-keep --json-pretty --json $@ $(wildcard bazel-out/*-fastbuild/bin)

coverage_bazel.json: coverage.json
	find $(realpath $(wildcard bazel-out/*-fastbuild/bin)) -name '*.gcda' -delete
	bazel coverage --instrumentation_filter=//:lib --experimental_fetch_all_coverage_outputs --test_output=all --test_env=VERBOSE_COVERAGE=1 //test:testcase
	$(GCOVR) -v --gcov-keep --json-pretty --json $@ $(realpath $(wildcard bazel-out/*-fastbuild/testlogs))

clean:
	rm -rf bazel-*
	rm -f coverage*.json MODULE.bazel.lock
