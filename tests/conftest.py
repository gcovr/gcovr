# -*- coding:utf-8 -*-

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

# cspell:ignore addoption
from contextlib import contextmanager
import difflib
import fnmatch
import logging
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess  # nosec: B404
from sys import stderr, stdout
from typing import Callable, Generator, List, NoReturn
from unittest import mock
import zipfile

import pytest
from lxml import etree  # nosec # Data is trusted.
from yaxmldiff import compare_xml

from gcovr.__main__ import main as gcovr_main
from gcovr.formats.gcov.parser.json import GCOV_JSON_VERSION

LOGGER = logging.getLogger(__name__)

_BASE_DIRECTORY = Path(__file__).absolute().parent
GCOVR_ISOLATED_TEST = os.getenv("GCOVR_ISOLATED_TEST") == "zkQEVaBpXF1i"

_ARCHIVE_DIFFERENCES_FILE = _BASE_DIRECTORY / "diff.zip"

IS_LINUX = platform.system() == "Linux"
IS_DARWIN = platform.system() == "Darwin"
IS_DARWIN_HOST = os.getenv("HOST_OS") == "Darwin"
IS_WINDOWS = platform.system() == "Windows"

# Clear color environment variables to avoid colored output in tests.
# The used escape sequences may interfere with the output comparison.
for envvar in ["FORCE_COLOR", "NO_COLOR"]:
    if envvar in os.environ:
        del os.environ[envvar]

CC = Path(str(shutil.which(os.environ.get("CC", "gcc-5"))))
os.environ["CC"] = str(CC)
CXX = CC.parent / CC.name.replace("clang", "clang++").replace("gcc", "g++")
os.environ["CXX"] = str(CXX)
GCOV = [CC.parent / CC.name.replace("clang", "llvm-cov").replace("gcc", "gcov")] + (
    ["gcov"] if "clang" in CC.name else []
)
os.environ["GCOV"] = shlex.join(str(e) for e in GCOV)

# The arguments to subprocess are constructed from trusted sources.
_CC_HELP_OUTPUT = subprocess.run(  # nosec: B603
    [CC, "--help", "--verbose"],
    capture_output=True,
    text=True,
    check=False,  # Some versions return 1
    shell=False,
).stdout
_CC_VERSION_OUTPUT = subprocess.run(  # nosec: B603
    [CC, "--version"],
    capture_output=True,
    text=True,
    check=True,
    shell=False,
).stdout
_GCOV_VERSION_OUTPUT = subprocess.run(  # nosec: B603
    [*GCOV, "--version"],
    capture_output=True,
    text=True,
    check=True,
    shell=False,
).stdout

# cspell:ignore Linaro xctoolchain
# look for a line "gcc WHATEVER VERSION.WHATEVER" in output like:
#   gcc-5 (Ubuntu/Linaro 5.5.0-12ubuntu1) 5.5.0 20171010
#   Copyright (C) 2015 Free Software Foundation, Inc.
#   This is free software; see the source for copying conditions.  There is NO
#   warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
if matches := re.search(r"^gcc\b.* ([0-9]+)\..+$", _CC_VERSION_OUTPUT, re.M):
    CC_VERSION = int(matches.group(1))
    IS_GCC = True
    _REFERENCE_DIR_VERSION_LIST = [
        f"gcc-{version}" for version in range(5, CC_VERSION + 1)
    ]
# look for a line "WHATEVER clang version VERSION.WHATEVER" in output like:
#    Apple clang version 13.1.6 (clang-1316.0.21.2.5)
#    Target: arm64-apple-darwin21.5.0
#    Thread model: posix
#    InstalledDir: /Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin
elif matches := re.search(r"\bclang version ([0-9]+)\.", _CC_VERSION_OUTPUT, re.M):
    CC_VERSION = int(matches.group(1))
    IS_GCC = False
    _REFERENCE_DIR_VERSION_LIST = [
        f"clang-{version}" for version in range(10, CC_VERSION + 1)
    ]
else:
    raise AssertionError(f"Unable to get compiler version from:\n{_CC_VERSION_OUTPUT}")

USE_GCC_JSON_INTERMEDIATE_FORMAT = (
    IS_GCC and f"JSON format version: {GCOV_JSON_VERSION}" in _GCOV_VERSION_OUTPUT
)
USE_PROFDATA_POSSIBLE = IS_LINUX and not IS_GCC
GCOVR_TEST_USE_CXX_LAMBDA_EXPRESSIONS = "c++20" in _CC_HELP_OUTPUT

_CFLAGS = [
    "-fPIC",
    "-fprofile-arcs",
    "-ftest-coverage",
]
if "condition-coverage" in _CC_HELP_OUTPUT:
    _CFLAGS.append("-fcondition-coverage")

_CFLAGS_PROFDATA = [
    "-fprofile-instr-generate",
    "-fcoverage-mapping",
]

_CXXFLAGS = _CFLAGS.copy()
_CXXFLAGS_PROFDATA = _CFLAGS_PROFDATA.copy()
if GCOVR_TEST_USE_CXX_LAMBDA_EXPRESSIONS:
    _CXXFLAGS += ["-std=c++20", "-DGCOVR_TEST_USE_CXX_LAMBDA_EXPRESSIONS"]
    _CXXFLAGS_PROFDATA += ["-std=c++20", "-DGCOVR_TEST_USE_CXX_LAMBDA_EXPRESSIONS"]

_REFERENCE_DIR_OS_SUFFIX = "" if IS_LINUX else f"-{platform.system()}"
REFERENCE_DIRS = list[str]()
for ref in _REFERENCE_DIR_VERSION_LIST:  # pragma: no cover
    REFERENCE_DIRS.append(ref)
    if _REFERENCE_DIR_OS_SUFFIX:
        REFERENCE_DIRS.append(f"{REFERENCE_DIRS[-1]}{_REFERENCE_DIR_OS_SUFFIX}")
REFERENCE_DIRS.reverse()


def pytest_report_header(config: pytest.Config) -> tuple[str, ...]:
    """Get additional info printed in pytest header."""
    if cmake := shutil.which("cmake"):
        cmake_version = subprocess.check_output(  # nosec: B603
            [cmake, "--version"],
            shell=False,
            text=True,
        ).splitlines()[0]
    else:
        cmake_version = "No CMake found"
    if make := shutil.which("make"):
        make_version = subprocess.check_output(  # nosec: B603
            [make, "--version"],
            shell=False,
            text=True,
        ).splitlines()[0]
    else:
        make_version = "No make found"
    if ninja := shutil.which("ninja"):
        ninja_version = (
            "ninja "
            + subprocess.check_output(  # nosec: B603
                [ninja, "--version"],
                shell=False,
                text=True,
            ).splitlines()[0]
        )
    else:
        ninja_version = "No ninja found"
    return (
        "GCOVR test configuration:",
        f"   {_CC_VERSION_OUTPUT.splitlines()[0]}",
        f"      C:   {CC} {shlex.join(_CFLAGS)}{(' (with profdata: ' + shlex.join(_CFLAGS_PROFDATA) + ')') if USE_PROFDATA_POSSIBLE else ''}",
        f"      C++: {CXX} {shlex.join(_CXXFLAGS)}{(' (with profdata: ' + shlex.join(_CXXFLAGS_PROFDATA) + ')') if USE_PROFDATA_POSSIBLE else ''}",
        f"      gcov: {shlex.join(str(e) for e in GCOV)}",
        f"   {cmake_version}",
        f"   {make_version}",
        f"   {ninja_version}",
        f"   Reference directories: {', '.join(REFERENCE_DIRS)}",
    )


def pytest_addoption(parser: pytest.Parser) -> None:  # pragma: no cover
    """Set the additional options for pytest."""
    parser.addoption(
        "--generate-reference", action="store_true", help="Generate the reference"
    )
    parser.addoption(
        "--update-reference", action="store_true", help="Update the reference"
    )
    parser.addoption(
        "--archive-differences", action="store_true", help="Archive the different files"
    )
    parser.addoption(
        "--skip-clean", action="store_true", help="Skip the clean after the test"
    )


@contextmanager
def chdir(directory: Path) -> Generator[None, None, None]:
    """Context manager for changing the working directory."""
    current_dir = os.getcwd()
    os.chdir(directory)
    try:
        yield
    finally:
        os.chdir(current_dir)


@contextmanager
def log_command(
    capsys: pytest.CaptureFixture[str],
    cwd: Path,
    cmd: List[str],
) -> Generator[None, None, None]:
    """Context manager to log the start and end of a command to stderr."""
    try:
        with capsys.disabled():
            cmd_quoted = shlex.join(cmd)
            print(f"\nRunning in {cwd}: {cmd_quoted}", file=stderr)
        yield
    finally:
        with capsys.disabled():
            print("-------------- done --------------\n", file=stderr)


@contextmanager
def create_output(
    test_id: str | None,
    request: pytest.FixtureRequest,
) -> Generator[Path, None, None]:
    """Context manager for creating a output directory."""
    output_dir = Path.cwd() / "output"
    if test_id is not None:
        output_dir /= test_id
    try:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)
        yield output_dir
    finally:
        if not request.config.getoption("skip_clean") and output_dir.is_dir():
            shutil.rmtree(output_dir, ignore_errors=True)


class GcovrTestCompare:
    """Class for comparing files."""

    # Regular expressions for scrubbing data
    RE_DECIMAL = re.compile(r"(\d+\.\d+)")

    RE_CRLF = re.compile(r"\r\n")

    RE_TXT_WHITESPACE_AT_EOL = re.compile(r"[ ]+$", flags=re.MULTILINE)

    RE_LCOV_PATH = re.compile(
        r"(SF:)(?:.:)?/.+?((?:tests|doc)/.+?)?$", flags=re.MULTILINE
    )

    RE_COBERTURA_SOURCE_DIR = re.compile(
        r"(<source>)(?:.:)?/.+?((?:tests/.+?)?</source>)"
    )

    RE_COVERALLS_CLEAN_KEYS = re.compile(r'"(commit_sha|repo_token)": "[^"]*"')
    RE_COVERALLS_GIT = re.compile(
        r'"git": \{(?:"[^"]*": (?:"[^"]*"|\{[^\}]*\}|\[[^\]]*\])(?:, )?)+\}, '
    )
    RE_COVERALLS_GIT_PRETTY = re.compile(
        r'\s+"git": \{\s+"head": \{(?:\s+"[^"]+":.+\n)+\s+\},\s+"branch": "branch",\s+"remotes": \[[^\]]+\]\s+\},'
    )

    def __init__(
        self,
        *,
        output_dir: Path,
        test_id: str | None,
        capsys: pytest.CaptureFixture[str],
        generate_reference: bool,
        update_reference: bool,
        archive_differences: bool,
    ):
        """Init the object."""
        self.output_dir = output_dir
        reference_root = Path.cwd() / "reference"
        if test_id is not None:
            reference_root /= test_id
        self.capsys = capsys
        self.main_reference = reference_root / REFERENCE_DIRS[0]
        self.generate_reference = generate_reference
        self.update_reference = update_reference
        self.archive_differences = archive_differences
        # Get a list of all reference files. Compared files are removed, at the end all files must be compared.
        seen_files = set[str]()
        reference_files = set[Path]()
        for reference_dir in self.reference_dirs():
            if reference_dir.exists():
                for reference_file in reference_dir.glob("*"):
                    if reference_file.name not in seen_files:
                        seen_files.add(reference_file.name)
                        reference_files.add(
                            (self.main_reference / reference_file.name)
                            if self.generate_reference
                            else reference_file
                        )
        self.reference_files = list(sorted(reference_files))
        if reference_files:
            with self.capsys.disabled():
                files = "\n  - ".join(str(p) for p in reference_files)
                print(
                    f"Expect following file(s) to be compared:\n  - {files}",
                    file=stderr,
                )

    def reference_dirs(self) -> Generator[Path, None, None]:
        """Yield all reference directories."""
        yield from [
            self.main_reference.parent / reference_dir
            for reference_dir in REFERENCE_DIRS
        ]

    @staticmethod
    def __translate_newlines_if_windows(contents: str) -> str:
        return (
            GcovrTestCompare.RE_CRLF.sub(r"\n", contents)
            if platform.system() == "Windows"
            else contents
        )

    @staticmethod
    def scrub_txt(contents: str) -> str:
        """Scrub data for compare."""
        return GcovrTestCompare.RE_TXT_WHITESPACE_AT_EOL.sub("", contents)

    @staticmethod
    def scrub_lcov(contents: str) -> str:
        """Scrub data for compare."""
        return GcovrTestCompare.RE_LCOV_PATH.sub(r"\1\2", contents)

    @staticmethod
    def scrub_xml(contents: str) -> str:
        """Scrub data for compare."""
        contents = GcovrTestCompare.RE_DECIMAL.sub(
            lambda m: str(round(float(m.group(1)), 5)), contents
        )
        return contents

    @staticmethod
    def scrub_cobertura(contents: str) -> str:
        """Scrub data for compare."""
        contents = GcovrTestCompare.scrub_xml(contents)
        contents = GcovrTestCompare.RE_COBERTURA_SOURCE_DIR.sub(r"\1\2", contents)
        return contents

    @staticmethod
    def scrub_coveralls(contents: str) -> str:
        """Scrub data for compare."""
        contents = GcovrTestCompare.RE_COVERALLS_CLEAN_KEYS.sub('"\\1": ""', contents)
        contents = GcovrTestCompare.RE_COVERALLS_GIT_PRETTY.sub("", contents)
        contents = GcovrTestCompare.RE_COVERALLS_GIT.sub("", contents)
        return contents

    def __find_reference_files(
        self, output_pattern: list[str]
    ) -> Generator[tuple[Path, Path], None, None]:
        seen_files = set[str]()
        missing_files = set[str]()
        for pattern in output_pattern:
            # Iterate over a shallow copy to allow removal during iteration
            for reference_file in list(self.reference_files):
                if fnmatch.fnmatch(reference_file.name, pattern):
                    seen_files.add(reference_file.name)
                    test_file = self.output_dir / reference_file.name
                    if test_file.is_file():
                        self.reference_files.remove(reference_file)
                        yield test_file, reference_file
                    else:
                        missing_files.add(test_file.name)

        assert seen_files, f"Reference files for pattern {' '.join(output_pattern)}."
        assert not missing_files, (
            f"Missing test files for pattern {' '.join(output_pattern)}: {', '.join(missing_files)}"
        )

    def __update_reference_data(  # pragma: no cover
        self, reference_file: Path, content: str, encoding: str
    ) -> Path:
        reference_file = self.main_reference / reference_file.name
        reference_file.parent.mkdir(parents=True, exist_ok=True)

        with open(reference_file, "w", newline="", encoding=encoding) as out:
            out.write(content)

        return reference_file

    def __archive_difference_data(  # pragma: no cover
        self, data: str, reference_file: Path, encoding: str
    ) -> None:
        with zipfile.ZipFile(_ARCHIVE_DIFFERENCES_FILE, mode="a") as fh_zip:
            fh_zip.writestr(
                (self.main_reference / reference_file.name)
                .relative_to(Path.cwd().parent)
                .as_posix(),
                data.encode(encoding),
            )

    def __remove_duplicate_data(  # pragma: no cover
        self,
        encoding: str,
        coverage: str,
        test_file: Path,
        reference_file: Path,
    ) -> None:
        # Loop over the other coverage data
        for reference_dir in self.reference_dirs():  # pragma: no cover
            other_reference_file = reference_dir / test_file.name
            # ... and unlink the current file if it's identical to the other one.
            if (
                other_reference_file != reference_file
                and other_reference_file.is_file()
            ):  # pragma: no cover
                # Only remove it if we have no suffix or the other file has the same.
                if not _REFERENCE_DIR_OS_SUFFIX or other_reference_file.name.endswith(
                    _REFERENCE_DIR_OS_SUFFIX
                ):
                    with other_reference_file.open(encoding=encoding, newline="") as f:
                        if coverage == f.read():
                            os.unlink(reference_file)
                break

        for reference_dir in self.reference_dirs():  # pragma: no cover
            # Check if folder is empty
            if reference_dir.exists() and len(list(reference_dir.glob("*"))) == 0:
                os.rmdir(str(reference_dir))

    @staticmethod
    def assert_equals(
        reference_file: Path, reference: str, test_file: Path, test: str, encoding: str
    ) -> None:
        """Assert that the given files are equal."""
        extension = reference_file.suffix
        check_output: list[str] = []
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

            if (
                compare_output := compare_xml(el_reference, el_test)
            ) is not None:  # pragma: no cover
                check_output.append(
                    f"-- {reference_file}\n++ {test_file}\n{compare_output}"
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
                    fromfile=str(reference_file),
                    tofile=str(test_file),
                )
            )

            if diff_lines:  # pragma: no cover
                check_output.append("".join(diff_lines))

        if extension == ".xml":
            schema: Path | None = None
            if "cobertura" in reference_file.name:
                schema = _BASE_DIRECTORY / "cobertura.coverage-04.dtd"
            elif "jacoco" in reference_file.name:
                schema = _BASE_DIRECTORY / "JaCoCo.report.dtd"
            elif "clover" in reference_file.name:
                schema = _BASE_DIRECTORY / "clover.xsd"
            elif "sonarqube" in reference_file.name:
                schema = _BASE_DIRECTORY / "sonar-generic-coverage.xsd"

            if schema is not None:
                if schema.suffix == ".dtd":

                    def run_xmllint() -> str | None:
                        dtd_schema = etree.DTD(str(schema))  # nosec # We parse our trusted XSD files here
                        doc = etree.parse(str(test_file))  # nosec # We parse our test files here
                        return (
                            None
                            if dtd_schema.validate(doc)
                            else f"DTD validation error for {test_file}:\n{dtd_schema.error_log}"
                        )

                else:

                    def run_xmllint() -> str | None:
                        xmlschema_doc = etree.parse(str(schema))  # nosec # We parse our trusted XSD files here
                        xmlschema = etree.XMLSchema(xmlschema_doc)
                        doc = etree.parse(str(test_file))  # nosec # We parse our test files here
                        return (
                            None
                            if xmlschema.validate(doc)
                            else f"XSD validation error for {test_file}:\n{xmlschema.error_log}"
                        )

                if (validation_error := run_xmllint()) is not None:
                    check_output.append(validation_error)

        if check_output:  # pragma: no cover
            raise AssertionError("\n\n".join(check_output))

    def compare_files(
        self,
        *,
        output_pattern: list[str],
        scrub: Callable[[str], str] | None = None,
        translate_new_line: bool = True,
        encoding: str = "utf-8",
        lambda_force_files_present: Callable[[Path, Path], bool] | None = None,
    ) -> None:
        """Compare the files with the given patterns."""
        if self.generate_reference:  # pragma: no cover
            for pattern in output_pattern:
                for generated_file in self.output_dir.glob(pattern):
                    reference_file = self.main_reference / generated_file.name
                    if not reference_file.exists():
                        reference_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(generated_file, reference_file)

        all_compare_errors = []
        for test_file, reference_file in self.__find_reference_files(output_pattern):
            with test_file.open(encoding=encoding, newline="") as fh_in:
                try:
                    test_content = fh_in.read()
                    if scrub is not None:
                        test_content = scrub(test_content)
                except UnicodeDecodeError as e:  # pragma: no cover
                    raise AssertionError(
                        f"Unable to read test file {test_file}: {e}"
                    ) from e

            # Overwrite the file created above with the scrubbed content
            if self.generate_reference:  # pragma: no cover
                with reference_file.open("w", encoding=encoding, newline="") as fh_out:
                    fh_out.write(test_content)
                reference_content = test_content
            else:
                with reference_file.open(encoding=encoding, newline="") as fh_in:
                    reference_content = fh_in.read()

            # This files should always be created if there is an HTML report
            force_file_present = (
                lambda_force_files_present
                and lambda_force_files_present(self.main_reference, test_file)
            )
            try:
                self.assert_equals(
                    reference_file,
                    self.__translate_newlines_if_windows(reference_content)
                    if translate_new_line
                    else reference_content,
                    test_file,
                    self.__translate_newlines_if_windows(test_content)
                    if translate_new_line
                    else test_content,
                    encoding,
                )

                if force_file_present and reference_file.parent != self.main_reference:
                    reference_file = self.__update_reference_data(
                        reference_file, test_content, encoding
                    )
                    if self.archive_differences:
                        self.__archive_difference_data(
                            test_content, reference_file, encoding
                        )
            except AssertionError as e:  # pragma: no cover
                all_compare_errors.append(str(e) + "\n")
                if self.update_reference:
                    reference_file = self.__update_reference_data(
                        reference_file, test_content, encoding
                    )
                if self.archive_differences:
                    self.__archive_difference_data(
                        test_content, reference_file, encoding
                    )

            if (
                (self.generate_reference or self.update_reference)
                and reference_file.parent == self.main_reference
                and not force_file_present
            ):  # pragma: no cover
                self.__remove_duplicate_data(
                    encoding, test_content, test_file, reference_file
                )

        if all_compare_errors:  # pragma: no cover
            raise AssertionError(f"Differences found:\n{''.join(all_compare_errors)}")

    def raise_not_compared_reference_files(self) -> None:
        """Must be called at the end of the test to get the missing compare calls."""

        not_compared_files = len(self.reference_files) == 0
        message = f"Not compared files found, update the test: {', '.join(str(p) for p in self.reference_files)}"
        self.reference_files.clear()
        if not not_compared_files:
            raise AssertionError(message)


class GcovrTestExec:
    """Builder to compile the test executable."""

    def __init__(  # type: ignore[no-untyped-def]
        self,
        *,
        output_dir: Path,
        test_name: str | None,
        test_id: str,
        capsys: pytest.CaptureFixture[str],
        check,
        markers: list[pytest.Mark],
        compare: GcovrTestCompare,
    ):
        """Init the builder."""
        self.output_dir = output_dir
        self.test_name = test_name
        self.test_id = test_id
        self.capsys = capsys
        self.check = check
        self.markers = markers
        self._compare = compare
        self.use_llvm_profdata = False

    @staticmethod
    def is_linux() -> bool:
        """Query if we are running under Linux."""
        return IS_LINUX

    @staticmethod
    def is_darwin() -> bool:
        """Query if we are running under MacOs."""
        return IS_DARWIN

    @staticmethod
    def is_windows() -> bool:
        """Query if we are running under Windows."""
        return IS_WINDOWS

    @staticmethod
    def is_gcc() -> bool:
        """Query if we are testing with GCC."""
        return IS_GCC

    @staticmethod
    def is_llvm() -> bool:
        """Query if we are testing with LLVM/clang."""
        return not IS_GCC

    @staticmethod
    def cc_version() -> int:
        """Query the version of CC."""
        return CC_VERSION

    @staticmethod
    def is_cxx_lambda_expression_available() -> bool:
        """Query if we are testing with LLVM/clang."""
        return not GCOVR_TEST_USE_CXX_LAMBDA_EXPRESSIONS

    @staticmethod
    def is_in_gcc_help(string: str) -> bool:
        """Check if the given string is in part of the GCC help."""
        return string in _CC_HELP_OUTPUT

    @staticmethod
    def use_gcc_json_format() -> bool:
        """Query if we can use the GCC JSON intermediate format."""
        return USE_GCC_JSON_INTERMEDIATE_FORMAT

    @staticmethod
    def gcov() -> list[str]:
        """Get the gcov command to use."""
        return [str(e) for e in GCOV]

    def copy_source(self, source: Path | None = None) -> None:
        """Copy the test data to the output."""
        if source is None:
            source = Path.cwd() / "source"
            if (source / self.test_id).exists():
                source = source / self.test_id
            elif self.test_name is not None and (source / self.test_name).exists():
                source = source / self.test_name
            if not source.exists():
                return

            if source.is_file():
                source = Path(
                    Path.cwd().parent
                    / source.read_text(encoding="utf-8").splitlines()[0]
                    / "source"
                )

        if not source.exists():
            raise ValueError(f"Source data {source.absolute()} does not exist.")
        if source.is_file():
            shutil.copy(source, self.output_dir)
        else:
            for entry in source.glob("*"):
                print(f"Copying {entry} to {self.output_dir}", file=stderr)
                if entry.is_dir():
                    shutil.copytree(entry, self.output_dir / entry.name)
                else:
                    shutil.copy(entry, self.output_dir)

    def skip(self, message: str) -> NoReturn:
        """Skip the current test."""
        self._compare.reference_files.clear()
        pytest.skip(message)

    def __get_env(self, env: dict[str, str] | None) -> dict[str, str]:
        if env is None:
            env = os.environ.copy()
        for name in ["CFLAGS", "CXXFLAGS"]:
            if name in env:
                del env[name]

        if self.use_llvm_profdata:
            env["LLVM_PROFDATA"] = str(
                CC.parent / CC.name.replace("clang", "llvm-profdata")
            )

        env["CC"] = str(CC)
        env["CXX"] = str(CXX)
        env["GCOV"] = shlex.join(str(e) for e in GCOV)

        return env

    @staticmethod
    def __get_subprocess_cmd(cwd: Path, args: list[str]) -> list[str]:
        """Get the subprocess command from the given arguments."""
        if not IS_WINDOWS or not args[0].startswith("./"):
            return args
        return [str(cwd / args[0]), *args[1:]]

    def run(
        self,
        *args: str | Path,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run the given arguments."""
        cmd = [str(arg) for arg in args]
        if cwd is None:
            cwd = self.output_dir
        elif not cwd.is_absolute():
            cwd = self.output_dir / cwd
        with log_command(self.capsys, cwd, cmd):
            # pylint: disable=subprocess-run-check
            process = subprocess.run(  # nosec
                self.__get_subprocess_cmd(cwd, cmd),
                capture_output=True,
                encoding="utf-8",
                env=self.__get_env(env),
                cwd=str(cwd),
            )
            with self.capsys.disabled():
                if process.stdout:
                    print(process.stdout, file=stdout)
                if process.stderr:
                    print(process.stderr, file=stderr)
            process.check_returncode()

        return process

    def run_parallel_from_directories(
        self,
        *args: str,
        env: dict[str, str] | None = None,
        cwd: list[Path],
    ) -> None:
        """Run the given arguments."""
        processes = list[subprocess.Popen[str]]()
        try:
            for index, current_cwd in enumerate(cwd, start=1):
                with self.capsys.disabled():
                    print(
                        f"\n[{index}] Starting in {current_cwd.relative_to(Path.cwd())}: {' '.join(args)}",
                        file=stderr,
                    )
                processes.append(
                    subprocess.Popen(  # nosec
                        self.__get_subprocess_cmd(current_cwd, list(args)),
                        encoding="utf-8",
                        env=self.__get_env(env),
                        cwd=str(current_cwd),
                    )
                )
        finally:
            for index, process in enumerate(processes, start=1):
                process.wait()
                with self.capsys.disabled():
                    print(
                        f"\n[{index}] done with exitcode {process.returncode}",
                        file=stderr,
                    )
        if any(process.returncode != 0 for process in processes):
            raise subprocess.CalledProcessError(1, ["Not all processes are successful"])

    def cc(
        self,
        *args: str | Path,
        cwd: Path | None = None,
        launcher: str | None = None,
    ) -> None:
        """Run CC with the given arguments."""
        args = (
            CC,
            *(_CFLAGS_PROFDATA if self.use_llvm_profdata else _CFLAGS),
            *args,
        )
        if launcher is not None:
            args = (launcher, *args)
        self.run(*args, cwd=cwd)

    def cxx(
        self,
        *args: str | Path,
        cwd: Path | None = None,
        launcher: str | None = None,
    ) -> None:
        """Run CXX with the given arguments."""
        args = (
            CXX,
            *(_CXXFLAGS_PROFDATA if self.use_llvm_profdata else _CXXFLAGS),
            *args,
        )
        if launcher is not None:
            args = (launcher, *args)
        self.run(*args, cwd=cwd)

    def cc_compile(
        self,
        source: str | Path,
        *,
        target: str | None = None,
        options: List[str] | None = None,
        cwd: Path | None = None,
        launcher: str | None = None,
    ) -> str:
        """Compile the given source and return the target."""
        target = str(Path(source).with_suffix(".o")) if target is None else target
        if options is None:
            options = []
        self.cc(*options, "-c", source, "-o", target, cwd=cwd, launcher=launcher)
        return target

    def cxx_compile(
        self,
        source: str | Path,
        *,
        target: str | None = None,
        options: List[str] | None = None,
        cwd: Path | None = None,
        launcher: str | None = None,
    ) -> str:
        """Compile the given source and return the target."""
        target = str(Path(source).with_suffix(".o")) if target is None else target
        if options is None:
            options = []
        self.cxx(*options, "-c", source, "-o", target, cwd=cwd, launcher=launcher)
        return target

    def cc_link(
        self,
        executable: str | Path,
        *args: str | Path,
        cwd: Path | None = None,
        launcher: str | None = None,
    ) -> None:
        """Link the given objects and return the full path of the executable."""
        self.cc(*args, "-o", executable, cwd=cwd, launcher=launcher)

    def cxx_link(
        self,
        executable: str,
        *args: str | Path,
        cwd: Path | None = None,
        launcher: str | None = None,
    ) -> None:
        """Link the given objects and return the full path of the executable."""
        self.cxx(*args, "-o", executable, cwd=cwd, launcher=launcher)

    def gcovr(
        self,
        *args: str | Path,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        use_main: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        """Run GCOVR with the given arguments"""
        if use_main:
            cwd = cwd or self.output_dir
            with chdir(cwd):
                with mock.patch.dict("os.environ", env or {}, clear=True):
                    cmd = ["--gcov-executable", shlex.join(str(e) for e in GCOV)] + [
                        str(arg) for arg in args
                    ]
                    with log_command(self.capsys, cwd, ["gcovr-main", *cmd]):
                        returncode = gcovr_main(cmd)
                        out, err = self.capsys.readouterr()
                        with self.capsys.disabled():
                            print(out, file=stdout)
                            print(err, file=stderr)
                    return subprocess.CompletedProcess(args, returncode, out, err)
        else:
            return self.run("gcovr", *args, cwd=cwd, env=env)

    def __check_and_update_marker(self, required_marker: str) -> None:
        if not any(m.name == required_marker for m in self.markers):
            raise RuntimeError(f"Marker '{required_marker}' not found in test markers.")
        self.markers = [m for m in self.markers if m.name != required_marker]

    # Compare methods for our own formats
    def compare_csv(self) -> None:
        """Compare the CSV output files."""
        with self.check:
            self.__check_and_update_marker("csv")
            self._compare.compare_files(
                output_pattern=["coverage*.csv"],
                translate_new_line=False,
            )

    def compare_json(self) -> None:
        """Compare the JSON output files."""
        with self.check:
            self.__check_and_update_marker("json")
            self._compare.compare_files(
                output_pattern=["coverage*.json"],
            )

    def compare_html(self, encoding: str = "utf8") -> None:
        """Compare the HTML report files."""
        with self.check:
            self.__check_and_update_marker("html")
            self._compare.compare_files(
                output_pattern=["coverage*.html", "coverage*.js", "coverage*.css"],
                encoding=encoding,
                lambda_force_files_present=(
                    lambda reference_dir, test_file: bool(
                        test_file.suffix in (".css", ".js")
                        and list(reference_dir.glob("*.html"))
                    )
                ),
            )

    def compare_txt(self) -> None:
        """Compare the text output files."""
        with self.check:
            self.__check_and_update_marker("txt")
            self._compare.compare_files(
                output_pattern=["coverage*.txt"],
                scrub=self._compare.scrub_txt,
            )

    def compare_markdown(self) -> None:
        """Compare the markdown output files."""
        with self.check:
            self.__check_and_update_marker("markdown")
            self._compare.compare_files(
                output_pattern=["coverage*.md"],
            )

    # Compare methods for other formats

    def compare_clover(self) -> None:
        """Compare the clover output files."""
        with self.check:
            self.__check_and_update_marker("clover")
            self._compare.compare_files(
                output_pattern=["clover*.xml"],
                scrub=self._compare.scrub_xml,
            )

    def compare_cobertura(self) -> None:
        """Compare the cobertura output files."""
        with self.check:
            self.__check_and_update_marker("cobertura")
            self._compare.compare_files(
                output_pattern=["cobertura*.xml"],
                scrub=self._compare.scrub_cobertura,
            )

    def compare_coveralls(self) -> None:
        """Compare the coveralls output files."""
        with self.check:
            self.__check_and_update_marker("coveralls")
            self._compare.compare_files(
                output_pattern=["coveralls*.json"],
                scrub=self._compare.scrub_coveralls,
            )

    def compare_jacoco(self) -> None:
        """Compare the jacoco output files."""
        with self.check:
            self.__check_and_update_marker("jacoco")
            self._compare.compare_files(
                output_pattern=["jacoco*.xml"],
                scrub=self._compare.scrub_xml,
            )

    def compare_lcov(self) -> None:
        """Compare the LCOV output files."""
        with self.check:
            self.__check_and_update_marker("lcov")
            self._compare.compare_files(
                output_pattern=["coverage*.lcov"],
                scrub=self._compare.scrub_lcov,
            )

    def compare_sonarqube(self) -> None:
        """Compare the sonarqube output files."""
        with self.check:
            self.__check_and_update_marker("sonarqube")
            self._compare.compare_files(
                output_pattern=["sonarqube*.xml"],
            )

    def raise_not_used_markers(self) -> None:
        """Must be called at the end of the test to get the markers which were not used."""

        if self.markers:
            raise AssertionError(
                "Following markers were not used: "
                + ", ".join(m.name for m in self.markers)
            )


@pytest.fixture(scope="function")
def gcovr_test_exec(  # type: ignore[no-untyped-def]
    request: pytest.FixtureRequest,
    capsys: pytest.CaptureFixture[str],
    check,
) -> Generator[GcovrTestExec, None, None]:
    """Test fixture to build an object/executable and run gcovr tool with comparison of files."""
    function_name = request.node.name
    parameter = None
    if "[" in function_name:
        function_name, parameter = function_name.split("[", maxsplit=1)
        parameter = parameter[:-1]
    test_id_parts = list[str]()
    if function_name != "test":
        test_id_parts.append(function_name[5:].replace("_", "-"))
    if parameter is not None:
        test_id_parts.append(parameter.replace("_", "-"))
    test_id = "-".join(test_id_parts)
    with chdir(request.path.parent) as _test_dir:
        with create_output(test_id, request) as output_dir:
            test_exec = GcovrTestExec(
                output_dir=output_dir,
                test_name=test_id_parts[0] if test_id_parts else None,
                test_id=test_id,
                capsys=capsys,
                check=check,
                markers=[
                    m
                    for m in request.node.iter_markers()
                    if m.name not in ("skipif", "parametrize")
                ],
                compare=GcovrTestCompare(
                    output_dir=output_dir,
                    test_id=test_id,
                    capsys=capsys,
                    generate_reference=request.config.getoption("generate_reference"),
                    update_reference=request.config.getoption("update_reference"),
                    archive_differences=request.config.getoption("archive_differences"),
                ),
            )
            test_exec.copy_source()

            yield test_exec
            test_exec.raise_not_used_markers()
            test_exec._compare.raise_not_compared_reference_files()
