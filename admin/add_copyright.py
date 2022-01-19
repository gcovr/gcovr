#!/usr/bin/env PYTHONPATH=./gcovr python3

# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2021 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

import copy
import os
import re
import subprocess

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
    "This software is distributed under the BSD License.",
    "Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,",
    "the U.S. Government retains certain rights in this software.",
]
HEADER_END = (
    " ****************************************************************************"
)


def getLicenseSection(filename, comment_char="#"):
    yield comment_char + "  ************************** Copyrights and license ***************************"
    yield comment_char
    yield comment_char + f" This file is part of gcovr {VERSION}, a parsing and reporting tool for gcov."
    yield comment_char + " https://gcovr.com/en/stable"
    yield comment_char
    yield comment_char + " _____________________________________________________________________________"
    yield comment_char
    for line in COPYRIGHT:
        yield comment_char + " " + line
    yield comment_char + " For more information, see the README.rst file."
    yield comment_char
    yield comment_char + HEADER_END


def addCopyrightToPythonFile(filename, lines):
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
    for line in getLicenseSection(filename):
        newLines.append(line)

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


def main():
    for root, dirs, files in os.walk(".", topdown=True):
        for skip_dir in [".git", "reference"]:
            if skip_dir in dirs:
                dirs.remove(skip_dir)

        for filename in files:
            handler = None
            fullname = os.path.join(root, filename)
            if filename.endswith(".py"):
                handler = addCopyrightToPythonFile

            if handler is not None:
                with open(fullname) as f:
                    lines = list(line.rstrip() for line in f)
                if filename == "__main__.py":
                    copyright_string = ["COPYRIGHT = ("]
                    for line in COPYRIGHT:
                        copyright_string.append(f'   "{line}\\n"')
                    copyright_string.append(")")
                    copyright_string.append("")
                    lines = re.sub(
                        r"COPYRIGHT = \(\n(?:[^\n]+\n)+\)\n",
                        "\n".join(copyright_string).replace("\\", "\\\\"),
                        "\n".join(lines),
                    ).split("\n")
                    lines = [line.rstrip() for line in lines]
                newLines = handler(
                    fullname, copy.copy(lines)
                )  # use a copy because of the compare in the next line
                if newLines != lines:
                    print("Modifying {}".format(fullname))
                    with open(fullname, "w") as f:
                        for line in newLines:
                            f.write(line + "\n")


if __name__ == "__main__":
    main()
