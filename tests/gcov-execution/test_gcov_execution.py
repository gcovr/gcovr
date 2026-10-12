#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import os
import re
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import pytest
from pytest_check import check

from tests.conftest import (
    GCOVR_ISOLATED_TEST,
    IS_DARWIN_HOST,
    IS_WINDOWS,
    USE_GCC_JSON_INTERMEDIATE_FORMAT,
    GcovrExecFixture,
)

CHMOD_IS_WORKING = (
    not GCOVR_ISOLATED_TEST or IS_DARWIN_HOST or USE_GCC_JSON_INTERMEDIATE_FORMAT
)


@contextmanager
def chmod(mode: int, *paths: Path) -> Generator[None, None, None]:
    """Change mode during execution."""
    modes = []
    try:
        for path in paths:
            modes.append(path.stat().st_mode)
            path.chmod(mode)
        yield
    finally:
        for index, old_mode in enumerate(modes):
            paths[index].chmod(old_mode)


@pytest.mark.skipif(IS_WINDOWS, reason="GCOV stub script isn't working under Windows")
def test_kill_by_signal(gcovr_exec: "GcovrExecFixture") -> None:
    """Test a unknown CLA."""
    gcovr_exec.cxx_link("testcase", "src/main.cpp")

    gcovr_exec.run("./testcase")
    env = os.environ.copy()
    env.update({"GCOV_STUB_KILL_BY_SIGNAL": "SIGSEGV"})
    gcovr_exec.gcovr(
        "--verbose",
        "--gcov-executable=./gcov-stub",
        "--json=coverage.json",
        env=env,
        use_main=False,
        exitcode_ok=64,
    )

    check.is_in(
        "GCOV returncode was -11 (exited by signal).",
        gcovr_exec.err,
    )
    check.is_in(
        "(ERROR) Error occurred while reading reports: Worker thread raised exception, workers canceled.",
        gcovr_exec.err,
        "Workers canceled exception found in stderr.",
    )


@pytest.mark.skipif(IS_WINDOWS, reason="GCOV stub script isn't working under Windows")
def test_unknown_cla(gcovr_exec: "GcovrExecFixture") -> None:
    """Test a unknown CLA."""
    gcovr_exec.cxx_link("testcase", "src/main.cpp")

    gcovr_exec.run("./testcase")
    env = os.environ.copy()
    env.update({"GCOV_STUB_ADDITIONAL_CLA": "--cla-does-not-exist"})
    gcovr_exec.gcovr(
        "--verbose",
        "--gcov-executable=./gcov-stub",
        "--json=coverage.json",
        env=env,
        use_main=False,
        exitcode_ok=64,
    )

    check.is_true(
        re.search(
            r": (?:unrecognized option|Unknown command line argument) ['`]--cla-does-not-exist'",
            gcovr_exec.err,
        ),
        "Unknown CLA message found in stderr.",
    )
    check.is_in(
        "(ERROR) Error occurred while reading reports: Worker thread raised exception, workers canceled.",
        gcovr_exec.err,
        "Workers canceled exception found in stderr.",
    )


@pytest.mark.skipif(IS_WINDOWS, reason="GCOV stub script isn't working under Windows")
def test_wrong_version(gcovr_exec: "GcovrExecFixture") -> None:
    """Test a version mismatch between gcc and gcov."""
    gcovr_exec.cxx_link("testcase", "src/main.cpp")

    gcovr_exec.run("./testcase")
    env = os.environ.copy()
    env.update(
        {
            "GCOV_STUB_ADDITIONAL_STDERR": "./dummy.gcda:version 'B32*', prefer version 'B42*'"
        }
    )
    gcovr_exec.gcovr(
        "--verbose",
        "--gcov-executable=./gcov-stub",
        "--json=coverage.json",
        "--trace-include=.*",
        env=env,
        use_main=False,
        exitcode_ok=64,
    )

    check.is_in(
        "Version mismatch gcc/gcov.",
        gcovr_exec.err,
    )
    check.is_in(
        "(ERROR) Error occurred while reading reports: Worker thread raised exception, workers canceled.",
        gcovr_exec.err,
        "Workers canceled exception found in stderr.",
    )


@pytest.mark.skipif(
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
def test_wd_not_found(gcovr_exec: "GcovrExecFixture") -> None:
    """Test working directory not found."""
    (gcovr_exec.output_dir / "build").mkdir()
    gcovr_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_exec.run("./testcase", cwd=Path("build"))

    with chmod(
        0o455 if gcovr_exec.is_darwin() else 0o555,
        gcovr_exec.output_dir / "src",
        gcovr_exec.output_dir / "build",
    ):
        gcovr_exec.gcovr(
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--root=src",
            "build",
            use_main=False,
            exitcode_ok=64,
        )
        check.is_in(
            "GCOV could not write output file, this can be ignored with --gcov-ignore-errors=output_error.",
            gcovr_exec.err,
        )
        check.is_in(
            "GCOV could not find source file, this can be ignored with --gcov-ignore-errors=source_not_found.",
            gcovr_exec.err,
        )
        check.is_in(
            "GCOVR could not infer a working directory that resolved it.",
            gcovr_exec.err,
        )
        check.is_in(
            "To ignore this error use option --gcov-ignore-errors=no_working_dir_found.",
            gcovr_exec.err,
        )
        check.is_false(
            (gcovr_exec.output_dir / "coverage.json").exists(),
            "No output file must be written.",
        )


@pytest.mark.skipif(
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
@pytest.mark.json
def test_ignore_output_error(gcovr_exec: "GcovrExecFixture") -> None:
    """Test ignoring GCOV output errors."""
    (gcovr_exec.output_dir / "build").mkdir()
    gcovr_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_exec.run("./testcase", cwd=Path("build"))

    with chmod(
        0o455 if gcovr_exec.is_darwin() else 0o555,
        gcovr_exec.output_dir / "src",
        gcovr_exec.output_dir / "build",
    ):
        gcovr_exec.gcovr(
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--gcov-ignore-errors=output_error",
            "--root=src",
            "build",
            use_main=False,
        )
        check.is_not_in(
            "GCOV could not write output file, this can be ignored with --gcov-ignore-errors=output_error.",
            gcovr_exec.err,
        )
        check.is_not_in(
            "GCOV could not find source file, this can be ignored with --gcov-ignore-errors=source_not_found.",
            gcovr_exec.err,
        )
        check.is_not_in(
            "GCOVR could not infer a working directory that resolved it.",
            gcovr_exec.err,
        )
    gcovr_exec.compare_json()


@pytest.mark.skipif(
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
@pytest.mark.json
def test_ignore_source_not_found(gcovr_exec: "GcovrExecFixture") -> None:
    """Test ignoring GCOV source not found errors."""
    (gcovr_exec.output_dir / "build").mkdir()
    gcovr_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_exec.run("./testcase", cwd=Path("build"))

    with chmod(
        0o455 if gcovr_exec.is_darwin() else 0o555,
        gcovr_exec.output_dir / "src",
        gcovr_exec.output_dir / "build",
    ):
        gcovr_exec.gcovr(
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--gcov-ignore-errors=source_not_found",
            "--root=src",
            "--trace-include=/.*main.*",
            "build",
            use_main=False,
        )
        check.is_not_in(
            "GCOV could not write output file, this can be ignored with --gcov-ignore-errors=output_error.",
            gcovr_exec.err,
        )
        check.is_not_in(
            "GCOV could not find source file, this can be ignored with --gcov-ignore-errors=source_not_found.",
            gcovr_exec.err,
        )
        check.is_not_in(
            "GCOVR could not infer a working directory that resolved it.",
            gcovr_exec.err,
        )
    gcovr_exec.compare_json()


@pytest.mark.skipif(
    CHMOD_IS_WORKING,
    reason="Only available in docker on hosts != MacOs",
)
@pytest.mark.json
def test_ignore_no_working_dir_found(gcovr_exec: "GcovrExecFixture") -> None:
    """Test gcov-no_working_dir_found logic."""
    (gcovr_exec.output_dir / "build").mkdir()
    gcovr_exec.cxx_link(
        "testcase",
        "../src/main.cpp",
        cwd=Path("build"),
    )

    gcovr_exec.run("./testcase", cwd=Path("build"))

    with chmod(
        0o455 if gcovr_exec.is_darwin() else 0o555,
        gcovr_exec.output_dir / "src",
        gcovr_exec.output_dir / "build",
    ):
        gcovr_args = [
            "--verbose",
            "--json-pretty",
            "--json=coverage.json",
            "--root=src",
            "build",
        ]
        if not gcovr_exec.use_gcc_json_format():
            gcovr_args.insert(0, "--gcov-ignore-errors=no_working_dir_found")
        gcovr_exec.gcovr(
            *gcovr_args,
            use_main=False,
        )
        check.is_not_in(
            "GCOV could not write output file, this can be ignored with --gcov-ignore-errors=output_error.",
            gcovr_exec.err,
        )
        check.is_not_in(
            "GCOV could not find source file, this can be ignored with --gcov-ignore-errors=source_not_found.",
            gcovr_exec.err,
        )
        check.is_not_in(
            "GCOVR could not infer a working directory that resolved it.",
            gcovr_exec.err,
        )
    gcovr_exec.compare_json()


@pytest.mark.skipif(IS_WINDOWS, reason="GCOV stub script isn't working under Windows")
def test_worker_exception(gcovr_exec: "GcovrExecFixture") -> None:
    """Test a gcovr worker exception."""
    gcovr_exec.cxx_link("testcase", "src/main.cpp")

    gcovr_exec.run("./testcase")
    env = os.environ.copy()
    env.update({"GCOV_STUB_ADDITIONAL_STDOUT": "Creating 'does#not#exist.gcov'"})
    gcovr_exec.gcovr(
        "--verbose",
        "--gcov-executable=./gcov-stub",
        "--json=coverage.json",
        env=env,
        use_main=False,
        exitcode_ok=64,
    )

    check.is_true(
        re.search(
            r"SanityCheckError: Output file .+does#not#exist.gcov doesn't exist but no error from GCOV detected.",
            gcovr_exec.err,
        ),
        "Sanity check exception found in stderr.",
    )
    check.is_in(
        "(ERROR) Error occurred while reading reports: Worker thread raised exception, workers canceled.",
        gcovr_exec.err,
        "Workers canceled exception found in stderr.",
    )

    check.is_false(
        (gcovr_exec.output_dir / "coverage.json").exists(),
        "No output file must be written.",
    )
