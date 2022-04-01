#!/usr/bin/env PYTHONPATH=./gcovr python3

# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.1, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2022 the gcovr authors
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
import subprocess
import time
from typing import List

import gcovr.version

DATE = subprocess.check_output(
    ["git", "log", "-1", "--format=format:%ad", "--date=short"],
    universal_newlines=True,
)
YEAR = DATE[:4]
VERSION = gcovr.version.__version__
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


def getLicenseSection(comment_char: str = "#"):
    yield comment_char + "  ************************** Copyrights and license ***************************"
    yield comment_char
    yield comment_char + f" This file is part of gcovr {VERSION}, a parsing and reporting tool for gcov."
    yield comment_char + " https://gcovr.com/en/stable"
    yield comment_char
    yield comment_char + " _____________________________________________________________________________"
    yield comment_char
    for line in COPYRIGHT:
        yield comment_char + " " + line
    yield comment_char
    yield comment_char + " " + LICENSE
    yield comment_char + " For more information, see the README.rst file."
    yield comment_char
    yield comment_char + HEADER_END


def addCopyrightHeaderToPythonFile(filename: str, lines: List[str]):
    # Empty file should be kept empty
    if len(lines) == 0:
        return lines

    newLines = []
    # Keep the Shebang
    if lines[0].startswith("#!"):
        newLines.append(lines.pop(0))
        newLines.append("")

    # Set the encoding
    if lines[0].startswith("# -*- coding:"):
        lines.pop(0)
    newLines.append("# -*- coding:utf-8 -*-")
    newLines.append("")

    # Add license information
    newLines.extend(getLicenseSection())

    iterLines = iter(lines)

    # skip lines until header end marker
    headerEndReached = False
    for line in iterLines:
        if len(line) > 0 and line == "#" + HEADER_END:
            headerEndReached = True
            break

    if headerEndReached:
        for line in iterLines:
            if line != "":
                # Use one empty line
                newLines.append("")
                # except for classes or functions, there we need two.
                if line.startswith("class") or line.startswith("def"):
                    newLines.append("")
                newLines.append(line)
                break
        # keep all other lines
        newLines.extend(iterLines)
    # no header found
    else:
        newLines.append("\n")
        # keep all other lines
        newLines.extend(lines)

    return newLines


def updateCopyrightString(filename: str, lines: List[str]):
    newLines = []

    iterLines = iter(lines)
    for line in iterLines:
        newLines.append(line)
        if line == "COPYRIGHT = (":
            break
    else:
        raise RuntimeError(f"Start of copyright not found in {filename!r}.")

    for line in COPYRIGHT:
        newLines.append(f'    "{line}\\n"')

    for line in iterLines:
        if line == ")":
            newLines.append(line)
            break
    else:
        raise RuntimeError(f"End of copyright not found in {filename!r}.")

    newLines.extend(iterLines)

    return newLines


def updateCallOfReleaseChecklist(filename: str, lines: List[str]):
    newLines = []

    callReleaseChecklist = "admin/release_checklist"
    callFound = False
    for line in lines:
        if callReleaseChecklist in line:
            line = re.sub(r"\d+\.\d+$", VERSION, line)
            callFound = True
        newLines.append(line)
    if not callFound:
        raise RuntimeError(
            f"Call of {callReleaseChecklist!r} not found in {filename!r}."
        )

    return newLines


def updateChangelog(filename: str, lines: List[str]):
    newLines = []

    # We need to also change the line after "Next Release"
    # because the minus must have the same length than the
    # headline to have valid RST.
    # We change:
    #    Next Release
    #    ------------
    # to:
    #    x.y (Day Month Year)
    #    --------------------
    nextLine = None
    for line in lines:
        if line == "Next Release":
            line = f"{VERSION} ({time.strftime('%d %B %Y')})"
            nextLine = "-" * len(line)
        elif nextLine:
            line = nextLine
            nextLine = None
        newLines.append(line)

    return newLines


def updateReadme(filename: str, lines: List[str]):
    newLines = []

    iterLines = iter(lines)
    for line in iterLines:
        newLines.append(line)
        if line == ".. begin license":
            break
    else:
        raise RuntimeError(f"Start of license not found in {filename!r}.")

    newLines.append("")
    for line in COPYRIGHT:
        newLines.append(line)
    newLines.append("")
    newLines.append(LICENSE)

    for line in iterLines:
        if line == "See LICENSE.txt for full details.":
            newLines.append(line)
            break
    else:
        raise RuntimeError(f"Reference to LICENSE.txr not found in {filename!r}.")

    newLines.extend(iterLines)

    return newLines


def updatDocumentation(filename: str, lines: List[str]):
    newLines = []

    for line in lines:
        if "NEXT" in line:
            line = re.sub(
                r"(\.\. (?:versionadded|versionchanged|deprecated):: )NEXT",
                r"\g<1>" + VERSION,
                line,
            )
        newLines.append(line)

    return newLines


def updateLicense(filename: str, lines: List[str]):
    newLines = []

    for line in COPYRIGHT:
        newLines.append(line)
    newLines.append("")

    iterLines = iter(lines)
    for line in iterLines:
        if line == "All rights reserved.":
            newLines.append(line)
            break
    else:
        raise RuntimeError(f"Start of license not found in {filename!r}.")

    newLines.extend(iterLines)

    return newLines


def main():
    for root, dirs, files in os.walk(".", topdown=True):

        def skip_dir(dir: str) -> bool:
            return dir in [".git", "reference"] or dir.startswith(".nox")

        dirs[:] = [dir for dir in dirs if not skip_dir(dir)]

        for filename in files:
            handlers = []
            fullname = os.path.join(root, filename)
            if filename.endswith(".py"):
                handlers.append(addCopyrightHeaderToPythonFile)
            if filename == "__main__.py":
                handlers.append(updateCopyrightString)
            if filename == "deploy.yml":
                handlers.append(updateCallOfReleaseChecklist)
            if filename == "CHANGELOG.rst":
                handlers.append(updateChangelog)
            if filename == "README.rst":
                handlers.append(updateReadme)
            if filename.endswith(".rst"):
                handlers.append(updatDocumentation)
            if filename == "LICENSE.txt":
                handlers.append(updateLicense)

            if handlers:
                with open(fullname) as f:
                    lines = list(line.rstrip() for line in f)
                newLines = copy.copy(
                    lines
                )  # use a copy because of the compare at the end
                for handler in handlers:
                    newLines = handler(fullname, newLines)
                if newLines != lines:
                    logging.info("Modifying {}".format(fullname))
                    with open(fullname, "w") as f:
                        for line in newLines:
                            f.write(line + "\n")


if __name__ == "__main__":
    main()
