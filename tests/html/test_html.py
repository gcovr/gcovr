import subprocess  # nosec
import typing

import pytest

from tests.conftest import GcovrTestExec

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
    GcovrTestExec.cc_version() >= (8 if GcovrTestExec.is_gcc() else 13),
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
    process = gcovr_test_exec.gcovr(
        "--gcov-keep", "--html-details", "--html", "coverage.html"
    )
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
        "--html-css=template_dir/style.css",
        "--html-template-dir=template_dir/config/",
        "--html=coverage.html",
    )
    gcovr_test_exec.compare_html()
