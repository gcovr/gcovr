#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.7+main, a parsing and reporting tool for gcov.
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
import platform
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest

if TYPE_CHECKING:
    from tests.conftest import GcovrExecFixture

LOGGER = logging.getLogger(__name__)


@contextmanager
def subst(gcovr_exec: "GcovrExecFixture") -> Generator[Path, None, None]:
    """Subst the path to a drive and return it."""
    import string  # noqa: PLC0415

    import win32api  # noqa: PLC0415

    used_drives = [e[:-1] for e in win32api.GetLogicalDriveStrings().split("\0")]
    gcovr_exec.print(f"Used drives: {', '.join(used_drives)}")
    free_drives = sorted({f"{e}:" for e in string.ascii_uppercase} - set(used_drives))
    gcovr_exec.print(f"Free drives: {', '.join(free_drives)}")
    assert free_drives, "Must have at least one free drive letter"
    drive = None
    try:
        path = gcovr_exec.output_dir
        drive = free_drives[-1]
        gcovr_exec.run("cmd", "/C", f"subst {drive} {path.parent}")
        gcovr_exec.print(f"Substituted path {path.parent} to {drive}.")
        yield Path(f"{drive}/{path.name}")
    finally:
        if drive is not None:
            gcovr_exec.print(
                f"Remove substitution {drive}.",
            )
            gcovr_exec.run("cmd", "/C", f"subst {drive} /d")


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
def test_drive_subst(gcovr_exec: "GcovrExecFixture") -> None:
    """Test with drive substitution on Windows."""
    with subst(gcovr_exec) as subst_drive:
        gcovr_exec.cxx_link("testcase", "main.cpp", cwd=subst_drive)

        gcovr_exec.run("./testcase")
        gcovr_exec.gcovr("--json-pretty", "--json=coverage.json", cwd=subst_drive)
        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--json-summary-pretty",
            "--json-summary=coverage_summary.json",
            cwd=subst_drive,
            use_main=False,
        )
        gcovr_exec.compare_json()

        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--html-details=coverage.html",
            cwd=subst_drive,
        )
        gcovr_exec.compare_html()

        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--txt=coverage.txt",
            cwd=subst_drive,
        )
        gcovr_exec.compare_txt()

        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--clover-pretty",
            "--clover=clover.xml",
            cwd=subst_drive,
        )
        gcovr_exec.compare_clover()

        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--cobertura-pretty",
            "--cobertura=cobertura.xml",
            cwd=subst_drive,
        )
        gcovr_exec.compare_cobertura()

        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--coveralls-pretty",
            "--coveralls=coveralls.json",
            use_main=False,
            cwd=subst_drive,
        )
        gcovr_exec.compare_coveralls()

        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--lcov=coverage.lcov",
            cwd=subst_drive,
        )
        gcovr_exec.compare_lcov()

        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--jacoco=jacoco.xml",
            cwd=subst_drive,
        )
        gcovr_exec.compare_jacoco()

        gcovr_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--sonarqube=sonarqube.xml",
            cwd=subst_drive,
        )
        gcovr_exec.compare_sonarqube()
