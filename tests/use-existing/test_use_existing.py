import pytest

from tests.conftest import (
    IS_GCC,
    USE_GCC_JSON_INTERMEDIATE_FORMAT,
    GcovrTestExec,
)


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
        "*.gcda files should not be touched",
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


def test_exclude_existing(gcovr_test_exec: "GcovrTestExec") -> None:
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


@pytest.mark.skipif(
    USE_GCC_JSON_INTERMEDIATE_FORMAT,
    reason="We only have the problem in text reports.",
)
def test_issue_1166(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """A test that verifies reading of text reports without a function line."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )
    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.run(
        *gcovr_test_exec.gcov(),
        *list(gcovr_test_exec.output_dir.glob("*.gcda")),
        "--branch-counts",
        "--preserve-paths",
    )
    process = gcovr_test_exec.gcovr(
        "--verbose",
        "--gcov-use-existing-files",
        "--json-pretty",
        "--json=coverage.json",
    )
    check.is_in("(WARNING) No function line found in gcov file:", process.stderr)
    check.is_in("/tests/use-existing/output/issue-1166/main.cpp.gcov", process.stderr)
    gcovr_test_exec.compare_json()

    gcovr_test_exec.gcovr(
        "--verbose",
        "--json-add-tracefile=coverage.json",
        "--html-details=coverage.html",
    )
    gcovr_test_exec.compare_html()


@pytest.mark.skipif(
    not IS_GCC,
    reason="We use an existing file and this is independent from compiler",
)
def test_issue_1168(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """A test that verifies correct parsing of template functions (specializations)."""
    gcov_file = (
        gcovr_test_exec.output_dir
        / "ParamWithIntArray_test.cpp.gcda.ParamWithValue.h.gcov"
    )
    gcov_file_content = gcov_file.read_text().replace(
        "/home/abrown/Catena/sdks/cpp/common/include",  # cspell:disable-line
        str(gcovr_test_exec.output_dir),
    )
    gcov_file.write_text(gcov_file_content)
    gcovr_test_exec.gcovr(
        "--verbose",
        "--gcov-use-existing-files",
        "--filter=.*ParamWithValue.*",
        "--trace-include=.*ParamWithValue.*",
        "--json-pretty",
        "--json=coverage.json",
        ".",
    )
    gcovr_test_exec.compare_json()
