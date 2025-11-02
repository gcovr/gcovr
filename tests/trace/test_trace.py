import platform
import re
import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="Dor-folders have no special meaning on Windows and we do not want to have separate data wor Windows and Darwin.",
)
def test(gcovr_test_exec: "GcovrTestExec", check) -> None:  # type: ignore[no-untyped-def]
    """Test adding a tracefile output."""
    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        *[
            gcovr_test_exec.cxx_compile(source, target=source + ".o", options=["-DFOO"])
            for source in [
                "subdir/A/file1.cpp",
                "subdir/A/File2.cpp",
                "subdir/A/file3.cpp",
                "subdir/A/File4.cpp",
                "subdir/A/C/file5.cpp",
                "subdir/A/C/D/File6.cpp",
                "subdir/B/main.cpp",
            ]
        ],
    )

    gcovr_test_exec.run("./subdir/testcase")
    process = gcovr_test_exec.gcovr(
        "--trace-include=.*(?-i:File).*",
        "--trace-exclude=.*File6.*",
        "--json-pretty",
        "--json=coverage.json",
    )
    for filename in ["File2", "File4"]:
        regex = re.compile(
            rf"^\(TRACE\) Running gcov in .+: .+{filename}.cpp.gcda .+$", re.MULTILINE
        )
        check.is_true(
            regex.search(process.stderr),
            f"Expected TRACE log running gcov for {filename} found.",
        )
        regex = re.compile(
            rf"^\(TRACE\) Stdout of gcov was >>File .+{filename}.+$", re.MULTILINE
        )
        check.is_true(
            regex.search(process.stderr),
            f"Expected TRACE log for gcov stdout of {filename} found.",
        )
        regex = re.compile(
            rf"^\(TRACE\) Parsing gcov data file .+{filename}.+:$", re.MULTILINE
        )
        check.is_true(
            regex.search(process.stderr),
            f"Expected TRACE log for parsing {filename} found.",
        )
    for filename in ["file1", "file3", "file5", "File6", "main"]:
        regex = re.compile(
            rf"^\(TRACE\) Running gcov in .+: .+{filename}.cpp.gcda .+$", re.MULTILINE
        )
        check.is_false(
            regex.search(process.stderr),
            f"Unexpected TRACE log running gcov for {filename} found.",
        )
        regex = re.compile(
            rf"^\(TRACE\) Stdout of gcov was >>File .+{filename}.+$", re.MULTILINE
        )
        check.is_false(
            regex.search(process.stderr),
            f"Unexpected TRACE log for gcov stdout of {filename} found",
        )
        regex = re.compile(
            rf"^\(TRACE\) Parsing gcov data file .+{filename}.+:$", re.MULTILINE
        )
        check.is_false(
            regex.search(process.stderr),
            f"Unexpected TRACE log for {filename} not found.",
        )

    for function in ["bar", "foobar"]:
        if gcovr_test_exec.use_gcc_json_format():
            regex = re.compile(
                rf"^\(TRACE\) Reading .*:\d+ of function .*{function}.*$",
                re.MULTILINE,
            )
        else:
            regex = re.compile(
                rf"^\(TRACE\) Parsed line: _FunctionLine\(name='.*?{function}.*', call_count=\d+, blocks_covered=\d+\.\d+\)$",
                re.MULTILINE,
            )
        check.is_true(
            regex.search(process.stderr),
            f"Expected TRACE log for function '{regex.pattern}' found.",
        )

    gcovr_test_exec.compare_json()
