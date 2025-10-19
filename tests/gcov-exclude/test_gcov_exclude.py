import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File2.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
    )

    gcovr_test_exec.run("./subdir/testcase")
    gcovr_test_exec.gcovr(
        "-r",
        "subdir",
        "--gcov-exclude-directory",
        ".*/A/C(?:/.*)?",
        "--gcov-filter",
        ".*",
        "--gcov-exclude",
        "subdir#A#[Ff]ile.\\.cpp\\.gcov",
        "--gcov-exclude",
        "[Ff]ile.\\.cpp##.*",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
