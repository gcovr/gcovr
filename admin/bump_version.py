#!/usr/bin/env PYTHONPATH=./gcovr python3

# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.5+main, a parsing and reporting tool for gcov.
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

import copy
import os
import logging
import re
import subprocess  # nosec # Commands are trusted.
import sys
import time
import datetime
from typing import Callable, Iterator

SOURCE_DATE_EPOCH = int(time.time())
SOURCE_DATE_EPOCH_STR = str(SOURCE_DATE_EPOCH)
UTC_DATE_TIME = datetime.datetime.fromtimestamp(
    SOURCE_DATE_EPOCH, datetime.timezone.utc
).strftime("%Y-%m-%d %H:%M:%S UTC")
ISO_DATE_TIME = datetime.datetime.fromtimestamp(
    SOURCE_DATE_EPOCH, datetime.timezone.utc
).isoformat(sep=" ", timespec="seconds")
DATE = subprocess.check_output(  # nosec # We run on several system and do not know the full path
    ["git", "log", "-1", "--format=format:%ad", "--date=short"],
    universal_newlines=True,
)
YEAR = DATE[:4]
COPYRIGHT = [
    f"Copyright (c) 2013-{YEAR} the gcovr authors",
    "Copyright (c) 2013 Sandia Corporation.",
    "Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,",
    "the U.S. Government retains certain rights in this software.",
]
LICENSE = "This software is distributed under the 3-clause BSD License."
HEADER_END = (
    " ****************************************************************************"
)


def get_read_the_docs_version(version: str) -> str:
    """Get the version to use for ReadTheDocs."""
    return "main" if version.endswith("+main") else version


def get_copyright_header(version: str, comment_char: str = "#") -> Iterator[str]:
    """Get the content of the copyright header."""
    yield (
        comment_char
        + "  ************************** Copyrights and license ***************************"
    )
    yield comment_char
    yield (
        comment_char
        + f" This file is part of gcovr {version}, a parsing and reporting tool for gcov."
    )
    yield comment_char + f" https://gcovr.com/en/{get_read_the_docs_version(version)}"
    yield comment_char
    yield (
        comment_char
        + " _____________________________________________________________________________"
    )
    yield comment_char
    for line in COPYRIGHT:
        yield comment_char + " " + line
    yield comment_char
    yield comment_char + " " + LICENSE
    yield comment_char + " For more information, see the README.rst file."
    yield comment_char
    yield comment_char + HEADER_END


def add_copyright_header_to_python_file(
    _filename: str, lines: list[str], version: str
) -> list[str]:
    """Add the copyright header to the python file."""
    # Empty file should be kept empty
    if len(lines) == 0:
        return lines

    new_lines = []
    # Keep the Shebang
    if lines[0].startswith("#!"):
        new_lines.append(lines.pop(0))
        new_lines.append("")

    # Set the encoding
    if lines[0].startswith("# -*- coding:"):
        lines.pop(0)
    new_lines.append("# -*- coding:utf-8 -*-")
    new_lines.append("")

    # Add license information
    new_lines.extend(get_copyright_header(version))

    iter_lines = iter(lines)

    skipped_lines = []
    # skip lines until header end marker
    for line in iter_lines:
        if len(line) > 0 and line == "#" + HEADER_END:
            for line in iter_lines:
                if line != "":
                    # Use one empty line
                    new_lines.append("")
                    # except for classes or functions, there we need two.
                    if line.startswith("class") or line.startswith("def"):
                        new_lines.append("")
                    new_lines.append(line)
                    break
            break
        skipped_lines.append(line)
    # no header found, use all skipped lines
    else:
        new_lines.extend(skipped_lines)
        new_lines.append("\n")

    # keep all other lines
    new_lines.extend(iter_lines)

    return new_lines


def update_copyright_string(
    filename: str, lines: list[str], _version: str
) -> list[str]:
    """Update the copyright."""
    new_lines = []

    iter_lines = iter(lines)
    for line in iter_lines:
        new_lines.append(line)
        if line == "COPYRIGHT = (":
            break
    else:
        raise RuntimeError(f"Start of copyright not found in {filename!r}.")

    for line in COPYRIGHT:
        new_lines.append(f'    "{line}\\n"')

    for line in iter_lines:
        if line == ")":
            new_lines.append(line)
            break
    else:
        raise RuntimeError(f"End of copyright not found in {filename!r}.")

    new_lines.extend(iter_lines)

    return new_lines


def update_changelog(filename: str, lines: list[str], version: str) -> list[str]:
    """Update the version in the CHANGELOG."""
    new_lines = []

    # We need to also change the line after "Next Release"
    # because the minus must have the same length than the
    # headline to have valid RST.
    # We change:
    #    .. _next_release:
    #
    #    Next Release
    #    ------------
    # to:
    #    .. _release_x_y:
    #
    #    x.y (Day Month Year)
    #    --------------------
    iter_lines = iter(lines)

    next_release_link_target = ".. _next_release:"
    next_release_link_id = f"release_{version.replace('.', '_')}"
    for line in iter_lines:
        if line == next_release_link_target:
            new_lines.append(f".. _{next_release_link_id}:")
            break
        new_lines.append(line)
    else:
        raise RuntimeError(
            f"Call of {next_release_link_target!r} not found in {filename!r}."
        )

    next_release = "Next Release"
    for line in iter_lines:
        if line == next_release:
            line = f"{version} ({time.strftime('%d %B %Y')})"
            new_lines.extend([line, "-" * len(line)])
            iter_lines.__next__()  # pylint: disable=unnecessary-dunder-call
            break
        new_lines.append(line)
    else:
        raise RuntimeError(f"Call of {next_release!r} not found in {filename!r}.")

    new_lines += list(iter_lines)

    return new_lines


def update_documentation(_filename: str, lines: list[str], version: str) -> list[str]:
    """Update the references to the next version in the documentation."""
    new_lines = []

    for line in lines:
        if "NEXT" in line:
            line = re.sub(
                r"(\.\. (?:versionadded|versionchanged|deprecated|versionremoved):: )NEXT",
                r"\g<1>" + version,
                line,
            )
        # We need to also change the line after "Next Release"
        # because the minus must have the same length than the
        # headline to have valid RST.
        # We change:
        #    :ref:`next_release`
        # to:
        #    :ref:`release_x_y`
        line = re.sub(
            r":ref:`next_release`",
            f":ref:`release_{version.replace('.', '_')}`",
            line,
        )
        new_lines.append(line)

    return new_lines


def update_reference_data(_filename: str, lines: list[str], version: str) -> list[str]:
    """Update the version in the reference data."""
    new_lines = []

    def replace_html_version(matches: re.Match[str]) -> str:
        return f"{matches.group(1)}{get_read_the_docs_version(version)}{matches.group(2)}{version}{matches.group(3)}"

    def replace_xml_version(matches: re.Match[str]) -> str:
        return f"{matches.group(1)}{version}{matches.group(2)}"

    def replace_xml_timestamp(matches: re.Match[str]) -> str:
        return f"{matches.group(1)}{SOURCE_DATE_EPOCH_STR}{matches.group(2)}"

    for line in lines:
        if "Created using " in line:
            line = re.sub(
                r'(Created using <a href="http://gcovr.com/en/).+?(">GCOVR \(Version ).+?(\)</a>)',
                replace_html_version,
                line,
            )
        if "version=" in line:
            line = re.sub(
                r'(version="gcovr ).+?(">)',
                replace_xml_version,
                line,
            )
        if "+00:00" in line:
            line = re.sub(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\+00:00",
                ISO_DATE_TIME,
                line,
            )
        if '"run_at":' in line:
            line = re.sub(
                r'"run_at": "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} UTC",',
                rf'"run_at": "{UTC_DATE_TIME}",',
                line,
            )
        for att in ["timestamp", "clover", "generated"]:
            if f' {att}="' in line:
                line = re.sub(
                    rf'( {att}=")\d+(")',
                    replace_xml_timestamp,
                    line,
                )
        new_lines.append(line)

    return new_lines


def update_license(filename: str, lines: list[str], _version: str) -> list[str]:
    """Update the license file."""
    new_lines = [
        "BSD 3-Clause License",
        "",
    ]

    for line in COPYRIGHT:
        new_lines.append(line)
    new_lines.append("")

    iter_lines = iter(lines)
    for line in iter_lines:
        if line == "All rights reserved.":
            new_lines.append(line)
            break
    else:
        raise RuntimeError(f"Start of license not found in {filename!r}.")

    new_lines.extend(iter_lines)

    return new_lines


def update_source_date_epoch_for_pytest(
    filename: str, lines: list[str], _version: str
) -> list[str]:
    """Update the timestamp in the test."""
    new_lines = []

    env_source_date_epoch = '"SOURCE_DATE_EPOCH='
    iter_lines = iter(lines)
    for line in iter_lines:
        if line.lstrip().startswith(env_source_date_epoch):
            line = re.sub(r"\d+", SOURCE_DATE_EPOCH_STR, line)
            new_lines.append(line)
            break
        new_lines.append(line)
    else:
        raise RuntimeError(
            f"Call of {env_source_date_epoch!r} not found in {filename!r}."
        )

    new_lines.extend(iter_lines)

    return new_lines


def main(version: str, for_file: str | None = None) -> None:
    """Main entry point."""
    for root, dirs, files in os.walk(".", topdown=True):

        def skip_dir(directory: str) -> bool:
            return directory in [".git", ".venv"] or directory.startswith(".nox")

        dirs[:] = [directory for directory in dirs if not skip_dir(directory)]

        for filename in files:
            handlers = list[Callable[[str, list[str], str], list[str]]]()
            _, extension = os.path.splitext(filename)
            fullname = os.path.join(root, filename)
            if for_file is not None and os.path.abspath(for_file) != os.path.abspath(
                fullname
            ):
                continue
            if filename.endswith(".py") and filename not in ["version.py"]:
                handlers.append(add_copyright_header_to_python_file)
            if filename == "__main__.py":
                handlers.append(update_copyright_string)
            if filename == "LICENSE.txt":
                handlers.append(update_license)
            if filename == "pyproject.toml" and "config" not in fullname:
                handlers.append(update_source_date_epoch_for_pytest)
            if extension in [".xml", ".html", ".json"] and (
                "reference" in fullname or "examples" in fullname
            ):
                handlers.append(update_reference_data)

            if not version.endswith("+main"):
                if filename == "CHANGELOG.rst":
                    handlers.append(update_changelog)
                if filename.endswith(".rst"):
                    handlers.append(update_documentation)

            if handlers:
                encoding = "UTF-8"
                if "encoding-report-" in fullname:
                    encoding = (
                        fullname.replace("\\", "/")
                        .split("encoding-report-")[1]
                        .split("/")[0]
                    )
                if filename == "main.cp1252.cpp":
                    encoding = "cp1252"
                with open(fullname, encoding=encoding) as fh_in:
                    lines = fh_in.readlines()
                    trailing_newline = lines and lines[-1][-1] == "\n"
                    lines = list(line.rstrip() for line in lines)
                new_lines = copy.copy(
                    lines
                )  # use a copy because of the compare at the end
                for handler in handlers:
                    new_lines = handler(fullname, new_lines, version)
                if new_lines != lines:
                    logging.info("Modifying %s", fullname)
                    new_lines = list(f"{line}\n" for line in new_lines)
                    if not trailing_newline:
                        new_lines[-1] = new_lines[-1][:-1]
                    with open(fullname, "w", encoding=encoding) as fh_out:
                        fh_out.writelines(new_lines)


if __name__ == "__main__":
    main(*sys.argv[1:])
