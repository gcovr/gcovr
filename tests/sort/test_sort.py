import typing

import pytest


if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec


@pytest.mark.parametrize(
    "sort",
    ["uncovered-percent", "uncovered-number"],
)
def test(gcovr_test_exec: "GcovrTestExec", sort: str) -> None:
    """Test excluding of functions."""
    gcovr_test_exec.cxx_link(
        "testcase",
        gcovr_test_exec.cxx_compile("file1.cpp"),
        gcovr_test_exec.cxx_compile("file2.cpp"),
        gcovr_test_exec.cxx_compile("file3.cpp"),
        gcovr_test_exec.cxx_compile("file4.cpp"),
        gcovr_test_exec.cxx_compile("main.cpp"),
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "--json-pretty",
        "--json=coverage.json",
    )

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        f"--sort={sort}",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()

    gcovr_test_exec.gcovr(
        "--json-add-tracefile=coverage.json",
        f"--sort={sort}",
        "--txt=coverage.txt",
    )
    gcovr_test_exec.compare_txt()
