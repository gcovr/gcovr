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

import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.parametrize(
    "metric",
    ["line", "branch", "condition", "decision"],
)
@pytest.mark.sonarqube
def test_metric(gcovr_test_exec: "GcovrTestExec", metric: str) -> None:
    """Test excluding of functions."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    additional_options = [f"--sonarqube-metric={metric}"]
    if metric == "decision":
        additional_options.append("--decision")
    gcovr_test_exec.gcovr(
        *additional_options,
        "--sonarqube=sonarqube.xml",
    )
    gcovr_test_exec.compare_sonarqube()
