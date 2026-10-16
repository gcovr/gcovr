#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.7, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.7
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

import logging

import pytest

from tests.conftest import CONDITION_COVERAGE_POSSIBLE, IS_LINUX, GcovrExecFixture

pytestmark = [
    pytest.mark.skipif(
        not CONDITION_COVERAGE_POSSIBLE,
        reason="Compiler doesn't support -fcondition-coverage.",
    ),
    pytest.mark.skipif(
        not IS_LINUX,
        reason="Condition parsing is independent of OS and we do not want to have separate data for Windows and Darwin.",
    ),
]


@pytest.mark.json
@pytest.mark.txt
def test_report(gcovr_exec: "GcovrExecFixture") -> None:
    """Full branch coverage with an uncovered condition outcome."""
    gcovr_exec.cc_link("testcase", "main.c")

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json",
    )
    gcovr_exec.compare_json()

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt-summary",
        "--txt-metric=condition",
        "--txt=coverage.txt",
    )
    (gcovr_exec.output_dir / "coverage_summary.txt").write_text(
        gcovr_exec.out, encoding="utf-8"
    )
    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt-summary",
        "--txt-metric=condition",
        "--txt-report-covered",
        "--txt=coverage_covered.txt",
    )
    gcovr_exec.compare_txt()


def test_fail_under(gcovr_exec: "GcovrExecFixture") -> None:
    """The condition threshold must fail where the branch threshold passes."""
    gcovr_exec.cc_link("testcase", "main.c")

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--fail-under-line=100",
        "--fail-under-branch=100",
    )

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--fail-under-condition-or-decision=100",
        exitcode_ok=8,
    )
    gcovr_exec.check_log(
        (logging.ERROR, "Failed minimum condition coverage "),
        compare="startswith",
    )

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--decisions",
        "--fail-under-condition-or-decision=100",
        exitcode_ok=8,
    )
    gcovr_exec.check_log(
        (logging.ERROR, "Failed minimum condition coverage "),
        compare="startswith",
    )

    # The deprecated flags are synonyms of the combined threshold.
    for option in ["--fail-under-condition", "--fail-under-decision"]:
        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--decisions",
            f"{option}=100",
            exitcode_ok=8,
        )
        gcovr_exec.check_log(
            (logging.ERROR, "Failed minimum condition coverage "),
            compare="startswith",
        )

    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--decisions",
        "--fail-under-condition-or-decision=83.3",
    )
    gcovr_exec.check_log()
