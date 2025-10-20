from pathlib import Path
import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test subfolder includes coverage."""
    gcovr_test_exec.cxx_link(
        "subfolder/testcase",
        gcovr_test_exec.cxx_compile(
            "subfolder/main.cpp", options=["-I../include"], cwd=Path("subfolder")
        ),
        gcovr_test_exec.cxx_compile(
            "subfolder/lib.cpp", options=["-I../include"], cwd=Path("subfolder")
        ),
        cwd=Path("subfolder"),
    )

    gcovr_test_exec.run("./subfolder/subfolder/testcase")
    gcovr_test_exec.gcovr("--html-details=coverage.html")
    gcovr_test_exec.compare_html()
