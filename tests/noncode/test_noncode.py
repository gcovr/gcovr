import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """A simple test that verifies line coverage with no branches."""
    gcovr_test_exec.cxx_link("testcase", "main.cpp")

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--exclude-noncode-lines",
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_test_exec.compare_json()
