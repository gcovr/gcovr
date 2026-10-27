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

from tests.conftest import (
    CC_VERSION,
    IS_DARWIN,
    IS_GCC,
    IS_LINUX,
    GcovrExecFixture,
)

SKIP_TEST = not IS_LINUX and not (IS_DARWIN and not IS_GCC and CC_VERSION == 17)  # noqa: PLR2004


@pytest.mark.skipif(
    SKIP_TEST,
    reason="Format is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.txt
def test_summary(gcovr_exec: "GcovrExecFixture") -> None:
    """Test of text summary."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--txt-summary",
        "--txt=coverage-output.txt",
    )
    (gcovr_exec.output_dir / "coverage_summary.txt").write_text(
        gcovr_exec.out, encoding="utf-8"
    )
    gcovr_exec.compare_txt()


@pytest.mark.skipif(
    SKIP_TEST,
    reason="Format is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.txt
def test_summary_full(gcovr_exec: "GcovrExecFixture") -> None:
    """Test of text summary."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--txt-summary",
        "--calls",
        "--decision",
        "--txt=coverage-output.txt",
    )
    (gcovr_exec.output_dir / "coverage_summary.txt").write_text(
        gcovr_exec.out, encoding="utf-8"
    )
    gcovr_exec.compare_txt()


@pytest.mark.skipif(
    SKIP_TEST,
    reason="Format is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.txt
def test_default(gcovr_exec: "GcovrExecFixture") -> None:
    """Test text output coverage."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr("--txt=coverage.txt")
    gcovr_exec.compare_txt()


@pytest.mark.skipif(
    SKIP_TEST,
    reason="Format is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.txt
def test_branches(gcovr_exec: "GcovrExecFixture") -> None:
    """Test branch metric in text output."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--txt-metric=branch",
        "--txt=coverage.txt",
    )
    gcovr_exec.compare_txt()


@pytest.mark.skipif(
    SKIP_TEST,
    reason="Format is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.txt
def test_report_covered(gcovr_exec: "GcovrExecFixture") -> None:
    """Test covered lines in text output."""
    gcovr_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--txt-report-covered",
        "--txt=coverage.txt",
    )
    gcovr_exec.compare_txt()


@pytest.mark.skipif(
    SKIP_TEST,
    reason="Format is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.txt
def test_report_covered_branches(gcovr_exec: "GcovrExecFixture") -> None:
    """Test branch metric with covered report in text output."""
    gcovr_exec.cxx_link("testcase", "main.cpp")

    gcovr_exec.run("./testcase")
    gcovr_exec.gcovr(
        "--txt-metric=branch",
        "--txt-report-covered",
        "--txt=coverage.txt",
    )
    gcovr_exec.compare_txt()
