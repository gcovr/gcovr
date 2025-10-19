import platform
import typing

import pytest

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrTestExec

PARAMETERS = [
    (
        "sort-none",
        [
            "--html-nested=./",
        ],
    ),
    (
        "filter",
        [
            "--filter",
            "subdir/A",
            "--html-nested=./",
        ],
    ),
    (
        "sort-uncovered-percentage",
        [
            "--sort",
            "uncovered-percent",
            "--html-nested=coverage.html",
        ],
    ),
    (
        "sort-uncovered-number",
        [
            "--sort",
            "uncovered-number",
            "--html-nested=coverage.html",
        ],
    ),
    (
        "default-theme-static",
        (
            "--filter",
            "subdir/A",
            "--html-details=./",
            "--html-single-page=static",
            "--no-html-self-contained",
        ),
    ),
    (
        "default-theme-js",
        (
            "--filter",
            "subdir/A",
            "--html-details=./",
            "--html-single-page",
        ),
    ),
    (
        "github-theme-static",
        (
            "--filter",
            "subdir/A",
            "--html-details=./",
            "--html-single-page",
            "--html-theme",
            "github.blue",
            "--no-html-self-contained",
        ),
    ),
    (
        "github-theme-js",
        (
            "--filter",
            "subdir/A",
            "--html-details=./",
            "--html-single-page=static",
            "--html-theme",
            "github.blue",
        ),
    ),
]


@pytest.mark.skipif(
    platform.system() != "Linux",
    reason="The nested report generation is independent of OS and we do not want to have separate data wor Windows and Darwin.",
)
@pytest.mark.parametrize(
    "_test_id,options",
    PARAMETERS,
    ids=[p[0] for p in PARAMETERS],
)
def test(
    gcovr_test_exec: "GcovrTestExec", _test_id: str, options: typing.List[str]
) -> None:
    """This test case tests the output of cascaded html coverage
    reports.

    It will test that a directory with items in it properly
    aggregates the statistics within it, all the sorting works for
    each directory, any flattening of directories that have a single
    entry, and the writing of source files within each directory.

    In this case, the directory listings should be unsorted.
    """

    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File2.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
    )

    gcovr_test_exec.run("./subdir/testcase")
    gcovr_test_exec.gcovr(
        "-r",
        "subdir",
        *options,
    )
    gcovr_test_exec.compare_html()
