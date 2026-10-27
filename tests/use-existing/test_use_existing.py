#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.8, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.8
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

import pytest
from pytest_check import check

from tests.conftest import (
    IS_GCC,
    USE_GCC_JSON_INTERMEDIATE_FORMAT,
    GcovrExecFixture,
)


@pytest.mark.json
def test_all(gcovr_exec: "GcovrExecFixture") -> None:
    """A test that verifies coverage when using existing *.gcov coverage files."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_exec.run("./testcase")
    gcovr_exec.run(
        *gcovr_exec.gcov(),
        *list(gcovr_exec.output_dir.glob("*.gcda")),
        "--branch-counts",
        "--branch-probabilities",
        "--preserve-paths",
    )
    gcovr_exec.gcovr(
        "--gcov-use-existing-files",
        "--gcov-delete",
        "--keep-intermediate-files",
        "--json-pretty",
        "--json=coverage.json",
    )
    check.is_true(
        list(gcovr_exec.output_dir.glob("*.gcda")),
        "*.gcda files should not be touched",
    )
    check.is_true(
        list(gcovr_exec.output_dir.glob("*.gcov")), "*.gcov files should be kept"
    )
    gcovr_exec.gcovr(
        "--gcov-use-existing-files",
        "--json-pretty",
        "--json=coverage.json",
    )
    check.is_false(
        list(gcovr_exec.output_dir.glob("*.gcov")),
        "*.gcov files should be removed",
    )
    gcovr_exec.compare_json()


@pytest.mark.json
def test_exclude_existing(gcovr_exec: "GcovrExecFixture") -> None:
    """A test that verifies exclusion when using existing *.gcov coverage files."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_exec.run("./testcase")
    gcovr_exec.run(
        *gcovr_exec.gcov(),
        *list(gcovr_exec.output_dir.glob("*.gcda")),
        "--branch-counts",
        "--branch-probabilities",
        "--preserve-paths",
    )
    gcovr_exec.gcovr(
        "--verbose",
        "--gcov-use-existing-files",
        "--gcov-exclude=.*main.*",
        "--gcov-delete",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_exec.compare_json()


@pytest.mark.skipif(
    USE_GCC_JSON_INTERMEDIATE_FORMAT,
    reason="We only have the problem in text reports.",
)
@pytest.mark.json
@pytest.mark.html
def test_issue_1166(gcovr_exec: "GcovrExecFixture") -> None:
    """A test that verifies reading of text reports without a function line."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_exec.run("./testcase")
    gcovr_exec.run(
        *gcovr_exec.gcov(),
        *list(gcovr_exec.output_dir.glob("*.gcda")),
        "--branch-counts",
        "--preserve-paths",
    )
    gcovr_exec.gcovr(
        "--verbose",
        "--gcov-use-existing-files",
        "--json-pretty",
        "--json=coverage.json",
        use_main=False,
    )
    check.is_in("(WARNING) No function line found in gcov file:", gcovr_exec.err)
    check.is_in(
        "/tests/use-existing/output/issue-1166/main.cpp.gcov",
        gcovr_exec.err,
    )
    gcovr_exec.compare_json()

    gcovr_exec.gcovr(
        "--verbose",
        "--json-add-tracefile=coverage.json",
        "--html-details=coverage.html",
    )
    gcovr_exec.compare_html()


@pytest.mark.skipif(
    not IS_GCC,
    reason="We use an existing file and this is independent from compiler",
)
@pytest.mark.json
def test_issue_1168(gcovr_exec: "GcovrExecFixture") -> None:
    """A test that verifies correct parsing of template functions (specializations)."""
    gcov_file = (
        gcovr_exec.output_dir / "ParamWithIntArray_test.cpp.gcda.ParamWithValue.h.gcov"
    )
    gcov_file_content = gcov_file.read_text().replace(
        "/home/abrown/Catena/sdks/cpp/common/include",  # cspell:disable-line
        str(gcovr_exec.output_dir),
    )
    gcov_file.write_text(gcov_file_content)
    gcovr_exec.gcovr(
        "--gcov-use-existing-files",
        "--filter=.*ParamWithValue.*",
        "--trace-include=.*ParamWithValue.*",
        "--json-pretty",
        "--json=coverage.json",
        ".",
    )
    gcovr_exec.compare_json()
