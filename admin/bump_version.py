#!/usr/bin/env PYTHONPATH=./gcovr python3

# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2+main, a parsing and reporting tool for gcov.
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

import copy
import os
import logging
import re
import subprocess  # nosec # Commands are trusted.
import sys
import time
from typing import Callable, Iterator

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
    return "main" if ".dev" in version else version


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
    # no header found
    else:
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
    #    Next Release
    #    ------------
    # to:
    #    x.y (Day Month Year)
    #    --------------------
    next_release = "Next Release"
    iter_lines = iter(lines)
    for line in iter_lines:
        if line == next_release:
            line = f"{version} ({time.strftime('%d %B %Y')})"
            new_lines.extend([line, "-" * len(line)])
            iter_lines.__next__()  # pylint: disable=unnecessary-dunder-call
            break
        new_lines.append(line)
    else:
        raise RuntimeError(f"Call of {next_release!r} not found in {filename!r}.")

    new_lines.extend(iter_lines)

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
        new_lines.append(line)

    return new_lines


def update_reference_data(_filename: str, lines: list[str], version: str) -> list[str]:
    """Update the version in the reference data."""
    new_lines = []

    def replace_html_version(matches: re.Match[str]) -> str:
        return f"{matches.group(1)}{get_read_the_docs_version(version)}{matches.group(2)}{version}{matches.group(3)}"

    def replace_xml_version(matches: re.Match[str]) -> str:
        return f"{matches.group(1)}{version}{matches.group(2)}"

    for line in lines:
        if "Generated by: " in line:
            line = re.sub(
                r'(Generated by: <a href="http://gcovr.com/en/).+?(">GCOVR \(Version ).+?(\)</a>)',
                replace_html_version,
                line,
            )
        if "version=" in line:
            line = re.sub(
                r'(version="gcovr ).+?(">)',
                replace_xml_version,
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


def update_source_date_epoch(
    filename: str, lines: list[str], _version: str
) -> list[str]:
    """Update the timestamp in the test."""
    new_lines = []

    env_source_date_epoch = 'env["SOURCE_DATE_EPOCH"] = '
    iter_lines = iter(lines)
    for line in iter_lines:
        if line.startswith(env_source_date_epoch):
            line = re.sub(r"\d+", str(int(time.time())), line)
            new_lines.append(line)
            break
        new_lines.append(line)
    else:
        raise RuntimeError(
            f"Call of {env_source_date_epoch!r} not found in {filename!r}."
        )

    new_lines.extend(iter_lines)

    return new_lines


def main(version: str) -> None:
    """Main entry point."""
    for root, dirs, files in os.walk(".", topdown=True):

        def skip_dir(directory: str) -> bool:
            return directory in [".git", ".venv"] or directory.startswith(".nox")

        dirs[:] = [directory for directory in dirs if not skip_dir(directory)]

        for filename in files:
            handlers = list[Callable[[str, list[str], str], list[str]]]()
            _, extension = os.path.splitext(filename)
            fullname = os.path.join(root, filename)
            if filename.endswith(".py") and filename not in ["version.py"]:
                handlers.append(add_copyright_header_to_python_file)
            if filename == "__main__.py":
                handlers.append(update_copyright_string)
            if filename == "LICENSE.txt":
                handlers.append(update_license)
            if filename == "test_gcovr.py":
                handlers.append(update_source_date_epoch)
            if (
                extension in [".xml", ".html"]
                and ("reference" in fullname or "examples" in fullname)
                and "html-encoding-" not in fullname
            ):
                handlers.append(update_reference_data)

            if not version.endswith("+main"):
                if filename == "CHANGELOG.rst":
                    handlers.append(update_changelog)
                if filename.endswith(".rst"):
                    handlers.append(update_documentation)

            if handlers:
                with open(fullname, encoding="utf-8") as f:
                    lines = list(line.rstrip() for line in f)
                new_lines = copy.copy(
                    lines
                )  # use a copy because of the compare at the end
                for handler in handlers:
                    new_lines = handler(fullname, new_lines, version)
                if new_lines != lines:
                    logging.info(f"Modifying {fullname}")
                    with open(fullname, "w", encoding="utf-8") as f:
                        for line in new_lines:
                            f.write(line + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:])
