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

# cspell:ignore metafunc finput


import glob
import logging
import os
import platform
import tempfile
from typing import (
    Callable,
    Iterable,
    Optional,
)
import pytest
import re
import shutil
import subprocess  # nosec # Commands are trusted.
import sys
import difflib
import zipfile

from yaxmldiff import compare_xml
from lxml import etree  # nosec # Data is trusted.

from gcovr.utils import force_unix_separator

python_interpreter = force_unix_separator(
    sys.executable
)  # use forward slash on windows as well
env = os.environ
env["SOURCE_DATE_EPOCH"] = "1759082961"
env["GCOVR"] = python_interpreter + " -m gcovr"
for var in [
    "CPATH",
    "C_INCLUDE_PATH",
    "CPLUS_INCLUDE_PATH",
    "OBJC_INCLUDE_PATH",
    "CFLAGS",
    "CXXFLAGS",
    "LDFLAGS",
]:
    if var in env:
        env.pop(var)
# Override language for input files
env["LANG"] = "C.UTF-8"

skip_clean = None

BASE_DIRECTORY = os.path.split(os.path.abspath(__file__))[0]
GCOVR_ISOLATED_TEST = os.getenv("GCOVR_ISOLATED_TEST") == "zkQEVaBpXF1i"

ARCHIVE_DIFFERENCES_FILE = os.path.join(BASE_DIRECTORY, "diff.zip")

CC = os.path.split(env["CC"])[1]

IS_MACOS_HOST = os.getenv("HOST_OS") == "Darwin"
IS_MACOS = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:  # pragma: no cover
    # This is only covered on Windows
    import win32api
    import string

    used_drives = win32api.GetLogicalDriveStrings().split("\0")
    sys.stdout.write(f"Used drives: {used_drives}")
    free_drives = sorted(set(string.ascii_uppercase) - set(used_drives))
    sys.stdout.write(f"Free drives: {free_drives}")
    assert free_drives, "Must have at least one free drive letter"
    env["GCOVR_TEST_DRIVE_WINDOWS"] = f"{free_drives[-1]}:"

CC_REFERENCE = env.get("CC_REFERENCE", CC)
CC_REFERENCE_VERSION = int(CC_REFERENCE.split("-")[1])
IS_CLANG = "clang" in CC_REFERENCE
IS_GCC = not IS_CLANG

REFERENCE_DIR_OS_SUFFIX = (
    "" if platform.system() == "Linux" else f"-{platform.system()}"
)

REFERENCE_DIRS = []
REFERENCE_DIR_VERSION_LIST = (
    [
        "gcc-5",
        "gcc-6",
        "gcc-8",
        "gcc-9",
        "gcc-10",
        "gcc-11",
        "gcc-12",
        "gcc-13",
        "gcc-14",
    ]
    if "gcc" in CC_REFERENCE
    else [
        "clang-10",
        "clang-13",
        "clang-14",
        "clang-15",
        "clang-16",
        "clang-17",
        "clang-18",
        "clang-19",
    ]
)
for ref in REFERENCE_DIR_VERSION_LIST:  # pragma: no cover
    REFERENCE_DIRS.append(os.path.join("reference", ref))
    if REFERENCE_DIR_OS_SUFFIX:
        REFERENCE_DIRS.append(f"{REFERENCE_DIRS[-1]}{REFERENCE_DIR_OS_SUFFIX}")
    if ref == CC_REFERENCE:
        break
REFERENCE_DIRS.reverse()

RE_DECIMAL = re.compile(r"(\d+\.\d+)")

RE_CRLF = re.compile(r"\r\n")

RE_TXT_WHITESPACE_AT_EOL = re.compile(r"[ ]+$", flags=re.MULTILINE)

RE_LCOV_PATH = re.compile(r"(SF:)(?:.:)?/.+?((?:tests|doc)/.+?)?$", flags=re.MULTILINE)

RE_COBERTURA_SOURCE_DIR = re.compile(r"(<source>)(?:.:)?/.+?((?:tests/.+?)?</source>)")

RE_COVERALLS_CLEAN_KEYS = re.compile(r'"(commit_sha|repo_token)": "[^"]*"')
RE_COVERALLS_GIT = re.compile(
    r'"git": \{(?:"[^"]*": (?:"[^"]*"|\{[^\}]*\}|\[[^\]]*\])(?:, )?)+\}, '
)
RE_COVERALLS_GIT_PRETTY = re.compile(
    r'\s+"git": \{\s+"head": \{(?:\s+"[^"]+":.+\n)+\s+\},\s+"branch": "branch",\s+"remotes": \[[^\]]+\]\s+\},'
)


def translate_newlines_if_windows(contents: str) -> str:
    return RE_CRLF.sub(r"\n", contents) if platform.system() == "Windows" else contents


def scrub_txt(contents: str) -> str:
    return RE_TXT_WHITESPACE_AT_EOL.sub("", contents)


def scrub_lcov(contents: str) -> str:
    return RE_LCOV_PATH.sub(r"\1\2", contents)


def scrub_xml(contents: str) -> str:
    contents = RE_DECIMAL.sub(lambda m: str(round(float(m.group(1)), 5)), contents)
    return contents


def scrub_cobertura(contents: str) -> str:
    contents = scrub_xml(contents)
    contents = RE_COBERTURA_SOURCE_DIR.sub(r"\1\2", contents)
    return contents


def scrub_coveralls(contents: str) -> str:
    contents = RE_COVERALLS_CLEAN_KEYS.sub('"\\1": ""', contents)
    contents = RE_COVERALLS_GIT_PRETTY.sub("", contents)
    contents = RE_COVERALLS_GIT.sub("", contents)
    return contents


def find_tests(basedir: str) -> Iterable[str]:
    for f in sorted(os.listdir(basedir)):
        if not os.path.isdir(os.path.join(basedir, f)):
            continue
        if not os.path.isfile(os.path.join(basedir, f, "Makefile")):  # pragma: no cover
            continue
        yield f


def assert_equals(
    reference_file: str, reference: str, test_file: str, test: str, encoding: str
) -> None:
    _, extension = os.path.splitext(reference_file)
    if extension in [".html", ".xml"]:
        if extension == ".html":
            el_reference = etree.fromstringlist(  # nosec # We parse our reference files here
                reference.encode().split(b"\n"), etree.HTMLParser(encoding=encoding)
            )
            el_test = etree.fromstringlist(  # nosec # We parse our test files here
                test.encode().split(b"\n"), etree.HTMLParser(encoding=encoding)
            )
        else:
            el_reference = etree.fromstringlist(  # nosec # We parse our reference files here
                reference.encode().split(b"\n")
            )
            el_test = etree.fromstringlist(  # nosec # We parse our test files here
                test.encode().split(b"\n")
            )

        diff_out: Optional[str] = compare_xml(el_reference, el_test)
        if diff_out is None:
            return

        diff_out = (
            f"-- {reference_file}\n++ {test_file}\n{diff_out}"  # pragma: no cover
        )
    else:
        reference_list = reference.splitlines(keepends=True)
        reference_list.append("\n")
        test_list = test.splitlines(keepends=True)
        test_list.append("\n")
        diff_lines = list[str](
            difflib.unified_diff(
                reference_list,
                test_list,
                fromfile=reference_file,
                tofile=test_file,
            )
        )

        diff_is_empty = len(diff_lines) == 0
        if diff_is_empty:
            return
        diff_out = "".join(diff_lines)  # pragma: no cover

    raise AssertionError(diff_out)  # pragma: no cover


def run(cmd: list[str], cwd: Optional[str] = None) -> bool:
    sys.stdout.write(f"STDOUT - START {cmd}\n")
    returncode = subprocess.call(  # nosec # We execute our tests here
        cmd, stderr=subprocess.STDOUT, env=env, cwd=cwd
    )
    sys.stdout.write("STDOUT - END\n")
    return returncode == 0


def find_reference_files(output_pattern: list[str]) -> Iterable[tuple[str, str]]:
    seen_files = set()
    for reference_dir in REFERENCE_DIRS:
        for pattern in output_pattern:
            if os.path.isdir(reference_dir):
                for reference_file in glob.glob(os.path.join(reference_dir, pattern)):
                    if os.path.basename(reference_file) not in seen_files:
                        test_file = os.path.basename(reference_file)
                        seen_files.add(test_file)
                        yield test_file, reference_file


@pytest.fixture(scope="module")
def compiled(name: str) -> Iterable[str]:
    path = os.path.join(BASE_DIRECTORY, name)
    assert run(["make", "clean"], cwd=path)
    assert run(["make", "all"], cwd=path)
    yield name
    if not skip_clean:  # pragma: no cover
        # In the automated tests skip_clean is always False.
        assert run(["make", "clean"], cwd=path)


KNOWN_FORMATS = [
    # Own formats
    "txt",
    "md",
    "html",
    "json",
    "json_summary",
    "csv",
    # Other formats
    "clover",
    "cobertura",
    "coveralls",
    "jacoco",
    "lcov",
    "sonarqube",
]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """generate a list of all available integration tests."""

    global skip_clean  # pylint: disable=global-statement
    skip_clean = metafunc.config.getoption("skip_clean")
    generate_reference = metafunc.config.getoption("generate_reference")
    update_reference = metafunc.config.getoption("update_reference")
    archive_differences = metafunc.config.getoption("archive_differences")

    collected_params = []

    if archive_differences:  # pragma: no cover
        if os.path.exists(ARCHIVE_DIFFERENCES_FILE):
            os.unlink(ARCHIVE_DIFFERENCES_FILE)

    for name in find_tests(BASE_DIRECTORY):
        targets = parse_makefile_for_available_targets(
            os.path.join(BASE_DIRECTORY, name, "Makefile")
        )

        # check that the "run" target lists no unknown formats
        target_run = targets.get("run", set())
        unknown_formats = target_run.difference(KNOWN_FORMATS)
        if unknown_formats:  # pragma: no cover
            raise ValueError(
                f"{name}/Makefile target 'run' references unknown format {unknown_formats}"
            )

        # check that all "run" targets are actually available
        unresolved_prerequisite = target_run.difference(targets)
        if unresolved_prerequisite:  # pragma: no cover
            raise ValueError(
                f"{name}/Makefile target 'run' has unresolved prerequisite {unresolved_prerequisite}"
            )

        # check that all available known formats are also listed in the "run" target
        unreferenced_formats = (
            set(KNOWN_FORMATS).intersection(targets).difference(target_run)
        )
        if unreferenced_formats:  # pragma: no cover
            raise ValueError(
                f"{name}/Makefile target 'run' doesn't reference available target {unreferenced_formats}"
            )

        for current_format in KNOWN_FORMATS:
            # only test formats where the Makefile provides a target
            if current_format not in targets:
                continue

            marks = [
                pytest.mark.xfail(
                    "virtual-classes" in name
                    and IS_GCC
                    and CC_REFERENCE_VERSION in [5, 6],
                    reason="The branch and call numbers differ in locale execution and CI",
                ),
                pytest.mark.skipif(
                    "conditions" in name and (not IS_GCC or CC_REFERENCE_VERSION < 14),
                    reason="Condition coverage needs at least gcc-14.",
                ),
                pytest.mark.skipif(
                    name in ["bazel"] and (IS_WINDOWS or IS_MACOS and IS_GCC),
                    reason="Bazel test not working on Windows or on MacOs (with gcc).",
                ),
                pytest.mark.skipif(
                    name == "simple1-drive-subst" and not IS_WINDOWS,
                    reason="drive substitution only available on Windows",
                ),
                pytest.mark.skipif(
                    name == "cmake_gtest" and not GCOVR_ISOLATED_TEST,
                    reason="only available in docker",
                ),
                pytest.mark.skipif(
                    name == "gcov-no_working_dir_found"
                    and (
                        not GCOVR_ISOLATED_TEST
                        or IS_MACOS_HOST
                        or (
                            # With JSON format this test doesn't work
                            IS_GCC and CC_REFERENCE_VERSION in (14,)
                        )
                    ),
                    reason="only available in docker on hosts != MacOs",
                ),
                pytest.mark.xfail(
                    name == "worker-exception" and IS_WINDOWS,
                    reason="GCOV stub script sin't working under Windows",
                ),
                pytest.mark.xfail(
                    name in ["gcov-ignore_output_error"] and IS_WINDOWS,
                    reason="Permission is ignored on Windows",
                ),
                pytest.mark.xfail(
                    name in ["less-lines"]
                    and (
                        (
                            IS_CLANG
                            and CC_REFERENCE_VERSION in [13, 14, 15, 16, 17, 18, 19]
                        )
                        or (IS_GCC and CC_REFERENCE_VERSION in [8, 9, 10, 11, 12, 13])
                    ),
                    reason="Other versions stub the line",
                ),
                pytest.mark.xfail(
                    name == "exclude-throw-branches"
                    and current_format == "html"
                    and IS_WINDOWS,
                    reason="branch coverage details seem to be platform-dependent",
                ),
                pytest.mark.xfail(
                    name == "rounding" and IS_WINDOWS,
                    reason="branch coverage seem to be platform-dependent",
                ),
                pytest.mark.xfail(
                    name == "html-source-encoding-cp1252" and IS_CLANG,
                    reason="clang doesn't understand -finput-charset=...",
                ),
                pytest.mark.xfail(
                    name in ["wrong-casing"] and not IS_WINDOWS,
                    reason="Only windows has a case insensitive file system",
                ),
                pytest.mark.xfail(
                    name == "gcc-abspath" and (IS_CLANG or CC_REFERENCE_VERSION < 8),
                    reason="Option -fprofile-abs-path is supported since gcc-8",
                ),
                pytest.mark.xfail(
                    name
                    in [
                        "cmake_oos",
                        "cmake_oos_ninja",
                        "coexisting_object_directories-from_build_dir",
                        "coexisting_object_directories-from_build_dir-without_search_dir",
                        "coexisting_object_directories-from_build_dir-without_object_dir",
                        "coexisting_object_directories-from_root_dir",
                        "coexisting_object_directories-from_root_dir-without_search_dir",
                        "coexisting_object_directories-from_root_dir-without_object_dir",
                    ]
                    and IS_MACOS
                    and CC_REFERENCE == "gcc-13",
                    reason="There are compiler errors from include of iostream",
                ),
            ]

            collected_params.append(
                pytest.param(
                    name,
                    current_format,
                    targets,
                    generate_reference,
                    update_reference,
                    archive_differences,
                    marks=marks,
                    id="-".join([name, current_format]),
                )
            )

    metafunc.parametrize(
        "name, current_format, available_targets, generate_reference, update_reference, archive_differences",
        collected_params,
        indirect=False,
        scope="module",
    )


def parse_makefile_for_available_targets(path: str) -> dict[str, set[str]]:
    targets = dict[str, set[str]]()
    with open(path, encoding="UTF-8") as makefile:
        for line in makefile:
            if m := re.match(r"^(\w[\w -]*):([\s\w.-]*)$", line):
                deps = m.group(2).split()
                for target in m.group(1).split():
                    targets.setdefault(target, set()).update(deps)
    return targets


def generate_reference_data(output_pattern: list[str]) -> None:  # pragma: no cover
    for pattern in output_pattern:
        for generated_file in glob.glob(pattern):
            reference_file = os.path.join(REFERENCE_DIRS[0], generated_file)
            if os.path.isfile(reference_file):
                continue
            else:
                os.makedirs(REFERENCE_DIRS[0], exist_ok=True)
                logging.info(f"copying {generated_file} to {reference_file}")
                shutil.copyfile(generated_file, reference_file)


def update_reference_data(  # pragma: no cover
    reference_file: str, content: str, encoding: str
) -> str:
    os.makedirs(REFERENCE_DIRS[0], exist_ok=True)
    reference_file = os.path.join(REFERENCE_DIRS[0], os.path.basename(reference_file))

    with open(reference_file, "w", newline="", encoding=encoding) as out:
        out.write(content)

    return reference_file


def archive_difference_data(  # pragma: no cover
    name: str, test_scrubbed: str, reference_file: str, encoding: str
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(
            os.path.join(tmpdir, os.path.basename(reference_file)),
            mode="wt",
            newline="",
            encoding=encoding,
        ) as fh_temp:
            fh_temp.write(test_scrubbed)

        reference_file_zip = os.path.join(
            name, REFERENCE_DIRS[0], os.path.basename(reference_file)
        ).replace(os.path.sep, "/")
        with zipfile.ZipFile(ARCHIVE_DIFFERENCES_FILE, mode="a") as fh_zip:
            fh_zip.write(
                fh_temp.name,
                reference_file_zip,
            )


def remove_duplicate_data(  # pragma: no cover
    encoding: str,
    coverage: str,
    test_file: str,
    reference_file: str,
) -> None:
    # Loop over the other coverage data
    for reference_dir in REFERENCE_DIRS:  # pragma: no cover
        other_reference_file = os.path.join(reference_dir, test_file)
        # ... and unlink the current file if it's identical to the other one.
        if other_reference_file != reference_file and os.path.isfile(
            other_reference_file
        ):  # pragma: no cover
            # Only remove it if we have no suffix or the other file has the same.
            if not REFERENCE_DIR_OS_SUFFIX or other_reference_file.endswith(
                REFERENCE_DIR_OS_SUFFIX
            ):
                with open(other_reference_file, newline="", encoding=encoding) as f:
                    if coverage == f.read():
                        os.unlink(reference_file)
            break
        # Check if folder is empty
        if (
            os.path.exists(reference_dir)
            and len(glob.glob(os.path.join(reference_dir, "*"))) == 0
        ):
            os.rmdir(reference_dir)


SCRUBBERS = dict[str, Optional[Callable[[str], str]]](
    # Own formats
    txt=scrub_txt,
    md=None,
    html=None,
    json=None,
    json_summary=None,
    csv=None,
    # Other formats
    clover=scrub_xml,
    cobertura=scrub_cobertura,
    coveralls=scrub_coveralls,
    jacoco=scrub_xml,
    lcov=scrub_lcov,
    sonarqube=None,
)

FORMATS_TO_SKIP_LINEBREAK_TRANSFORMATION = ("csv",)

OUTPUT_PATTERN = dict(
    # Own formats
    txt=["coverage*.txt"],
    md=["coverage*.md"],
    html=["coverage*.html", "coverage*.css"],
    json=["coverage*.json"],
    json_summary=["summary_coverage*.json"],
    csv=["coverage*.csv"],
    # Other formats
    clover=["clover*.xml"],
    cobertura=["cobertura*.xml"],
    coveralls=["coveralls*.json"],
    jacoco=["jacoco*.xml"],
    lcov=["coverage*.lcov"],
    sonarqube=["sonarqube*.xml"],
)


def test_build(
    compiled: str,
    current_format: str,
    available_targets: str,
    generate_reference: bool,
    update_reference: bool,
    archive_differences: bool,
) -> None:
    name = compiled
    scrub = SCRUBBERS[current_format]
    output_pattern = OUTPUT_PATTERN[current_format]

    encoding = "utf8"
    if current_format == "html" and name.startswith("html-encoding-"):
        if m := re.match("^html-encoding-(.*)$", name):
            encoding = m.group(1)

    os.chdir(os.path.join(BASE_DIRECTORY, name))
    make_options = ["-j", "4"]
    if not IS_MACOS:
        make_options.append("--output-sync=target")
    assert run(["make", *make_options, current_format])

    if generate_reference:  # pragma: no cover
        generate_reference_data(output_pattern)

    whole_diff_output = list[str]()
    for test_file, reference_file in find_reference_files(output_pattern):
        with open(test_file, newline="", encoding=encoding) as f:
            test_content = f.read()
            if scrub is not None:
                test_content = scrub(test_content)

        # Overwrite the file created above with the scrubbed content
        if generate_reference:  # pragma: no cover
            with open(reference_file, "w", newline="", encoding=encoding) as f:
                f.write(test_content)
            reference_content = test_content
        else:
            with open(reference_file, newline="", encoding=encoding) as f:
                reference_content = f.read()

        try:
            assert_equals(
                reference_file,
                reference_content
                if current_format in FORMATS_TO_SKIP_LINEBREAK_TRANSFORMATION
                else translate_newlines_if_windows(reference_content),
                test_file,
                test_content
                if current_format in FORMATS_TO_SKIP_LINEBREAK_TRANSFORMATION
                else translate_newlines_if_windows(test_content),
                encoding,
            )
        except AssertionError as e:  # pragma: no cover
            whole_diff_output += str(e) + "\n"
            if update_reference:
                reference_file = update_reference_data(
                    reference_file, test_content, encoding
                )
            if archive_differences:
                archive_difference_data(name, test_content, reference_file, encoding)

        if generate_reference or update_reference:  # pragma: no cover
            remove_duplicate_data(encoding, test_content, test_file, reference_file)

    diff_is_empty = len(whole_diff_output) == 0
    assert diff_is_empty, "Diff output:\n" + "".join(whole_diff_output)

    # some tests require additional cleanup after each test
    if "clean-each" in available_targets:  # pragma: no cover
        assert run(["make", "clean-each"])

    os.chdir(BASE_DIRECTORY)
