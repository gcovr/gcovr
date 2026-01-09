# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.5+main, a parsing and reporting tool for gcov.
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

from contextlib import contextmanager
from pathlib import Path
import platform
import sys
import typing

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@contextmanager
def subst(gcovr_test_exec: "GcovrTestExec") -> typing.Iterator[Path]:
    """Subst the path to a drive and return it."""
    import win32api
    import string

    used_drives = [e[:-1] for e in win32api.GetLogicalDriveStrings().split("\0")]
    sys.stdout.write(f"Used drives: {', '.join(used_drives)}")
    free_drives = sorted(
        set(f"{e}:" for e in string.ascii_uppercase) - set(used_drives)
    )
    sys.stdout.write(f"Free drives: {', '.join(free_drives)}")
    assert free_drives, "Must have at least one free drive letter"
    drive = None
    try:
        path = gcovr_test_exec.output_dir
        drive = free_drives[-1]
        gcovr_test_exec.run("cmd", "/C", f"subst {drive} {path.parent}")
        print(f"Substituted path {path.parent} to {drive}.", file=sys.stderr)
        yield Path(drive, path.name)
    finally:
        if drive is not None:
            print(f"Remove substitution {drive}.", file=sys.stderr)
            gcovr_test_exec.run("cmd", "/C", f"subst {drive} /d")


@pytest.mark.skipif(platform.system() != "Windows", reason="Only for windows")
@pytest.mark.html
@pytest.mark.clover
@pytest.mark.cobertura
@pytest.mark.coveralls
@pytest.mark.jacoco
@pytest.mark.json
@pytest.mark.lcov
@pytest.mark.sonarqube
@pytest.mark.txt
def test_drive_subst(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test with drive substitution on Windows."""

    with subst(gcovr_test_exec) as subst_drive:
        gcovr_test_exec.cxx_link("testcase", "main.cpp", cwd=subst_drive)

        gcovr_test_exec.run("./testcase")
        gcovr_test_exec.gcovr("--json-pretty", "--json=coverage.json", cwd=subst_drive)
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--json-summary-pretty",
            "--json-summary=coverage_summary.json",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_json()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--html-details=coverage.html",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_html()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--txt=coverage.txt",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_txt()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--clover-pretty",
            "--clover=clover.xml",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_clover()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--cobertura-pretty",
            "--cobertura=cobertura.xml",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_cobertura()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--coveralls-pretty",
            "--coveralls=coveralls.json",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_coveralls()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--lcov=coverage.lcov",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_lcov()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--jacoco=jacoco.xml",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_jacoco()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--sonarqube=sonarqube.xml",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_sonarqube()
