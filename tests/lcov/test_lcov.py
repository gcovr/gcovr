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
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test_report_name_with_spaces(
    gcovr_test_exec: "GcovrTestExec", caplog: pytest.LogCaptureFixture
) -> None:
    """Test error if report name contains spaces."""
    process = gcovr_test_exec.gcovr(
        "--lcov-test-name", "Name with spaces", use_main=True
    )
    assert process.returncode == 1
    messages = caplog.record_tuples
    assert len(messages) == 1
    assert messages[0][1] == logging.ERROR
    assert (
        messages[0][2]
        == "The LCOV test name must not contain spaces, got 'Name with spaces'."
    )
