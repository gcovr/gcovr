# -*- coding:utf-8 -*-

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

import logging

import pytest

from tests.conftest import CONDITION_COVERAGE_POSSIBLE, IS_LINUX, GcovrTestExec

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
def test_report(gcovr_test_exec: "GcovrTestExec") -> None:
    """Full branch coverage with an uncovered condition outcome."""
    gcovr_test_exec.cc_link("testcase", "main.c")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json",
    )
    gcovr_test_exec.compare_json()

    process = gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--txt-summary",
        "--txt=coverage.txt",
    )
    (gcovr_test_exec.output_dir / "coverage_summary.txt").write_text(
        process.stdout, encoding="utf-8"
    )
    gcovr_test_exec.compare_txt()


def test_fail_under(
    gcovr_test_exec: "GcovrTestExec", caplog: pytest.LogCaptureFixture
) -> None:
    """The condition threshold must fail where the branch threshold passes."""
    gcovr_test_exec.cc_link("testcase", "main.c")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )

    process = gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--fail-under-line=100",
        "--fail-under-branch=100",
        use_main=True,
    )
    assert process.returncode == 0
    assert caplog.record_tuples == []

    process = gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--fail-under-condition-or-decision=100",
        use_main=True,
    )
    assert process.returncode == 8
    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.ERROR
    assert messages[0][2].startswith("Failed minimum condition coverage ")
    caplog.clear()

    process = gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--decisions",
        "--fail-under-condition-or-decision=100",
        use_main=True,
    )
    assert process.returncode == 8
    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.ERROR
    assert messages[0][2].startswith("Failed minimum condition coverage ")
    caplog.clear()

    # The deprecated flags are synonyms of the combined threshold.
    for option in ["--fail-under-condition", "--fail-under-decision"]:
        process = gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--decisions",
            f"{option}=100",
            use_main=True,
        )
        assert process.returncode == 8
        messages = caplog.record_tuples
        assert len(messages) == 1
        assert messages[0][1] == logging.ERROR
        assert messages[0][2].startswith("Failed minimum condition coverage ")
        caplog.clear()

    process = gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        "--decisions",
        "--fail-under-condition-or-decision=83.3",
        use_main=True,
    )
    assert process.returncode == 0
    assert caplog.record_tuples == []
