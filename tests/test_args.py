# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 7.2+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2024 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from gcovr.__main__ import main
from gcovr.version import __version__
from gcovr.formats.json.versions import JSON_FORMAT_VERSION

import logging
import pytest
import os
import re
import sys


GCOVR_ISOLATED_TEST = os.getenv("GCOVR_ISOLATED_TEST") == "zkQEVaBpXF1i"


# The CaptureObject class holds the capture method result
class CaptureObject:
    def __init__(self, out, err, exception):
        self.out = out
        self.err = err
        self.exception = exception


def capture(capsys, args):
    """The capture method calls the main method and captures its output/error
    streams and exit code."""
    e = None
    try:
        main(args)
        # Explicit SystemExit exception in case main() returns normally
        sys.exit(0)
    except SystemExit as exception:
        e = exception
    out, err = capsys.readouterr()
    return CaptureObject(out, err, e)


# The LogCaptureObject class holds the capture method result
class LogCaptureObject:
    def __init__(self, record_tuples, exception):
        self.record_tuples = record_tuples
        self.exception = exception


def log_capture(caplog, args):
    """The capture method calls the main method and captures its output/error
    streams and exit code."""
    e = None
    try:
        main(args)
        # Explicit SystemExit exception in case main() returns normally
        sys.exit(0)
    except SystemExit as exception:
        e = exception
    return LogCaptureObject(caplog.record_tuples, e)


def test_version(capsys):
    c = capture(capsys, ["--version"])
    assert c.err == ""
    assert c.out.startswith(f"gcovr {__version__}")
    assert c.exception.code == 0


def test_help(capsys):
    c = capture(capsys, ["-h"])
    assert c.err == ""
    assert c.out.startswith("usage: gcovr [options]")
    assert c.exception.code == 0


def test_empty_root(capsys):
    c = capture(capsys, ["-r", ""])
    assert c.out == ""
    assert "argument -r/--root: Should not be set to an empty string." in c.err
    assert c.exception.code != 0


def test_empty_exclude(capsys):
    c = capture(capsys, ["--exclude", ""])
    assert c.out == ""
    assert "filter cannot be empty" in c.err
    assert c.exception.code != 0


def test_empty_exclude_directories(capsys):
    c = capture(capsys, ["--gcov-exclude-directories", ""])
    assert c.out == ""
    assert "filter cannot be empty" in c.err
    assert c.exception.code != 0


def test_empty_objdir(capsys):
    c = capture(capsys, ["--gcov-object-directory", ""])
    assert c.out == ""
    assert (
        "argument --gcov-object-directory/--object-directory: Should not be set to an empty string."
        in c.err
    )
    assert c.exception.code != 0


def test_invalid_objdir(caplog):
    c = log_capture(caplog, ["--gcov-object-directory", "not-existing-dir"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2].startswith("Bad --gcov-object-directory option.")
    assert c.exception.code == 1


def helper_test_non_existing_directory_output(capsys, option):
    c = capture(capsys, [option, "not-existing-dir/file.txt"])
    assert c.out == ""
    assert "Could not create output file 'not-existing-dir/file.txt': " in c.err
    assert c.exception.code != 0


def test_non_existing_directory_output(capsys):
    helper_test_non_existing_directory_output(capsys, "--output")


def test_non_existing_directory_txt(capsys):
    helper_test_non_existing_directory_output(capsys, "--txt")


def test_non_existing_directory_xml(capsys):
    helper_test_non_existing_directory_output(capsys, "--xml")


def test_non_existing_directory_html(capsys):
    helper_test_non_existing_directory_output(capsys, "--html")


def test_non_existing_directory_html_details(capsys):
    helper_test_non_existing_directory_output(capsys, "--html-details")


def test_non_existing_directory_html_nested(capsys):
    helper_test_non_existing_directory_output(capsys, "--html-nested")


def test_non_existing_directory_sonarqube(capsys):
    helper_test_non_existing_directory_output(capsys, "--sonarqube")


def test_non_existing_directory_json(capsys):
    helper_test_non_existing_directory_output(capsys, "--json")


def test_non_existing_directory_csv(capsys):
    helper_test_non_existing_directory_output(capsys, "--csv")


def helper_test_non_existing_directory_2_output(capsys, option):
    c = capture(capsys, [option, "not-existing-dir/subdir/"])
    assert c.out == ""
    assert "Could not create output directory 'not-existing-dir/subdir/': " in c.err
    assert c.exception.code != 0


def test_non_existing_directory_2_output(capsys):
    helper_test_non_existing_directory_2_output(capsys, "--output")


def test_non_existing_directory_2_txt(capsys):
    helper_test_non_existing_directory_2_output(capsys, "--txt")


def test_non_existing_directory_2_xml(capsys):
    helper_test_non_existing_directory_2_output(capsys, "--xml")


def test_non_existing_directory_2_html(capsys):
    helper_test_non_existing_directory_2_output(capsys, "--html")


def test_non_existing_directory_2_html_details(capsys):
    helper_test_non_existing_directory_2_output(capsys, "--html-details")


def test_non_existing_directory_2_html_nested(capsys):
    helper_test_non_existing_directory_2_output(capsys, "--html-nested")


def test_non_existing_directory_2_sonarqube(capsys):
    helper_test_non_existing_directory_2_output(capsys, "--sonarqube")


def test_non_existing_directory_2_json(capsys):
    helper_test_non_existing_directory_2_output(capsys, "--json")


def test_non_existing_directory_2_csv(capsys):
    helper_test_non_existing_directory_2_output(capsys, "--csv")


def helper_test_non_writable_directory_output(capsys, option):
    c = capture(capsys, [option, "/file.txt"])
    assert c.out == ""
    assert "Could not create output file '/file.txt': " in c.err
    assert c.exception.code != 0


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_output(capsys):
    helper_test_non_writable_directory_output(capsys, "--output")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_txt(capsys):
    helper_test_non_writable_directory_output(capsys, "--txt")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_xml(capsys):
    helper_test_non_writable_directory_output(capsys, "--xml")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_html(capsys):
    helper_test_non_writable_directory_output(capsys, "--html")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_html_details(capsys):
    helper_test_non_writable_directory_output(capsys, "--html-details")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_html_nested(capsys):
    helper_test_non_writable_directory_output(capsys, "--html-nested")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_sonarqube(capsys):
    helper_test_non_writable_directory_output(capsys, "--sonarqube")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_json(capsys):
    helper_test_non_writable_directory_output(capsys, "--json")


@pytest.mark.skipif(not GCOVR_ISOLATED_TEST, reason="Only for docker")
def test_non_writable_directory_csv(capsys):
    helper_test_non_writable_directory_output(capsys, "--csv")


def test_no_output_html_details(caplog):
    c = log_capture(caplog, ["--html-details"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "a named output must be given, if the option --html-details\nis used."
    )
    assert c.exception.code != 0


def test_no_output_html_nested(caplog):
    c = log_capture(caplog, ["--html-nested"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "a named output must be given, if the option --html-nested\nis used."
    )
    assert c.exception.code != 0


def test_html_details_and_html_nested(caplog):
    c = log_capture(caplog, ["--output", "x", "--html-details", "--html-nested"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2] == "--html-details and --html-nested can not be used together."
    assert c.exception.code != 0


@pytest.mark.parametrize(
    "option",
    [
        "--fail-under-line",
        "--fail-under-branch",
        "--fail-under-decision",
        "--fail-under-function",
    ],
)
def test_failed_under_threshold_nan(option, capsys):
    c = capture(capsys, [option, "nan"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exception.code != 0


@pytest.mark.parametrize(
    "option",
    [
        "--fail-under-line",
        "--fail-under-branch",
        "--fail-under-decision",
        "--fail-under-function",
    ],
)
def test_failed_under_threshold_negative(option, capsys):
    c = capture(capsys, [option, "-0.1"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exception.code != 0


@pytest.mark.parametrize(
    "option",
    [
        "--fail-under-line",
        "--fail-under-branch",
        "--fail-under-decision",
        "--fail-under-function",
    ],
)
def test_failed_under_threshold_100_1(option, capsys):
    c = capture(capsys, [option, "100.1"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exception.code != 0


def test_failed_under_decision_without_active_decision(caplog):
    c = log_capture(caplog, ["--fail-under-decision", "90"])
    message0 = c.record_tuples[0]
    assert message0[1] == logging.ERROR
    assert message0[2] == "--fail-under-decision need also option --decision."
    assert c.exception.code != 0


def test_filter_backslashes_are_detected(caplog):
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
        "Error setting up filter 'C:\\\\foo\\moo': bad escape \\m at position 7"
    )


def test_html_css_not_exists(capsys):
    c = capture(capsys, ["--html-css", "/File/does/not/\texist"])
    assert c.out == ""
    assert (
        re.search(
            r"Should be a file that already exists: '[/\\]+File[/\\]+does[/\\]+not[/\\]+\\texist'",
            c.err,
        )
        is not None
    )
    assert c.exception.code != 0


def test_html_title_empty_string(caplog):
    c = log_capture(caplog, ["--html-title", ""])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2] == "an empty --html-title= is not allowed."
    assert c.exception.code != 0


def test_html_medium_threshold_nan(capsys):
    c = capture(capsys, ["--html-medium-threshold", "nan"])
    assert c.out == ""
    assert "--html-medium-threshold: nan not in range [0.0, 100.0]" in c.err
    assert c.exception.code != 0


def test_html_medium_threshold_negative(capsys):
    c = capture(capsys, ["--html-medium-threshold", "-0.1"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exception.code != 0


def test_html_medium_threshold_zero(caplog):
    c = log_capture(caplog, ["--html-medium-threshold", "0.0"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2] == "value of --html-medium-threshold= should not be zero."
    assert c.exception.code != 0


def test_html_high_threshold_nan(capsys):
    c = capture(capsys, ["--html-high-threshold", "nan"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exception.code != 0


def test_html_high_threshold_negative(capsys):
    c = capture(capsys, ["--html-high-threshold", "-0.1"])
    assert c.out == ""
    assert "not in range [0.0, 100.0]" in c.err
    assert c.exception.code != 0


def test_html_medium_threshold_gt_html_high_threshold(caplog):
    c = log_capture(
        caplog, ["--html-medium-threshold", "60", "--html-high-threshold", "50"]
    )
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "value of --html-medium-threshold=60.0 should be\nlower than or equal to the value of --html-high-threshold=50.0."
    )
    assert c.exception.code != 0


def test_html_tab_size_zero(caplog):
    c = log_capture(caplog, ["--html-tab-size", "0"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2] == "value of --html-tab-size= should be greater 0."
    assert c.exception.code != 0


def test_html_template_dir(capsys):
    c = capture(capsys, ["--html", "--html-template-dir", "foo"])
    assert "<html" in c.out
    assert "</html>" in c.out


def test_multiple_output_formats_to_stdout(caplog):
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
            "gcovr",
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
        format, option = text_fragments
        message = c.record_tuples[index]
        assert message[1] == logging.WARNING
        assert (
            message[2]
            == f"{format} output skipped - consider providing an output file with `{option}=OUTPUT`."
        )
    assert c.exception.code == 0


def test_multiple_output_formats_to_stdout_1(caplog):
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
            "gcovr",
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
        format, option = text_fragments
        message = c.record_tuples[index]
        assert message[1] == logging.WARNING
        assert (
            message[2]
            == f"{format} output skipped - consider providing an output file with `{option}=OUTPUT`."
        )
    assert c.exception.code == 0


def test_no_self_contained_without_file(caplog):
    c = log_capture(caplog, ["--no-html-self-contained", "--html"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert (
        message[2]
        == "can only disable --html-self-contained when a named output is given."
    )
    assert c.exception.code != 0


def test_html_injection_via_json(capsys, tmp_path):
    import json
    import markupsafe

    script = '<script>alert("pwned")</script>'
    jsondata = {
        "gcovr/format_version": JSON_FORMAT_VERSION,
        "files": [
            {"file": script, "functions": [], "lines": []},
            {"file": "other", "functions": [], "lines": []},
        ],
    }

    tempfile = tmp_path / "injection.json"

    with tempfile.open("w+") as jsonfile:
        json.dump(jsondata, jsonfile)

    c = capture(capsys, ["-a", str(tempfile), "--html"])

    assert script not in c.out
    assert str(markupsafe.escape(script)) in c.out, "--- got:\n{}\n---".format(c.out)
    assert c.exception.code == 0


def test_import_valid_cobertura_file(tmp_path):
    from gcovr.formats import read_reports
    from gcovr.configuration import merge_options_and_set_defaults
    from gcovr.coverage import FileCoverage

    testfile = "/path/to/source/code.cpp"
    xmldata = f"""<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE coverage SYSTEM 'http://cobertura.sourceforge.net/xml/coverage-04.dtd'>
<coverage line-rate="0.9" branch-rate="0.75" lines-covered="9" lines-valid="10" branches-covered="3" branches-valid="4" complexity="0.0" timestamp="" version="gcovr 7.1">
  <sources>
    <source>.</source>
  </sources>
  <packages>
    <package name="source" line-rate="0.9" branch-rate="0.75" complexity="0.0">
      <classes>
        <class name="code_cpp" filename="{testfile}" line-rate="0.9" branch-rate="0.75" complexity="0.0">
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
    testfile = os.path.abspath(testfile)
    tempfile = tmp_path / "valid_cobertura.xml"
    with tempfile.open("w+") as fp:
        fp.write(xmldata)

    filename = str(tempfile)
    opts = merge_options_and_set_defaults(
        [{"cobertura_add_tracefile": [filename], "filter": [re.compile(".")]}]
    )
    covdata = read_reports(opts)
    assert covdata is not None
    assert testfile in covdata
    fcov: FileCoverage = covdata[testfile]
    assert len(fcov.lines) == 10
    for line, count, branches in [
        (7, 1, None),
        (9, 3, None),
        (16, 0, None),
        (13, 2, [1, 0]),
    ]:
        assert fcov.lines[line].count == count
        if branches is not None:
            assert len(fcov.lines[line].branches) == len(branches)
            for branch_idx, branch_count in enumerate(branches):
                assert fcov.lines[line].branches[branch_idx].count == branch_count


def test_import_corrupt_cobertura_file(caplog, tmp_path):
    xmldata = "weiuh wliecsdfsef"
    tempfile = tmp_path / "corrupt_cobertura.xml"
    with tempfile.open("w+") as fp:
        fp.write(xmldata)

    c = log_capture(caplog, ["--cobertura-add-tracefile", str(tempfile)])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert "Start tag expected" in message[2]
    assert c.exception.code != 0


def test_import_cobertura_file_with_invalid_line(caplog, tmp_path):
    xmldata = """<?xml version='1.0' encoding='UTF-8'?>
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
            <line number="asdas" branch="true" condition-coverage="100% (2/2)" />
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
        fp.write(xmldata)

    c = log_capture(
        caplog, ["--cobertura-add-tracefile", str(tempfile), "--filter", "."]
    )
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert "'number' attribute is required and must be an integer" in message[2]
    assert c.exception.code != 0


def test_exclude_lines_by_pattern(caplog):
    c = log_capture(caplog, ["--exclude-lines-by-pattern", "example.**"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2].startswith(
        "--exclude-lines-by-pattern: Invalid regular expression"
    )
    assert c.exception.code != 0


def test_exclude_branches_by_pattern(caplog):
    c = log_capture(caplog, ["--exclude-branches-by-pattern", "example.**"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2].startswith(
        "--exclude-branches-by-pattern: Invalid regular expression"
    )
    assert c.exception.code != 0


def test_invalid_timestamp(capsys):
    c = capture(capsys, ["--timestamp=foo"])
    assert c.out == ""
    assert "argument --timestamp: unknown timestamp format: 'foo'" in c.err
    assert c.exception.code != 0


def test_sort_branch_and_not_uncovered_or_percent(caplog):
    c = log_capture(caplog, ["--sort-branches"])
    message = c.record_tuples[0]
    assert message[1] == logging.ERROR
    assert message[2].startswith(
        "the options --sort-branches without '--sort uncovered-number' or '--sort uncovered-percent' doesn't make sense."
    )
    assert c.exception.code == 1


@pytest.mark.parametrize(
    "option",
    [
        ("-b", "--txt-metric branch"),
        ("--txt-branches", "--txt-metric branch"),
        ("--branches", "--txt-metric branch"),
        ("--sort-uncovered", "--sort-key uncovered-number"),
        ("--sort-percentage", "--sort-key uncovered-percent"),
    ],
    ids=lambda option: option[0],
)
def test_deprecated_option(caplog, option):
    c = log_capture(caplog, [option[0]])
    message = c.record_tuples[0]
    assert message[1] == logging.WARNING
    assert (
        f"Deprecated option {option[0]} used, please use {option[1]!r} instead"
        in message[2]
    )
    assert c.exception.code != 1
