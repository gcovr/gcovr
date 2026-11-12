#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.8+main, a parsing and reporting tool for gcov.
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

import typing

import pytest
from pytest_check import check

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrExecFixture


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
