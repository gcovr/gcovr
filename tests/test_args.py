#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.6+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2026 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

"""Tests for arguments processing."""

import logging
import platform
import re
import sys
import textwrap
import typing
from pathlib import Path

import pytest

from gcovr.data_model.coverage import FileCoverage
from gcovr.data_model.version import FORMAT_VERSION
from gcovr.version import __version__
from tests.conftest import GCOVR_ISOLATED_TEST

if typing.TYPE_CHECKING:
    from tests.conftest import GcovrExecFixture


def test_version(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--version", exitcode_ok=0)
    assert gcovr_exec.err == ""
    assert gcovr_exec.out.startswith(f"gcovr {__version__}")


def test_help(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("-h", exitcode_ok=0)
    assert gcovr_exec.err == ""
    assert gcovr_exec.out.startswith("usage: gcovr [options]")


def test_empty_root(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("-r", "", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "argument -r/--root: Should not be set to an empty string." in gcovr_exec.err


def test_empty_exclude(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--exclude", "", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "filter cannot be empty" in gcovr_exec.err


def test_empty_exclude_directory(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--exclude-directory", "", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "filter cannot be empty" in gcovr_exec.err


def test_empty_objdir(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--gcov-object-directory", "", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert (
        "argument --gcov-object-directory/--object-directory: Should not be set to an empty string."
        in gcovr_exec.err
    )


def test_invalid_objdir(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--gcov-object-directory", "not-existing-dir", exitcode_ok=1)
    gcovr_exec.check_log(
        (logging.ERROR, "Bad --gcov-object-directory option."),
        compare="startswith",
    )


def helper_test_non_existing_directory_output(
    gcovr_exec: "GcovrExecFixture", option: str
) -> None:
    gcovr_exec.gcovr(option, "not-existing-dir/file.txt", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert (
        "Could not create output file 'not-existing-dir/file.txt': " in gcovr_exec.err
    )


def test_non_existing_directory_output(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_output(gcovr_exec, "--output")


def test_non_existing_directory_txt(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_output(gcovr_exec, "--txt")


def test_non_existing_directory_xml(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_output(gcovr_exec, "--xml")


def test_non_existing_directory_html(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_output(gcovr_exec, "--html")


def test_non_existing_directory_html_details(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    helper_test_non_existing_directory_output(gcovr_exec, "--html-details")


def test_non_existing_directory_html_nested(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    helper_test_non_existing_directory_output(gcovr_exec, "--html-nested")


def test_non_existing_directory_sonarqube(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_output(gcovr_exec, "--sonarqube")


def test_non_existing_directory_json(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_output(gcovr_exec, "--json")


def test_non_existing_directory_csv(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_output(gcovr_exec, "--csv")


def helper_test_non_existing_directory_2_output(
    gcovr_exec: "GcovrExecFixture", option: str
) -> None:
    gcovr_exec.gcovr(option, "not-existing-dir/subdir/", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert (
        "Could not create output directory 'not-existing-dir/subdir/': "
        in gcovr_exec.err
    )


def test_non_existing_directory_2_output(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_2_output(gcovr_exec, "--output")


def test_non_existing_directory_2_txt(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_2_output(gcovr_exec, "--txt")


def test_non_existing_directory_2_xml(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_2_output(gcovr_exec, "--xml")


def test_non_existing_directory_2_html(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_2_output(gcovr_exec, "--html")


def test_non_existing_directory_2_html_details(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    helper_test_non_existing_directory_2_output(gcovr_exec, "--html-details")


def test_non_existing_directory_2_html_nested(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    helper_test_non_existing_directory_2_output(gcovr_exec, "--html-nested")


def test_non_existing_directory_2_sonarqube(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    helper_test_non_existing_directory_2_output(gcovr_exec, "--sonarqube")


def test_non_existing_directory_2_json(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_2_output(gcovr_exec, "--json")


def test_non_existing_directory_2_csv(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_existing_directory_2_output(gcovr_exec, "--csv")


def helper_test_non_writable_directory_output(
    gcovr_exec: "GcovrExecFixture", option: str
) -> None:
    gcovr_exec.gcovr(option, "/file.txt", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "Could not create output file '/file.txt': " in gcovr_exec.err


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_output(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_writable_directory_output(gcovr_exec, "--output")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_txt(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_writable_directory_output(gcovr_exec, "--txt")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_xml(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_writable_directory_output(gcovr_exec, "--xml")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_html(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_writable_directory_output(gcovr_exec, "--html")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_html_details(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    helper_test_non_writable_directory_output(gcovr_exec, "--html-details")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_html_nested(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    helper_test_non_writable_directory_output(gcovr_exec, "--html-nested")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_sonarqube(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_writable_directory_output(gcovr_exec, "--sonarqube")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_json(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_writable_directory_output(gcovr_exec, "--json")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_csv(gcovr_exec: "GcovrExecFixture") -> None:
    helper_test_non_writable_directory_output(gcovr_exec, "--csv")


def test_stdout_no_html_self_contained(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--output", "-", "--no-html-self-contained", exitcode_ok=1)
    gcovr_exec.check_log(
        (logging.ERROR, "only self contained reports can be printed to STDOUT")
    )


def test_no_output_html_details(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--html-details", exitcode_ok=1)
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "a named output must be given, if the option --html-details is used.",
        )
    )


def test_stdout_html_details(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--html-details", "-", exitcode_ok=1)
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "detailed reports can only be printed to STDOUT as --html-single-page.",
        )
    )


def test_no_output_html_nested(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--html-nested", exitcode_ok=1)
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "a named output must be given, if the option --html-nested is used.",
        )
    )


def test_stdout_html_nested(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--html-nested", "-", exitcode_ok=1)
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "detailed reports can only be printed to STDOUT as --html-single-page.",
        )
    )


def test_html_details_and_html_nested(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--output", "x", "--html-details", "--html-nested", exitcode_ok=1)
    gcovr_exec.check_log(
        (logging.ERROR, "--html-details and --html-nested can not be used together.")
    )


def test_html_single_page_without_html_details_or_html_nested(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    gcovr_exec.gcovr("--output", "x", "--html-single-page", exitcode_ok=1)
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "option --html-details or --html-nested is needed, if the option --html-single-page is used.",
        )
    )


@pytest.mark.parametrize(
    "option",
    [
        "--fail-under-line",
        "--fail-under-branch",
        "--fail-under-condition-or-decision",
        "--fail-under-condition",
        "--fail-under-decision",
        "--fail-under-function",
    ],
)
def test_failed_under_threshold_nan(
    gcovr_exec: "GcovrExecFixture", option: str
) -> None:
    gcovr_exec.gcovr(option, "nan", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "not in range [0.0, 100.0]" in gcovr_exec.err


@pytest.mark.parametrize(
    "option",
    [
        "--fail-under-line",
        "--fail-under-branch",
        "--fail-under-condition-or-decision",
        "--fail-under-condition",
        "--fail-under-decision",
        "--fail-under-function",
    ],
)
def test_failed_under_threshold_negative(
    gcovr_exec: "GcovrExecFixture", option: str
) -> None:
    gcovr_exec.gcovr(option, "-0.1", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "not in range [0.0, 100.0]" in gcovr_exec.err


@pytest.mark.parametrize(
    "option",
    [
        "--fail-under-line",
        "--fail-under-branch",
        "--fail-under-condition-or-decision",
        "--fail-under-condition",
        "--fail-under-decision",
        "--fail-under-function",
    ],
)
def test_failed_under_threshold_100_1(
    gcovr_exec: "GcovrExecFixture", option: str
) -> None:
    gcovr_exec.gcovr(option, "100.1", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "not in range [0.0, 100.0]" in gcovr_exec.err


def test_filter_backslashes_are_detected(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    # gcov-exclude all to prevent any coverage data from being found
    gcovr_exec.gcovr(
        "--filter",
        r"C:\\foo\moo",
        "--gcov-exclude",
        "",
        exitcode_ok=1,
    )
    gcovr_exec.check_log(
        (
            logging.WARNING,
            "Filters must use forward slashes as path separators, your filter >>C:\\\\foo\\moo<<.",
        ),
        (logging.WARNING, "Did you mean >>C:/foo/moo<<?"),
        (
            logging.ERROR,
            "Error setting up filter --filter='C:\\\\foo\\moo': bad escape \\m at position 7",
        ),
        compare="startswith",
    )


def test_html_css_not_exists(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--html-css", "/File/does/not/\texist", exitcode_ok=1)
    if platform.system() == "Windows":
        pattern = r"\\\\File\\\\does\\\\not\\\\\\texist"
        # Starting with 3.13 a path starting with a leading (back)slash isn't considered
        # as absolute anymore by os.path.isabs and we add the current working directory
        if sys.version_info >= (3, 13):
            pattern = rf"[A-Z]:(?:\\\\[^\\]+)*?{pattern}"
    else:
        pattern = r"/File/does/not/\\texist"
    assert gcovr_exec.out == ""
    assert (
        re.search(
            rf"Should be a file that already exists: '{pattern}'",
            gcovr_exec.err,
        )
        is not None
    )


def test_html_title_empty_string(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--html-title", "", exitcode_ok=1)
    gcovr_exec.check_log((logging.ERROR, "An empty --html-title= is not allowed."))


def test_medium_threshold_nan(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--medium-threshold", "nan", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert (
        "--medium-threshold/--html-medium-threshold: nan not in range [0.0, 100.0]"
        in gcovr_exec.err
    )


def test_medium_threshold_negative(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--medium-threshold", "-0.1", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "not in range [0.0, 100.0]" in gcovr_exec.err


def test_medium_threshold_zero(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--medium-threshold", "0.0", exitcode_ok=1)
    gcovr_exec.check_log(
        (logging.ERROR, "Value of --medium-threshold should not be zero.")
    )


def test_high_threshold_nan(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--high-threshold", "nan", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "not in range [0.0, 100.0]" in gcovr_exec.err


def test_high_threshold_negative(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--high-threshold", "-0.1", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "not in range [0.0, 100.0]" in gcovr_exec.err


def test_medium_threshold_gt_high_threshold(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    gcovr_exec.gcovr(
        "--medium-threshold", "60", "--high-threshold", "50", exitcode_ok=1
    )
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "Value of --medium-threshold=60.0 should be\nlower than or equal to the value of --high-threshold=50.0.",
        )
    )


def test_html_tab_size_zero(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--html-tab-size", "0", exitcode_ok=1)
    gcovr_exec.check_log(
        (logging.ERROR, "Value of --html-tab-size should be greater 0.")
    )


def test_multiple_output_formats_to_stdout(gcovr_exec: "GcovrExecFixture") -> None:
    """Test to check if a output file is missing."""
    gcovr_exec.gcovr(
        "--coveralls",
        "--cobertura",
        "--csv",
        "--html",
        "--jacoco",
        "--json",
        "--json-summary",
        "--sonarqube",
        "--txt",
        "--root",
        ".",
    )

    gcovr_exec.check_log(
        (
            logging.WARNING,
            "All coverage data is filtered out. Please check your paths and filters.",
        ),
        *(
            (
                logging.WARNING,
                f"{format_name} output skipped - consider providing an output file with `{option}=OUTPUT`.",
            )
            for format_name, option in [
                ("Coveralls", "--coveralls"),
                ("CSV", "--csv"),
                ("HTML", "--html"),
                ("JaCoCo", "--jacoco"),
                ("JSON", "--json"),
                ("JSON summary", "--json-summary"),
                ("SonarQube", "--sonarqube"),
                ("Text", "--txt"),
            ]
        ),
    )


def test_multiple_output_formats_to_stdout_1(gcovr_exec: "GcovrExecFixture") -> None:
    """Test to check if a output file is missing."""
    gcovr_exec.gcovr(
        "--coveralls",
        "--cobertura",
        "--csv",
        "--html",
        "--jacoco",
        "--json",
        "--json-summary",
        "--sonarqube",
        "--txt",
        "-o",
        "-",
        "--root",
        ".",
    )
    gcovr_exec.check_log(
        (
            logging.WARNING,
            "All coverage data is filtered out. Please check your paths and filters.",
        ),
        *(
            (
                logging.WARNING,
                f"{format_name} output skipped - consider providing an output file with `{option}=OUTPUT`.",
            )
            for format_name, option in [
                ("Coveralls", "--coveralls"),
                ("CSV", "--csv"),
                ("HTML", "--html"),
                ("JaCoCo", "--jacoco"),
                ("JSON", "--json"),
                ("JSON summary", "--json-summary"),
                ("SonarQube", "--sonarqube"),
                ("Text", "--txt"),
            ]
        ),
    )


def test_no_self_contained_without_file(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--no-html-self-contained", "--html", exitcode_ok=1)
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "can only disable --html-self-contained when a named output is given.",
        )
    )


def test_html_injection_via_json(
    gcovr_exec: "GcovrExecFixture", tmp_path: Path
) -> None:
    import json  # noqa: PLC0415

    import markupsafe  # noqa: PLC0415

    script = '<script>alert("pwned")</script>'
    json_data = {
        "gcovr/format_version": FORMAT_VERSION,
        "files": [
            {"file": script, "functions": [], "lines": []},
            {"file": "other", "functions": [], "lines": []},
        ],
    }

    tempfile = tmp_path / "injection.json"

    with tempfile.open("w+") as json_file:
        json.dump(json_data, json_file)

    gcovr_exec.gcovr("-a", str(tempfile), "--html")

    assert script not in gcovr_exec.out
    assert str(markupsafe.escape(script)) in gcovr_exec.out, (
        f"--- got:\n{gcovr_exec.out}\n---"
    )


def test_import_valid_cobertura_file(tmp_path: Path) -> None:
    from gcovr.configuration import merge_options_and_set_defaults  # noqa: PLC0415
    from gcovr.formats import read_reports  # noqa: PLC0415

    testfile = "code.cpp"
    xml_data = f"""<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE coverage SYSTEM 'https://github.com/cobertura/cobertura/blob/e5eea8679ebce047ec6ccdfdbf6cf2c14b376875/cobertura/src/site/htdocs/xml/coverage-04.dtd'>
<coverage
    line-rate="0.9"
    branch-rate="0.75"
    lines-covered="9"
    lines-valid="10"
    branches-covered="3"
    branches-valid="4"
    complexity="0.0"
    timestamp=""
    version="gcovr 7.1">
  <sources>
    <source>{tmp_path}</source>
  </sources>
  <packages>
    <package name="source" line-rate="0.9" branch-rate="0.75" complexity="0.0">
      <classes>
        <class name="code_cpp" filename="code.cpp" line-rate="0.9" branch-rate="0.75" complexity="0.0">
          <methods/>
          <lines>
            <line number="3" hits="3" branch="false"/>
            <line number="4" hits="3" branch="true" condition-coverage="100% (2/2)">
              <conditions>
                <condition number="0" type="jump" coverage="100%"/>
              </conditions>
            </line>
            <line number="5" hits="2" branch="false"/>
            <line number="7" hits="1" branch="false"/>
            <line number="9" hits="3" branch="false"/>
            <line number="12" hits="2" branch="false"/>
            <line number="13" hits="2" branch="true" condition-coverage="50% (1/2)">
              <conditions>
                <condition number="0" type="jump" coverage="50%"/>
              </conditions>
            </line>
            <line number="14" hits="2" branch="false"/>
            <line number="16" hits="0" branch="false"/>
            <line number="18" hits="2" branch="false"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
    """
    tempfile = tmp_path / "valid_cobertura.xml"
    with tempfile.open("w+") as fp:
        fp.write(xml_data)

    filename = str(tempfile)
    opts = merge_options_and_set_defaults(
        [
            {
                "cobertura_tracefile": [filename],
                "include_filter": [re.compile(".")],
                "root": str(tmp_path),
            }
        ]
    )
    opts.include_filter = tuple(opts.include_filter)
    covdata = read_reports(opts)
    assert covdata is not None
    testfile = str(Path(tmp_path, testfile))
    assert testfile in covdata
    cov = covdata[testfile]
    assert isinstance(cov, FileCoverage)
    assert len(list(cov.lines())) == 10  # noqa: PLR2004
    for line, count, branches in [
        (7, 1, None),
        (9, 3, None),
        (16, 0, None),
        (13, 2, [1, 0]),
    ]:
        linecovs = cov.get_line(line)
        assert linecovs is not None
        assert linecovs.count == count
        branchcov_list = list(linecovs[""].branches())
        if branches is not None:
            assert len(branchcov_list) == len(branches)
            for branch_idx, branch_count in enumerate(branches):
                matching_branch = [
                    branchcov
                    for branchcov in branchcov_list
                    if branchcov.key == (branch_idx, -1, -1)
                ]
                assert len(matching_branch) == 1
                assert matching_branch[0].count == branch_count
        else:
            assert len(branchcov_list) == 0


def test_invalid_cobertura_file(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr(
        "--cobertura-add-tracefile",
        "/*.FileDoesNotExist.*",
        exitcode_ok=64,
    )
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "Bad --covertura-add-tracefile option.\n\tThe specified file does not exist.",
        ),
        compare="contains",
    )


def test_import_corrupt_cobertura_file(
    gcovr_exec: "GcovrExecFixture", tmp_path: Path
) -> None:
    xml_data = "Invalid XML content"
    tempfile = tmp_path / "corrupt_cobertura.xml"
    with tempfile.open("w+") as fp:
        fp.write(xml_data)

    gcovr_exec.gcovr(
        "--cobertura-add-tracefile",
        str(tempfile),
        exitcode_ok=64,
    )
    gcovr_exec.check_log((logging.ERROR, "Start tag expected"), compare="contains")


def test_import_cobertura_file_with_invalid_line(
    gcovr_exec: "GcovrExecFixture", tmp_path: Path
) -> None:
    xml_data = """<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE coverage SYSTEM 'https://github.com/cobertura/cobertura/blob/e5eea8679ebce047ec6ccdfdbf6cf2c14b376875/cobertura/src/site/htdocs/xml/coverage-04.dtd'>
<coverage
    line-rate="0.9"
    branch-rate="0.75"
    lines-covered="9"
    lines-valid="10"
    branches-covered="3"
    branches-valid="4"
    complexity="0.0"
    timestamp=""
    version="gcovr 7.1">
  <sources>
    <source>.</source>
  </sources>
  <packages>
    <package name="source" line-rate="0.9" branch-rate="0.75" complexity="0.0">
      <classes>
        <class name="code_cpp" filename="/path/to/source/code.cpp" line-rate="0.9" branch-rate="0.75" complexity="0.0">
          <methods/>
          <lines>
            <line number="3" hits="3" branch="false"/>
            <line number="NoNumber" branch="true" condition-coverage="100% (2/2)" />
            <line number="18" hits="2" branch="false"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
    """
    tempfile = tmp_path / "cobertura_invalid_line.xml"
    with tempfile.open("w+") as fp:
        fp.write(xml_data)

    gcovr_exec.gcovr(
        "--cobertura-add-tracefile",
        str(tempfile),
        "--filter",
        ".",
        exitcode_ok=64,
    )
    gcovr_exec.check_log(
        (logging.ERROR, "'number' attribute is required and must be an integer"),
        compare="contains",
    )


@pytest.mark.parametrize(
    "option",
    [
        "--filter",
        "--exclude",
        "--include",
        "--gcov-filter",
        "--gcov-exclude",
        "--exclude-directory",
        "--trace-include",
        "--trace-exclude",
        "--exclude-lines-by-pattern",
        "--exclude-branches-by-pattern",
    ],
)
def test_exclude_filter(gcovr_exec: "GcovrExecFixture", option: str) -> None:
    gcovr_exec.gcovr(option, "example.**", exitcode_ok=1)
    gcovr_exec.check_log(
        (
            logging.ERROR,
            f"Error setting up {'pattern' if 'pattern' in option else 'filter'} {option}='example.**': multiple repeat at position 9",
        ),
        compare="startswith",
    )


@pytest.mark.parametrize(
    "option",
    [
        "--exclude-function",
        "--exclude-lines-by-pattern",
        "--exclude-branches-by-pattern",
    ],
)
def test_exclude_pattern(gcovr_exec: "GcovrExecFixture", option: str) -> None:
    gcovr_exec.gcovr(
        option,
        "/example.**/" if option == "--exclude-function" else "example.**",
        exitcode_ok=1,
    )
    gcovr_exec.check_log(
        (
            logging.ERROR,
            f"Error setting up pattern {option}='example.**': multiple repeat at position 9",
        ),
        compare="startswith",
    )


def test_invalid_timestamp(gcovr_exec: "GcovrExecFixture") -> None:
    gcovr_exec.gcovr("--timestamp=foo", exitcode_ok=1)
    assert gcovr_exec.out == ""
    assert "argument --timestamp: unknown timestamp format: 'foo'" in gcovr_exec.err


def test_sort_branch_and_not_uncovered_or_percent(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    gcovr_exec.gcovr("--sort-branches", exitcode_ok=1)
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "The options --sort-branches without '--sort uncovered-number' or '--sort uncovered-percent' doesn't make sense.",
        ),
        compare="startswith",
    )


@pytest.mark.parametrize(
    "option",
    [
        ("--sort-uncovered", "--sort uncovered-number"),
        ("--sort-percentage", "--sort uncovered-percent"),
    ],
    ids=lambda option: option[0],
)
def test_deprecated_option(
    gcovr_exec: "GcovrExecFixture", option: tuple[str, str]
) -> None:
    gcovr_exec.gcovr(option[0], "--help")
    gcovr_exec.check_log(
        (
            logging.WARNING,
            f"Deprecated option {option[0]} used, please use {option[1]!r} instead.",
        )
    )


def test_lcov_report_name_with_spaces(gcovr_exec: "GcovrExecFixture") -> None:
    """Test error if report name contains spaces."""
    gcovr_exec.gcovr(
        "--lcov-test-name",
        "Name with spaces",
        exitcode_ok=1,
    )
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "The LCOV test name must not contain spaces, got 'Name with spaces'.",
        )
    )


@pytest.mark.parametrize(
    ("name", "option"),
    [
        pytest.param(name, f"--{name.lower()}", id=name)
        for name in [
            "Clover",
            "Cobertura",
            "Coveralls",
            "CSV",
            "JaCoCo",
            "LCOV",
            "Markdown",
            "SonarQube",
        ]
    ],
)
def test_json_compare_not_possible_option(
    gcovr_exec: "GcovrExecFixture", name: str, option: str
) -> None:
    """Test if a report is not possible with --json-compare."""
    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage_1.json",
        "--json-add-tracefile=coverage_2.json",
        "--json-compare",
        option,
        exitcode_ok=1,
    )
    gcovr_exec.check_log(
        (logging.ERROR, f"A {name} report is not possible with --json-compare.")
    )


def test_json_compare_with_several_text_metrics(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    """Test if a report is not possible with --json-compare."""
    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage_1.json",
        "--json-add-tracefile=coverage_2.json",
        "--json-compare",
        "--txt-metric=line",
        "--txt-metric=branch",
        "--txt",
        exitcode_ok=1,
    )
    gcovr_exec.check_log(
        (
            logging.ERROR,
            "A txt report with several metrics is not possible with --json-compare.",
        )
    )


def test_json_compare_with_several_cobertura_tracefile(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    """Test if a report is not possible with --json-compare."""
    gcovr_exec.gcovr(
        "--json-add-tracefile=coverage_1.json",
        "--json-add-tracefile=coverage_2.json",
        "--cobertura-add-tracefile=coverage_1.json",
        "--json-compare",
        "--txt",
        exitcode_ok=1,
    )
    gcovr_exec.check_log(
        (logging.ERROR, "A Cobertura tracefile is not possible with --json-compare.")
    )


def test_json_tracefile_with_useless_option(
    gcovr_exec: "GcovrExecFixture",
) -> None:
    """Test if a report is not possible with --json-compare."""
    coverage_json = gcovr_exec.output_dir / "coverage_in.json"
    coverage_json.write_text(
        textwrap.dedent("""\
            {
                "gcovr/format_version": "0.15",
                "files": []
            }
            """),
        encoding="UTF-8",
    )

    options_with_no_effect = [
        "--exclude-directory=.*",
        "--exclude-noncode-lines",
        "--exclude-throw-branches",
        "--exclude-unreachable-branches",
        "--exclude-function-lines",
        "--exclude-function=xxx",
        "--exclude-lines-by-pattern=.*",
        "--exclude-branches-by-pattern=.*",
        "--warn-excluded-lines-with-hits",
        "--gcov-allowed-working-directory-root=.*",
        "--include-internal-functions",
        "--no-markers",
    ]
    gcovr_exec.gcovr(
        f"--json-add-tracefile={coverage_json}",
        *options_with_no_effect,
        "--json-pretty",
        "--json=coverage.json",
    )
    gcovr_exec.check_log(
        *(
            (
                logging.WARNING,
                f"Option {option.split('=', maxsplit=1)[0]} has no effect when generating reports from tracefiles.",
            )
            for option in options_with_no_effect
        ),
        (
            logging.WARNING,
            "All coverage data is filtered out. Please check your paths and filters.",
        ),
    )
