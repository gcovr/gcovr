import os
import shutil

import pytest

from tests.conftest import IS_DARWIN, IS_GCC, IS_WINDOWS, GcovrTestExec

BAZEL = shutil.which("bazel")


def build_bazel_example(gcovr_test_exec: "GcovrTestExec") -> dict[str, str]:
    """Build the bazel example to verify that bazel is working."""
    bazel_build_options = [
        "--collect_code_coverage=True",
        "--test_output=all",
        "--test_env=VERBOSE_COVERAGE=1",
    ]
    if not gcovr_test_exec.is_windows():
        bazel_build_options.append("--force_pic")
    if gcovr_test_exec.is_llvm():
        bazel_build_options.append("--config=clang-gcov")

    env = os.environ.copy()
    env.update(
        {
            "USE_BAZEL_VERSION": "7.4.1",
            "GCOV": gcovr_test_exec.gcov()[0],
        }
    )

    gcovr_test_exec.run(
        str(BAZEL),
        "build",
        *bazel_build_options,
        "//test:testcase",
        env=env,
    )

    # Remove existing gcda files
    bazel_out = gcovr_test_exec.output_dir / "bazel-out"
    for file in bazel_out.resolve().rglob("*.gcda"):
        file.unlink()

    return env


@pytest.mark.skipif(
    BAZEL is None or IS_WINDOWS or (IS_DARWIN and IS_GCC) or not IS_GCC,
    reason="Bazel test not working on Windows or on MacOs (with gcc).",
)
def test_run_on_our_own(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test bazel build."""
    build_bazel_example(gcovr_test_exec)

    for directory in [
        p / "bin"
        for p in (gcovr_test_exec.output_dir / "bazel-out").glob("*-fastbuild")
    ]:
        gcovr_test_exec.run(directory / "test" / "testcase")
        additional_options = []
        if gcovr_test_exec.use_gcc_json_format():
            additional_options += ["--root", "/proc/self/cwd"]

        gcovr_test_exec.gcovr(
            "--gcov-keep",
            "--json-pretty",
            "--json=coverage.json",
            *additional_options,
            directory,
        )
        break
    else:
        raise AssertionError("Can't resolve directory bazel-out/*-fastbuild/bin.")

    gcovr_test_exec.compare_json()


@pytest.mark.skipif(
    BAZEL is None or IS_WINDOWS or IS_DARWIN or not IS_GCC,
    reason="Bazel test not working on Windows and MacOs or with LLVM/clang.",
)
def test_use_coverage_dat(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test bazel build."""
    env = build_bazel_example(gcovr_test_exec)

    for directory in [
        p / "bin"
        for p in (gcovr_test_exec.output_dir / "bazel-out").glob("*-fastbuild")
    ]:
        bazel_coverage_options = [
            "--instrumentation_filter=//:lib",
            "--experimental_fetch_all_coverage_outputs",
            "--test_output=all",
            "--test_env=VERBOSE_COVERAGE=1",
        ]
        gcovr_test_exec.run(
            str(BAZEL),
            "coverage",
            *bazel_coverage_options,
            "//test:testcase",
            env=env,
        )

        additional_options = []
        if gcovr_test_exec.use_gcc_json_format():
            additional_options += ["--root", "/proc/self/cwd"]
        gcovr_test_exec.gcovr(
            "--gcov-keep",
            "--json-pretty",
            "--json",
            "coverage.json",
            *additional_options,
            directory.parent / "testlogs",
        )

        break
    else:
        raise AssertionError("Can't resolve directory bazel-out/*-fastbuild/bin.")

    gcovr_test_exec.compare_json()
