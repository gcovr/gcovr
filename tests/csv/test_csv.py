import typing


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test for generation of CSV report."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--csv", "coverage.csv")
    gcovr_test_exec.compare_csv()
