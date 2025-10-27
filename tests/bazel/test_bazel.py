import os
from pathlib import Path
import shutil

import pytest

from tests.conftest import IS_DARWIN, IS_GCC, IS_WINDOWS, GcovrTestExec

BAZEL = shutil.which("bazel")


@pytest.mark.skipif(
    BAZEL is None or IS_WINDOWS or (IS_DARWIN and IS_GCC) or not IS_GCC,
    reason="Bazel test not working on Windows or on MacOs (with gcc).",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test bazel build."""
    bazel_build_options = [
        "--collect_code_coverage=True",
        "--test_output=all",
        "--test_env=VERBOSE_COVERAGE=1",
    ]
    bazel_coverage_options = [
        "--instrumentation_filter=//:lib",
        "--experimental_fetch_all_coverage_outputs",
        "--test_output=all",
        "--test_env=VERBOSE_COVERAGE=1",
    ]
    if not gcovr_test_exec.is_windows():
        bazel_build_options.append("--force_pic")
    if gcovr_test_exec.is_llvm():
        bazel_build_options.append("--config=clang-gcov")
        bazel_coverage_options.append("--config=clang-gcov")

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

    def remove_gcda(directory: Path) -> None:
        for file in directory.resolve().rglob("*.gcda"):
            file.unlink()

    # Remove all gcda files in the bin directory
    for directory in [
        p / "bin"
        for p in (gcovr_test_exec.output_dir / "bazel-out").glob("*-fastbuild")
    ]:
        remove_gcda(directory)
        gcovr_test_exec.run(directory / "test" / "testcase")
        additional_options = []
        if gcovr_test_exec.use_gcc_json_format():
            additional_options += ["--root", "/proc/self/cwd"]

        gcovr_test_exec.gcovr(
            "--json-pretty",
            "--json=coverage.json",
            *additional_options,
            directory,
        )

        if gcovr_test_exec.is_darwin():
            (gcovr_test_exec.output_dir / "coverage_bazel.json").write_text(
                '"Test not working"\n',
                encoding="utf-8",
            )
        else:
            remove_gcda(directory)
            gcovr_test_exec.run(
                str(BAZEL),
                "coverage",
                *bazel_coverage_options,
                "//test:testcase",
                env=env,
            )
            gcovr_test_exec.gcovr(
                "--json-pretty",
                "--json=coverage_bazel.json",
                *additional_options,
                directory.parent / "testlogs",
            )

        break
    else:
        raise AssertionError("Can't resolve directory bazel-out/*-fastbuild/bin.")

    gcovr_test_exec.compare_json()
