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

    used_drives = win32api.GetLogicalDriveStrings().split("\0")
    sys.stdout.write(f"Used drives: {used_drives}")
    free_drives = sorted(set(string.ascii_uppercase) - set(used_drives))
    sys.stdout.write(f"Free drives: {free_drives}")
    assert free_drives, "Must have at least one free drive letter"
    root = None
    try:
        path = gcovr_test_exec.output_dir
        gcovr_test_exec.run(f"subst {free_drives[-1]}: {path.parent}")
        root = f"{free_drives[-1]}:\\"
        print(f"Substituted path {path.parent} to {root}.", file=sys.stderr)
        yield Path(root, path.name)
    finally:
        if root is not None:
            print(f"Remove substitution {root}.", file=sys.stderr)
            gcovr_test_exec.run(f"subst {root} /d")


@pytest.mark.skipif(platform.system() != "Windows", reason="Only for windows")
def test_drive_subst(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test with drive substitution on Windows."""

    with subst(gcovr_test_exec) as subst_drive:
        gcovr_test_exec.cxx_link("testcase", "main.cpp", cwd=subst_drive)

        gcovr_test_exec.run("testcase")
        gcovr_test_exec.gcovr("--json-pretty", "--json=coverage.json", cwd=subst_drive)
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--json-summary-pretty",
            "--json=coverage_summary.json",
            cwd=subst_drive,
        )
        gcovr_test_exec.compare_json()

        gcovr_test_exec.gcovr(
            "--json-add-tracefile=coverage.json",
            "--html-details=coverage-details-linkcss.html",
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
