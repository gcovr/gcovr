import logging
import os
import subprocess  # nosec
import typing

import pytest

from gcovr.formats.html.write import _make_short_source_filename
from tests.conftest import IS_LINUX, IS_WINDOWS, GcovrTestExec


@pytest.mark.parametrize(
    "outfile,source_filename",
    [
        ("../gcovr", "C:\\other_dir\\project\\source.c"),
        ("../gcovr/", "C:\\other_dir\\project\\source.c"),
        ("..\\gcovr", "C:\\other_dir\\project\\source.c"),
        ("..\\gcovr\\", "C:\\other_dir\\project\\source.c"),
        (
            "..\\gcovr",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        ("..\\gcovr\\result.html", "C:\\other_dir\\project\\source.c"),
        (
            "..\\gcovr\\result",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        (
            "C:\\gcovr",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        (
            "C:/gcovr",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        (
            "C:/gcovr_files",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
    ],
)
@pytest.mark.skipif(not IS_WINDOWS, reason="Only for Windows")
def test_windows_make_short_source_filename(outfile: str, source_filename: str) -> None:
    CurrentDrive = os.getcwd()[0:1]
    outfile = outfile.replace("C:", CurrentDrive)
    source_filename = source_filename.replace("C:", CurrentDrive)

    result = _make_short_source_filename(outfile, source_filename)
    logging.info("=" * 100)
    logging.info(outfile)
    logging.info(source_filename)
    logging.info(result)
    assert (
        ":" not in result
        or (  # nosec
            result.startswith(CurrentDrive) and ":" not in result[2:]
        )
    )

    assert len(result) < 256  # nosec


PARAMETERS = [
    (
        "details",
        ("--html-details",),
    ),
    (
        "high-75",
        ("--html-details", "--high-threshold=75.0"),
    ),
    (
        "high-100",
        ("--html-details", "--high-threshold=100.0"),
    ),
    (
        "medium-50",
        ("--html-details", "--medium-threshold=50.0"),
    ),
    (
        "medium-100-high-100",
        ("--html-details", "--medium-threshold=100.0", "--high-threshold=100.0"),
    ),
    (
        "no-syntax-highlighting",
        ("--html-details", "--no-html-details-syntax-highlighting"),
    ),
    (
        "css",
        ("--html-self-contained", "--html-css=config/style.css"),
    ),
    (
        "css-with-pygments",
        ("--html-self-contained", "--html-css=config/style_with_pygments.css"),
    ),
    (
        "tab-size-2",
        ("--no-html-self-contained", "--html-tab-size=2"),
    ),
    (
        "title",
        ("--html-details", "--html-title=Title of report"),
    ),
    (
        "line-branch-threshold",
        (
            "--html-details",
            "--high-threshold=75.0",
            "--medium-threshold-branch=74",
            "--medium-threshold-line=70",
            "--high-threshold-line=70",
        ),
    ),
    (
        "theme-default-green",
        (
            "--html-details",
            "--html-block-ids",
            "--html-theme=green",
        ),
    ),
    (
        "theme-default-blue",
        (
            "--html-details",
            "--html-block-ids",
            "--html-theme=blue",
        ),
    ),
    (
        "theme-github-green",
        (
            "--html-details",
            "--html-block-ids",
            "--html-theme=github.green",
        ),
    ),
    (
        "theme-github-dark-green",
        (
            "--html-details",
            "--html-block-ids",
            "--html-theme=github.dark-green",
        ),
    ),
    (
        "theme-github-blue",
        (
            "--html-details",
            "--html-block-ids",
            "--html-theme=github.blue",
        ),
    ),
    (
        "theme-github-dark-blue",
        (
            "--html-details",
            "--html-block-ids",
            "--html-theme=github.dark-blue",
        ),
    ),
]


@pytest.mark.parametrize(
    "_test_id,options",
    PARAMETERS,
    ids=[p[0] for p in PARAMETERS],
)
def test(
    gcovr_test_exec: "GcovrTestExec", _test_id: str, options: typing.List[str]
) -> None:
    """Test HTML single page output variants."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr("-d", "--html", *options, "--html", "coverage.html")
    gcovr_test_exec.compare_html()


@pytest.mark.skipif(
    GcovrTestExec.cc_version() >= (8 if GcovrTestExec.is_gcc() else 12),
    reason="Newer versions stub the missing lines",
)
def test_less_lines(  # type: ignore[no-untyped-def]
    gcovr_test_exec: "GcovrTestExec",
    check,
) -> None:
    """Test HTML single page output variants."""
    main_cpp = gcovr_test_exec.output_dir / "main.cpp"
    content = main_cpp.read_text(encoding="utf-8")
    main_cpp.write_text(("\n" * 20) + content)

    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    main_cpp.write_text(content)

    gcovr_test_exec.run("./testcase")
    process = gcovr_test_exec.gcovr("--html-details", "--html", "coverage.html")
    with check:
        assert (
            f"(WARNING) File {main_cpp} has 5 line(s) but coverage data has 23 line(s)."
            in process.stderr
        )

    gcovr_test_exec.compare_html()


PARAMETERS_ENCODING = [
    (
        "report-cp1252",
        "utf8",
        "cp1252",
    ),
    (
        "report-iso-8859-15",
        "utf8",
        "iso-8859-15",
    ),
    (
        "source-cp1252",
        "cp1252",
        "utf8",
    ),
    (
        "source-utf8",
        "utf8",
        "utf8",
    ),
]


@pytest.mark.parametrize(
    "_test_id,source_encoding,html_encoding",
    PARAMETERS_ENCODING,
    ids=[p[0] for p in PARAMETERS_ENCODING],
)
def test_encoding(
    gcovr_test_exec: "GcovrTestExec",
    _test_id: str,
    source_encoding: str,
    html_encoding: str,
) -> None:
    """Test HTML single page output variants."""
    (gcovr_test_exec.output_dir / "main.cpp").unlink()
    (gcovr_test_exec.output_dir / f"main.{source_encoding}.cpp").rename(
        gcovr_test_exec.output_dir / "main.cpp"
    )
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    additional_options = (
        [] if html_encoding == "utf8" else [f"--html-encoding={html_encoding}"]
    )
    gcovr_test_exec.gcovr(
        "-d",
        "--html-details",
        "--source-encoding=utf8",
        *additional_options,
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html(encoding=html_encoding)


def test_empty_nested_report(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test HTML report generation without data files."""
    gcovr_test_exec.gcovr(
        "--html-nested=coverage.html",
    )


def test_file_not_found(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test HTML output when file is not found, using tracefile."""
    # No compilation needed, just run gcovr with tracefile

    with pytest.raises(subprocess.CalledProcessError) as exc:
        gcovr_test_exec.gcovr(
            "--json-add-tracefile=file_not_found.json",
            "--html-details=coverage.html",
        )
    assert exc.value.returncode == 128
    gcovr_test_exec.compare_html()


def test_template_dir(gcovr_test_exec: "GcovrTestExec") -> None:
    """Test HTML single page output variants."""
    gcovr_test_exec.cxx_link(
        "testcase",
        "main.cpp",
    )

    gcovr_test_exec.run("./testcase")
    gcovr_test_exec.gcovr(
        "-d",
        "--html",
        "--html-self-contained",
        "--html-css=user_template/style.css",
        "--html-template-dir=user_template/config/",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()


PARAMETERS_NESTED = [
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
            "--html-single-page=static",
            "--html-theme=github.blue",
            "--no-html-self-contained",
        ),
    ),
    (
        "github-theme-js",
        (
            "--filter",
            "subdir/A",
            "--html-details=./",
            "--html-single-page",
            "--html-theme=github.blue",
        ),
    ),
]


@pytest.mark.skipif(
    not IS_LINUX,
    reason="The nested report generation is independent of OS and we do not want to have separate data for Windows and Darwin.",
)
@pytest.mark.parametrize(
    "test_id,options",
    PARAMETERS_NESTED,
    ids=[p[0] for p in PARAMETERS_NESTED],
)
def test_nested(
    gcovr_test_exec: "GcovrTestExec", test_id: str, options: typing.List[str]
) -> None:
    """This test case tests the output of cascaded html coverage
    reports.

    It will test that a directory with items in it properly
    aggregates the statistics within it, all the sorting works for
    each directory, any flattening of directories that have a single
    entry, and the writing of source files within each directory.

    In this case, the directory listings should be unsorted.
    """

    file2_cpp = gcovr_test_exec.output_dir / "subdir" / "A" / "File2.cpp"
    if "-theme-js" in test_id:
        deep_dir = file2_cpp.parent.joinpath(*[f"subdir_{i}" for i in range(0, 10)])
        deep_dir.mkdir(parents=True, exist_ok=True)
        file2_cpp = file2_cpp.rename(deep_dir / file2_cpp.name)
    gcovr_test_exec.cxx_link(
        "subdir/testcase",
        gcovr_test_exec.cxx_compile("subdir/A/file1.cpp"),
        gcovr_test_exec.cxx_compile(
            file2_cpp.relative_to(gcovr_test_exec.output_dir).as_posix()
        ),
        gcovr_test_exec.cxx_compile("subdir/A/file3.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/File4.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/file7.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/file5.cpp"),
        gcovr_test_exec.cxx_compile("subdir/A/C/D/File6.cpp"),
        gcovr_test_exec.cxx_compile("subdir/B/main.cpp"),
    )

    gcovr_test_exec.run("./subdir/testcase")
    gcovr_test_exec.gcovr(
        "--root=subdir",
        *options,
    )
    gcovr_test_exec.compare_html()
