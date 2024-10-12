# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.1, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.1
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

"""
Script to generate the installer for gcovr.
"""

from runpy import run_path
import time
from setuptools import setup, find_packages
from os import path
import re


version = run_path("./gcovr/version.py")["__version__"]
# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

long_description = re.sub(
    r"^\.\. image:: \./",
    rf".. image:: https://raw.githubusercontent.com/gcovr/gcovr/{version}/",
    long_description,
    flags=re.MULTILINE,
)
long_description = re.sub(
    r":option:`(.*?)<gcovr.*?>`", r"``\1``", long_description, flags=re.MULTILINE
)

setup(
    name="gcovr",
    version=(
        version.replace("+main", f".dev{int(time.time())}+main")
        if version.endswith("+main")
        else version
    ),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    platforms=["any"],
    python_requires=">=3.8",
    packages=find_packages(include=["gcovr*"]),
    install_requires=[
        "jinja2",
        "lxml",
        "colorlog",
        "pygments>=2.13.0",
        "tomli >= 1.1.0 ; python_version < '3.11'",
    ],
    package_data={
        "gcovr": [
            "formats/html/*/*.css",
            "formats/html/*/*.html",
            "formats/html/*/pygments.*",
        ],
    },
    entry_points={
        "console_scripts": [
            "gcovr=gcovr.__main__:main",
        ],
    },
)
