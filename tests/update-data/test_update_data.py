import pytest

from tests.conftest import IS_LINUX, GcovrTestExec


@pytest.mark.skipif(
    not IS_LINUX,
    reason="Merging is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """A test that verifies CoverageData.update function.

    The same header will be included by 2 source files and
    shall report 100% coverage.
    """
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
        gcovr_test_exec.cc_compile("update-data.c"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("--json-pretty", "--json", "coverage.json")
    gcovr_test_exec.compare_json()
