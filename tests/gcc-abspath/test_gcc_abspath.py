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

import pytest

from tests.conftest import _CC_HELP_OUTPUT, GcovrTestExec

PROFILE_ABS_PATH = "-fprofile-abs-path"


@pytest.mark.skipif(
    PROFILE_ABS_PATH not in _CC_HELP_OUTPUT,
    reason=f"GCC version does not support {PROFILE_ABS_PATH}",
)
@pytest.mark.json
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test gcc-abspath coverage."""
    subfolder = gcovr_test_exec.output_dir / "subfolder"
    gcovr_test_exec.cc_link(
        "testcase",
        PROFILE_ABS_PATH,
        "main.c",
        cwd=subfolder,
    )

    gcovr_test_exec.run("./testcase", cwd=subfolder)
    for file in subfolder.glob("*.gc??"):
        file.rename(file.parent.parent / file.name)
    gcovr_test_exec.gcovr(
        "--delete-input-files", "--json-pretty", "--json=coverage.json"
    )
    gcovr_test_exec.compare_json()
