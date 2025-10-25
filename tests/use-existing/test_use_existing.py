import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """A test that verifies coverage when using existing *.gcov coverage files with verbose output.
    All files identical to tests/simple1 except for this README file and Makefile"""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.run(
        *gcovr_test_exec.gcov(),
        *list(gcovr_test_exec.output_dir.glob("*.gcda")),
        "--branch-counts",
        "--branch-probabilities",
        "--preserve-paths",
    )
    gcovr_test_exec.gcovr(
        "--gcov-use-existing-files",
        "--gcov-delete",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
