# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.4+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2025 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import logging
import os
from pathlib import Path
import platform
import sys
import re

import pytest

from gcovr.__main__ import main
from gcovr.version import __version__
from gcovr.data_model.version import FORMAT_VERSION


GCOVR_ISOLATED_TEST = os.getenv("GCOVR_ISOLATED_TEST") == "zkQEVaBpXF1i"


# The CaptureObject class holds the capture method result
class CaptureObject:
    def __init__(self, out: str, err: str, exitcode: int) -> None:
        self.out = out
        self.err = err
        self.exitcode = exitcode


def capture(capsys: pytest.CaptureFixture[str], args: list[str]) -> CaptureObject:
    """The capture method calls the main method and captures its output/error
    streams and exit code."""
    e = main(args)
    out, err = capsys.readouterr()
    return CaptureObject(out, err, e)


# The LogCaptureObject class holds the capture method result
class LogCaptureObject:
    def __init__(
        self, record_tuples: list[tuple[str, int, str]], exitcode: int
    ) -> None:
        self.record_tuples = record_tuples
        self.exitcode = exitcode


def log_capture(caplog: pytest.LogCaptureFixture, args: list[str]) -> LogCaptureObject:
    """The capture method calls the main method and captures its output/error
    streams and exit code."""
    e = main(args)
    return LogCaptureObject(caplog.record_tuples, e)


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--version"])
    assert c.err == ""
    assert c.out.startswith(f"gcovr {__version__}")
    assert c.exitcode == 0


def test_help(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["-h"])
    assert c.err == ""
    assert c.out.startswith("usage: gcovr [options]")
    assert c.exitcode == 0


def test_empty_root(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["-r", ""])
    assert c.out == ""
    assert "argument -r/--root: Should not be set to an empty string." in c.err
    assert c.exitcode != 0


def test_empty_exclude(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--exclude", ""])
    assert c.out == ""
    assert "filter cannot be empty" in c.err
    assert c.exitcode != 0


def test_empty_exclude_directory(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--gcov-exclude-directory", ""])
    assert c.out == ""
    assert "filter cannot be empty" in c.err
    assert c.exitcode != 0


def test_empty_objdir(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--gcov-object-directory", ""])
    assert c.out == ""
    assert (
        "argument --gcov-object-directory/--object-directory: Should not be set to an empty string."
        in c.err
    )
    assert c.exitcode != 0


def test_invalid_objdir(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--gcov-object-directory", "not-existing-dir"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2].startswith("Bad --gcov-object-directory option.")
    assert c.exitcode == 1


def helper_test_non_existing_directory_output(
    capsys: pytest.CaptureFixture[str], option: str
) -> None:
    c = capture(capsys, [option, "not-existing-dir/file.txt"])
    assert c.out == ""
    assert "Could not create output file 'not-existing-dir/file.txt': " in c.err
    assert c.exitcode != 0


def test_non_existing_directory_output(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_output(capsys, "--output")


def test_non_existing_directory_txt(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_output(capsys, "--txt")


def test_non_existing_directory_xml(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_output(capsys, "--xml")


def test_non_existing_directory_html(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_output(capsys, "--html")


def test_non_existing_directory_html_details(
    capsys: pytest.CaptureFixture[str],
) -> None:
    helper_test_non_existing_directory_output(capsys, "--html-details")


def test_non_existing_directory_html_nested(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_output(capsys, "--html-nested")


def test_non_existing_directory_sonarqube(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_output(capsys, "--sonarqube")


def test_non_existing_directory_json(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_output(capsys, "--json")


def test_non_existing_directory_csv(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_output(capsys, "--csv")


def helper_test_non_existing_directory_2_output(
    capsys: pytest.CaptureFixture[str], option: str
) -> None:
    c = capture(capsys, [option, "not-existing-dir/subdir/"])
    assert c.out == ""
    assert "Could not create output directory 'not-existing-dir/subdir/': " in c.err
    assert c.exitcode != 0


def test_non_existing_directory_2_output(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_2_output(capsys, "--output")


def test_non_existing_directory_2_txt(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_2_output(capsys, "--txt")


def test_non_existing_directory_2_xml(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_2_output(capsys, "--xml")


def test_non_existing_directory_2_html(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_2_output(capsys, "--html")


def test_non_existing_directory_2_html_details(
    capsys: pytest.CaptureFixture[str],
) -> None:
    helper_test_non_existing_directory_2_output(capsys, "--html-details")


def test_non_existing_directory_2_html_nested(
    capsys: pytest.CaptureFixture[str],
) -> None:
    helper_test_non_existing_directory_2_output(capsys, "--html-nested")


def test_non_existing_directory_2_sonarqube(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_2_output(capsys, "--sonarqube")


def test_non_existing_directory_2_json(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_2_output(capsys, "--json")


def test_non_existing_directory_2_csv(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_existing_directory_2_output(capsys, "--csv")


def helper_test_non_writable_directory_output(
    capsys: pytest.CaptureFixture[str], option: str
) -> None:
    c = capture(capsys, [option, "/file.txt"])
    assert c.out == ""
    assert "Could not create output file '/file.txt': " in c.err
    assert c.exitcode != 0


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_output(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_writable_directory_output(capsys, "--output")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_txt(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_writable_directory_output(capsys, "--txt")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_xml(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_writable_directory_output(capsys, "--xml")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_html(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_writable_directory_output(capsys, "--html")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_html_details(
    capsys: pytest.CaptureFixture[str],
) -> None:
    helper_test_non_writable_directory_output(capsys, "--html-details")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_html_nested(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_writable_directory_output(capsys, "--html-nested")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_sonarqube(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_writable_directory_output(capsys, "--sonarqube")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_json(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_writable_directory_output(capsys, "--json")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_csv(capsys: pytest.CaptureFixture[str]) -> None:
    helper_test_non_writable_directory_output(capsys, "--csv")


def test_stdout_no_html_self_contained(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--output", "-", "--no-html-self-contained"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2] == "only self contained reports can be printed to STDOUT"
    assert c.exitcode != 0


def test_no_output_html_details(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--html-details"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "a named output must be given, if the option --html-details is used."
    )
    assert c.exitcode != 0


def test_stdout_html_details(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--html-details", "-"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "detailed reports can only be printed to STDOUT as --html-single-page."
    )
    assert c.exitcode != 0


def test_no_output_html_nested(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--html-nested"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "a named output must be given, if the option --html-nested is used."
    )
    assert c.exitcode != 0


def test_stdout_html_nested(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--html-nested", "-"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "detailed reports can only be printed to STDOUT as --html-single-page."
    )
    assert c.exitcode != 0


def test_html_details_and_html_nested(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--output", "x", "--html-details", "--html-nested"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2] == "--html-details and --html-nested can not be used together."
    assert c.exitcode != 0


def test_html_single_page_without_html_details_or_html_nested(
    caplog: pytest.LogCaptureFixture,
) -> None:
    c = log_capture(caplog, ["--output", "x", "--html-single-page"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "option --html-details or --html-nested is needed, if the option --html-single-page is used."
    )
    assert c.exitcode != 0


@pytest.mark.parametrize(
    "option",
    [
        "--fail-under-line",
        "--fail-under-branch",
        "--fail-under-decision",
        "--fail-under-function",
    ],
)
def test_failed_under_threshold_nan(
    option: str, capsys: pytest.CaptureFixture[str]
) -> None:
    c = capture(capsys, [option, "nan"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exitcode != 0


@pytest.mark.parametrize(
    "option",
    [
        "--fail-under-line",
        "--fail-under-branch",
        "--fail-under-decision",
        "--fail-under-function",
    ],
)
def test_failed_under_threshold_negative(
    option: str, capsys: pytest.CaptureFixture[str]
) -> None:
    c = capture(capsys, [option, "-0.1"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exitcode != 0


@pytest.mark.parametrize(
    "option",
    [
        "--fail-under-line",
        "--fail-under-branch",
        "--fail-under-decision",
        "--fail-under-function",
    ],
)
def test_failed_under_threshold_100_1(
    option: str, capsys: pytest.CaptureFixture[str]
) -> None:
    c = capture(capsys, [option, "100.1"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exitcode != 0


def test_failed_under_decision_without_active_decision(
    caplog: pytest.LogCaptureFixture,
) -> None:
    c = log_capture(caplog, ["--fail-under-decision", "90"])
    message0 = c.record_tuples[0]
    assert message0[1] == logging.ERROR
    assert message0[2] == "--fail-under-decision need also option --decision."
    assert c.exitcode != 0


def test_filter_backslashes_are_detected(caplog: pytest.LogCaptureFixture) -> None:
    # gcov-exclude all to prevent any coverage data from being found
    c = log_capture(
        caplog,
        args=["--filter", r"C:\\foo\moo", "--gcov-exclude", ""],
    )
    message0 = c.record_tuples[0]
    assert message0[1] == logging.WARNING
    assert message0[2].startswith("filters must use forward slashes as path separators")
    message = c.record_tuples[1]
    assert message[1] == logging.WARNING
    assert message[2].startswith("your filter : C:\\\\foo\\moo")
    message = c.record_tuples[2]
    assert message[1] == logging.WARNING
    assert message[2].startswith("did you mean: C:/foo/moo")
    message = c.record_tuples[3]
    assert message[1] == logging.ERROR
    assert message[2].startswith(
        "Error setting up filter --filter='C:\\\\foo\\moo': bad escape \\m at position 7"
    )


def test_html_css_not_exists(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--html-css", "/File/does/not/\texist"])
    if platform.system() == "Windows":
        pattern = r"\\\\File\\\\does\\\\not\\\\\\texist"
        # Starting with 3.13 a path starting with a leading (back)slash isn't considered
        # as absolute anymore by os.path.isabs and we add the current working directory
        if sys.version_info >= (3, 13):
            pattern = rf"[A-Z]:(?:\\\\[^\\]+)*?{pattern}"
    else:
        pattern = r"/File/does/not/\\texist"
    assert c.out == ""
    assert (
        re.search(
            rf"Should be a file that already exists: '{pattern}'",
            c.err,
        )
        is not None
    )
    assert c.exitcode != 0


def test_html_title_empty_string(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--html-title", ""])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2] == "an empty --html-title= is not allowed."
    assert c.exitcode != 0


def test_medium_threshold_nan(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--medium-threshold", "nan"])
    assert c.out == ""
    assert (
        "--medium-threshold/--html-medium-threshold: nan not in range [0.0, 100.0]"
        in c.err
    )
    assert c.exitcode != 0


def test_medium_threshold_negative(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--medium-threshold", "-0.1"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exitcode != 0


def test_medium_threshold_zero(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--medium-threshold", "0.0"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2] == "value of --medium-threshold should not be zero."
    assert c.exitcode != 0


def test_high_threshold_nan(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--high-threshold", "nan"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exitcode != 0


def test_high_threshold_negative(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--high-threshold", "-0.1"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exitcode != 0


def test_medium_threshold_gt_high_threshold(
    caplog: pytest.LogCaptureFixture,
) -> None:
    c = log_capture(caplog, ["--medium-threshold", "60", "--high-threshold", "50"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "value of --medium-threshold=60.0 should be\nlower than or equal to the value of --high-threshold=50.0."
    )
    assert c.exitcode != 0


def test_html_tab_size_zero(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--html-tab-size", "0"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2] == "value of --html-tab-size= should be greater 0."
    assert c.exitcode != 0


def test_multiple_output_formats_to_stdout(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(
        caplog,
        [
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
            "src/gcovr",
        ],
    )
    for index, text_fragments in enumerate(
        [
            ("Coveralls", "--coveralls"),
            ("CSV", "--csv"),
            ("HTML", "--html"),
            ("JaCoCo", "--jacoco"),
            ("JSON", "--json"),
            ("JSON summary", "--json-summary"),
            ("SonarQube", "--sonarqube"),
            ("Text", "--txt"),
        ]
    ):
        format_name, option = text_fragments
        message = c.record_tuples[index]
        assert message[1] == logging.WARNING
        assert (
            message[2]
            == f"{format_name} output skipped - consider providing an output file with `{option}=OUTPUT`."
        )
    assert c.exitcode == 0


def test_multiple_output_formats_to_stdout_1(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(
        caplog,
        [
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
            "src/gcovr",
        ],
    )
    for index, text_fragments in enumerate(
        [
            ("Coveralls", "--coveralls"),
            ("CSV", "--csv"),
            ("HTML", "--html"),
            ("JaCoCo", "--jacoco"),
            ("JSON", "--json"),
            ("JSON summary", "--json-summary"),
            ("SonarQube", "--sonarqube"),
            ("Text", "--txt"),
        ]
    ):
        format_name, option = text_fragments
        message = c.record_tuples[index]
        assert message[1] == logging.WARNING
        assert (
            message[2]
            == f"{format_name} output skipped - consider providing an output file with `{option}=OUTPUT`."
        )
    assert c.exitcode == 0


def test_no_self_contained_without_file(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--no-html-self-contained", "--html"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "can only disable --html-self-contained when a named output is given."
    )
    assert c.exitcode != 0


def test_html_injection_via_json(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    import json
    import markupsafe

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

    c = capture(capsys, ["-a", str(tempfile), "--html"])

    assert script not in c.out
    assert str(markupsafe.escape(script)) in c.out, f"--- got:\n{c.out}\n---"
    assert c.exitcode == 0


def test_import_valid_cobertura_file(tmp_path: Path) -> None:
    from gcovr.formats import read_reports
    from gcovr.configuration import merge_options_and_set_defaults

    testfile = "code.cpp"
    xml_data = f"""<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE coverage SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-04.dtd'>
<coverage line-rate="0.9" branch-rate="0.75" lines-covered="9" lines-valid="10" branches-covered="3" branches-valid="4" complexity="0.0" timestamp="" version="gcovr 7.1">
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
        [{"cobertura_tracefile": [filename], "include_filter": [re.compile(".")]}]
    )
    covdata = read_reports(opts)
    assert covdata is not None
    testfile = os.path.join(tmp_path, testfile)
    assert testfile in covdata
    filecov = covdata[testfile]
    assert len(list(filecov.lines())) == 10
    for line, count, branches in [
        (7, 1, None),
        (9, 3, None),
        (16, 0, None),
        (13, 2, [1, 0]),
    ]:
        linecovs = filecov.get_line(line)
        assert linecovs is not None
        assert linecovs.count == count
        branchcov_list = list(linecovs[""].branches())
        if branches is not None:
            assert len(branchcov_list) == len(branches)
            for branch_idx, branch_count in enumerate(branches):
                matching_branch = [
                    branchcov
                    for branchcov in branchcov_list
                    if branchcov.key == (branch_idx, None, None)
                ]
                assert len(matching_branch) == 1
                assert matching_branch[0].count == branch_count
        else:
            assert len(branchcov_list) == 0


def test_invalid_cobertura_file(caplog: pytest.LogCaptureFixture) -> None:
    c = log_capture(caplog, ["--cobertura-add-tracefile", "/*.FileDoesNotExist.*"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        "Bad --covertura-add-tracefile option.\n\tThe specified file does not exist."
        in message[2]
    )
    assert c.exitcode != 0


def test_import_corrupt_cobertura_file(
    caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    xml_data = "Invalid XML content"
    tempfile = tmp_path / "corrupt_cobertura.xml"
    with tempfile.open("w+") as fp:
        fp.write(xml_data)

    c = log_capture(caplog, ["--cobertura-add-tracefile", str(tempfile)])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert "Start tag expected" in message[2]
    assert c.exitcode != 0


def test_import_cobertura_file_with_invalid_line(
    caplog: pytest.LogCaptureFixture, tmp_path: Path
) -> None:
    xml_data = """<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE coverage SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-04.dtd'>
<coverage line-rate="0.9" branch-rate="0.75" lines-covered="9" lines-valid="10" branches-covered="3" branches-valid="4" complexity="0.0" timestamp="" version="gcovr 7.1">
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

    c = log_capture(
        caplog, ["--cobertura-add-tracefile", str(tempfile), "--filter", "."]
    )
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert "'number' attribute is required and must be an integer" in message[2]
    assert c.exitcode != 0


@pytest.mark.parametrize(
    "option",
    [
        "--filter",
        "--exclude",
        "--include",
        "--gcov-filter",
        "--gcov-exclude",
        "--gcov-exclude-directory",
    ],
)
def test_exclude_filter(caplog: pytest.LogCaptureFixture, option: str) -> None:
    c = log_capture(
        caplog,
        [option, "example.**"],
    )
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2].startswith(
        f"Error setting up filter {option}='example.**': multiple repeat at position 9"
    )
    assert c.exitcode != 0


@pytest.mark.parametrize(
    "option",
    [
        "--exclude-function",
        "--exclude-lines-by-pattern",
        "--exclude-branches-by-pattern",
    ],
)
def test_exclude_pattern(caplog: pytest.LogCaptureFixture, option: str) -> None:
    c = log_capture(
        caplog,
        [option, "/example.**/" if option == "--exclude-function" else "example.**"],
    )
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2].startswith(
        f"Error setting up pattern {option}='example.**': multiple repeat at position 9"
    )
    assert c.exitcode != 0


def test_invalid_timestamp(capsys: pytest.CaptureFixture[str]) -> None:
    c = capture(capsys, ["--timestamp=foo"])
    assert c.out == ""
    assert "argument --timestamp: unknown timestamp format: 'foo'" in c.err
    assert c.exitcode != 0


def test_sort_branch_and_not_uncovered_or_percent(
    caplog: pytest.LogCaptureFixture,
) -> None:
    c = log_capture(caplog, ["--sort-branches"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2].startswith(
        "the options --sort-branches without '--sort uncovered-number' or '--sort uncovered-percent' doesn't make sense."
    )
    assert c.exitcode == 1


@pytest.mark.parametrize(
    "option",
    [
        ("-b", "--txt-metric branch"),
        ("--txt-branches", "--txt-metric branch"),
        ("--branches", "--txt-metric branch"),
        ("--sort-uncovered", "--sort uncovered-number"),
        ("--sort-percentage", "--sort uncovered-percent"),
    ],
    ids=lambda option: option[0],
)
def test_deprecated_option(
    caplog: pytest.LogCaptureFixture, option: tuple[str, str]
) -> None:
    c = log_capture(caplog, [option[0], "--help"])
    message = c.record_tuples[0]
    assert message[1] == logging.WARNING
    assert (
        f"Deprecated option {option[0]} used, please use {option[1]!r} instead"
        in message[2]
    )
    assert c.exitcode != 1
