import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test_all(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """A test that verifies coverage when using existing *.gcov coverage files."""
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
        "--gcov-keep",
        "--json-pretty",
        "--json=coverage.json",
    )
    check.is_true(
        list(gcovr_test_exec.output_dir.glob("*.gcda")),
        "*.gcda files should be touched",
    )
    check.is_true(
        list(gcovr_test_exec.output_dir.glob("*.gcov")), "*.gcov files should be kept"
    )
    gcovr_test_exec.gcovr(
        "--gcov-use-existing-files",
        "--json-pretty",
        "--json=coverage.json",
    )
    check.is_false(
        list(gcovr_test_exec.output_dir.glob("*.gcov")),
        "*.gcov files should be removed",
    )
    gcovr_test_exec.compare_json()


def test_exclude_existing(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """A test that verifies exclusion when using existing *.gcov coverage files."""
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
        "--verbose",
        "--gcov-use-existing-files",
        "--gcov-exclude=.*main.*",
        "--gcov-delete",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
