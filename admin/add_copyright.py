#!/usr/bin/env PYTHONPATH=./gcovr python3

# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 4.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2021 Spacetown <michael.foerderer@gmx.de>
# and possibly others.
# Copyright (c) 2013 Sandia Corporation.
# This software is distributed under the BSD License.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
# For more information, see the README.rst file.
#
# ****************************************************************************

import os
import re
import subprocess

import version

REGEX_EMAIL = re.compile(r"\d+\+([^@]+)@users\.noreply\.github\.com")
HEADER_END = (
    " ****************************************************************************"
)


def getLicenseSection(filename, comment_char="#"):
    yield comment_char + "  ************************** Copyrights and license ***************************"
    yield comment_char
    yield comment_char + " This file is part of gcovr {}, a parsing and reporting tool for gcov.".format(
        version.__version__
    )
    yield comment_char + " https://gcovr.com/en/stable"
    yield comment_char
    yield comment_char + " _____________________________________________________________________________"
    yield comment_char
    for name, year in getContributors(filename):
        yield comment_char + " Copyright (c) " + year + " " + name
    yield comment_char + " and possibly others."
    yield comment_char + " Copyright (c) 2013 Sandia Corporation."
    yield comment_char + " This software is distributed under the BSD License."
    yield comment_char + " Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,"
    yield comment_char + " the U.S. Government retains certain rights in this software."
    yield comment_char + " For more information, see the README.rst file."
    yield comment_char
    yield comment_char + HEADER_END


def getContributors(filename, sortBy="end"):
    yearsOfContributions = dict()
    emailByName = dict()
    newMailByOldMail = dict()
    nameByEmail = dict()
    newNameByOldName = dict()
    for line in subprocess.check_output(
        ["git", "log", "--format=format:%ad|%an|%ae", "--date=short", "--", filename],
        universal_newlines=True,
    ).split("\n"):
        (date, name, email) = line.split("|")
        year = date[:4]
        key = "{} <{}>".format(name, email)
        # User name is unknown, check if it was changed...
        if key not in yearsOfContributions:
            # User name is already known --> Get matching email address
            if name in emailByName:
                newMailByOldMail[email] = emailByName[name]  # Save changed email address
                email = newMailByOldMail[email]
            # Email address is already known --> Get matching user name
            elif email in nameByEmail:
                newNameByOldName[name] = nameByEmail[email]  # Save changed user name
                name = newNameByOldName[name]
            # User name is already known --> Get matching email address
            elif email in newMailByOldMail:
                email = newMailByOldMail[email]
                name = nameByEmail[email]
            # User name is already known --> Get matching email address
            elif name in newNameByOldName:
                name = newNameByOldName[name]
                email = emailByName[name]
            else:
                # Try to get the user name from the mail address
                match = REGEX_EMAIL.match(email)
                if match is not None:
                    if match.group(1) in emailByName:
                        name = match.group(1)
                        email = emailByName[name]
            # Update the key
            key = "{} <{}>".format(name, email)

            emailByName[name] = email
            nameByEmail[email] = name
        email = emailByName[name]
        # Add year to list, key is the user name followed by email address
        if key not in yearsOfContributions:
            yearsOfContributions[key] = set()
        yearsOfContributions[key].add(year)

    contributors = set()
    for (name, years) in yearsOfContributions.items():
        contributors.add((name, min(years), max(years)))

    # first sort by name
    contributors = sorted(contributors, key=lambda x: x[0])
    if sortBy == "start":
        contributors = sorted(contributors, key=lambda x: x[1], reverse=True)
    if sortBy == "end":
        contributors = sorted(contributors, key=lambda x: x[2], reverse=True)

    return list(
        (x[0], x[1] if x[1] == x[2] else "{}-{}".format(x[1], x[2]))
        for x in contributors
    )


def addCopyrightToPythonFile(filename, lines):
    # Empty file should be kept empty
    if len(lines) == 0:
        return lines

    newLines = []
    # Keep the Shebang
    if lines[0].startswith("#!"):
        newLines.append(lines.pop(0))
        newLines.append("")

    # Add encoding
    newLines.append("# -*- coding:utf-8 -*-")
    newLines.append("")

    # Add license information
    for line in getLicenseSection(filename):
        newLines.append(line)

    # Skip header and add rest of file
    headerEndReached = False
    skipEmptyLines = True
    for line in lines:
        if not headerEndReached:
            if len(line) > 0 and line[0] == "#" and line[1:] == HEADER_END:
                headerEndReached = True
                continue

        if headerEndReached:
            if skipEmptyLines:
                if len(line) == 0:
                    continue
                skipEmptyLines = False
                newLines.append("")
            newLines.append(line)

    if not headerEndReached:
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
                newLines = handler(fullname, lines)
                if newLines != lines:
                    print("Modifying {}".format(fullname))
                    with open(fullname, "w") as f:
                        for line in newLines:
                            f.write(line + "\n")


if __name__ == "__main__":
    main()
