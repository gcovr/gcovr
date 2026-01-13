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
from pathlib import Path
import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.txt
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """A test that verifies coverage when using symlinks to create a root directory."""
    (gcovr_test_exec.output_dir / "symlink").symlink_to(
        gcovr_test_exec.output_dir / "root"
    )
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
        cwd=Path("symlink"),
    )

    gcovr_test_exec.run("./testcase", cwd=Path("symlink"))
    gcovr_test_exec.gcovr("--txt=../coverage.txt", "--root=.", cwd=Path("symlink"))
    gcovr_test_exec.compare_txt()
