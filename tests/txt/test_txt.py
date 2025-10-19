import platform
import typing

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Format is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_summary(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test of text summary."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "--txt-summary",
        "--txt=coverage-output.txt",
    )
    (gcovr_test_exec.output_dir / "coverage_summary.txt").write_text(
        process.stdout, encoding="utf-8"
    )
    gcovr_test_exec.compare_txt()


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Format is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_summary_full(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test of text summary."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr(
        "--txt-summary",
        "--calls",
        "--decision",
        "--txt=coverage-output.txt",
    )
    (gcovr_test_exec.output_dir / "coverage_summary.txt").write_text(
        process.stdout, encoding="utf-8"
    )
    gcovr_test_exec.compare_txt()


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Format is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_default(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test text output coverage."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--txt=coverage.txt")
    gcovr_test_exec.compare_txt()


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Format is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_branches(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test branch metric in text output."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--txt-metric=branch",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Format is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_report_covered(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test covered lines in text output."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--txt-report-covered",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Format is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test_report_covered_branches(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test branch metric with covered report in text output."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--txt-metric=branch",
        "--txt-report-covered",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()
