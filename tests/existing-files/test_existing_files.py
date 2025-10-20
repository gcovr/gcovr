import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test using existing gcov files."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.run(
        *gcovr_test_exec.gcov(),
        "--branch-counts",
        "--branch-probabilities",
        "--all-blocks",
        *list(gcovr_test_exec.output_dir.glob("*.gc*")),
    )
    gcovr_test_exec.gcovr(
        "--verbose",
        "--gcov-use-existing-files",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()
