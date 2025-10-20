import typing

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


def test(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test workspace coverage."""
    gcovr_test_exec.gcovr(
        "--verbose",
        "--gcov-use-existing-files",
        "--json-pretty",
        "--json=coverage.json",
        "main.case_1.gcov",
        "data",
    )
    gcovr_test_exec.compare_json()
