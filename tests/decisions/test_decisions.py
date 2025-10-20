import platform
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Parsing of decision is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test of decision parsing."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
        "switch_test.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--keep",
        "--verbose",
        "--decisions",
        "--json-pretty",
        "--json",
        "coverage.json.gz",
    )
    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile",
        "coverage.json.gz",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile",
        "coverage.json.gz",
        "--decision",
        "--json-summary-pretty",
        "--json-summary=coverage_summary.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile",
        "coverage.json.gz",
        "--decision",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.compare_html()

    process = gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile",
        "coverage.json.gz",
        "--txt-metric",
        "decision",
        "--txt-summary",
        "--txt=coverage.txt",
    )
    (gcovr_test_exec.output_dir / "coverage_summary.txt").write_text(
        process.stdout, encoding="utf-8"
    )
    gcovr_test_exec.compare_txt()
