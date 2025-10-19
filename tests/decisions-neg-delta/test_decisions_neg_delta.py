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
    """This test case causes a negative delta value during the multiline decision analysis, which results in a:
    DecisionCoverageUncheckable: decision and a debug log
    AssertionError: assert count_false >= 0
    """
    gcovr_test_exec.cxx_link(
        "testcase",
        "-std=c++11",
        "-O0",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--verbose",
        "--decisions",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile",
        "coverage.json",
        "--txt-metric",
        "decision",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile",
        "coverage.json",
        "--decision",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.compare_html()
