import re

import pytest

from tests.conftest import GcovrTestExec


@pytest.mark.parametrize("activate_trace", [True, False])
def test(gcovr_test_exec: "GcovrTestExec", check, activate_trace: bool) -> None:  # type: ignore[no-untyped-def]
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

    additional_options = []
    if activate_trace:
        check_function = check.is_true
        additional_options += [
            "--trace-include=.*(?-i:File).*",
            "--trace-exclude=.*File6.*",
        ]
    else:
        check_function = check.is_false
    gcovr_test_exec.run("./subdir/testcase")
    process = gcovr_test_exec.gcovr(
        *additional_options,
        "--json-pretty",
        "--json=coverage.json",
    )
    for filename in ["File2", "File4"]:
        regex = re.compile(
            rf"^\(TRACE\) Running gcov in .+: .+{filename}.cpp.gcda .+$", re.MULTILINE
        )
        check_function(
            regex.search(process.stderr),
            f"Expected TRACE log running gcov for {filename} found.",
        )
        regex = re.compile(rf"^\(TRACE\) STDOUT >>File .+{filename}.+$", re.MULTILINE)
        check_function(
            regex.search(process.stderr),
            f"Expected TRACE log for gcov stdout of {filename} found.",
        )
        regex = re.compile(
            rf"^\(TRACE\) Parsing gcov data file .+{filename}.+:$", re.MULTILINE
        )
        check_function(
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
        regex = re.compile(rf"^\(TRACE\) STDOUT >>File .+{filename}.+$", re.MULTILINE)
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

    if activate_trace:
        for function in ["bar", "foobar"]:
            if gcovr_test_exec.use_gcc_json_format():
                regex = re.compile(
                    rf"^\(TRACE\) Reading .*:\d+ of function .*{function}.*$",
                    re.MULTILINE,
                )
            else:
                regex = re.compile(
                    rf"^\(TRACE\) Processing line: _FunctionLine\(name='.*?{function}.*', call_count=\d+, blocks_covered=\d+\.\d+\)$",
                    re.MULTILINE,
                )
            check.is_true(
                regex.search(process.stderr),
                f"Expected TRACE log for function '{regex.pattern}' found.",
            )
