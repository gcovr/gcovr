import os
import platform
import typing

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="File inclusion is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test include filtering and multiple HTML themes."""
    # Compile file1.cpp without coverage flags, then main.cpp with coverage
    gcovr_test_exec.run(os.environ["CXX"], "-fPIC", "-c", "file1.cpp", "-o", "file1.o")
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
        "file1.o",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--verbose",
        "--include=file1.cpp",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
