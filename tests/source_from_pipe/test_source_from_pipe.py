import typing


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test ignoring GCOV output errors."""

    gcovr_test_exec.run(
        "sh", "-c", "cat test.cpp | $CXX $CXXFLAGS -x c++ -c - -o test.o"
    )
    gcovr_test_exec.cxx_link(
        "testcase", gcovr_test_exec.cxx_compile("code.cpp"), "test.o"
    )

    gcovr_test_exec.run("./testcase")
    gcovr_args = [
        "--verbose",
        "--json-pretty",
        "--json=coverage.json",
    ]
    if not gcovr_test_exec.use_gcc_json_format():
        gcovr_args.insert(0, "--gcov-ignore-errors=no_working_dir_found")
    gcovr_test_exec.gcovr(*gcovr_args)
    gcovr_test_exec.compare_json()
