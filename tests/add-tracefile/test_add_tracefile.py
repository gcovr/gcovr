import typing


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test merging of tracefiles."""
    common_objects = [
        gcovr_test_exec.cxx_compile("foo.cpp"),
        gcovr_test_exec.cxx_compile("bar.cpp"),
    ]
    gcovr_test_exec.cxx_link(
        "testcase_foo",
        gcovr_test_exec.cxx_compile("main.cpp", target="main_foo.o", options=["-DFOO"]),
        *common_objects,
    )
    gcovr_test_exec.cxx_link(
        "testcase_bar",
        gcovr_test_exec.cxx_compile("main.cpp", target="main_bar.o", options=["-DBAR"]),
        *common_objects,
    )

    gcovr_test_exec.run("./testcase_foo")
    gcovr_test_exec.gcovr("-d", "--json-pretty", "--json", "coverage_foo.json")

    gcovr_test_exec.run("./testcase_bar")
    gcovr_test_exec.gcovr("-d", "--json-pretty", "--json", "coverage_bar.json")

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage_*.json",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
