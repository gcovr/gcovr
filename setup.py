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

"""
Script to generate the installer for gcovr.
"""

import os
import re
import time

from runpy import run_path
from setuptools import setup, find_packages


version = run_path("./gcovr/version.py")["__version__"]
if version.endswith("+main"):
    # Add a default if environment is not set
    os.environ["TIMESTAMP"] = os.environ.get("TIMESTAMP", str(int(time.time())))
    # ...and use this timestamp.
    version = version.replace("+main", f".dev{os.environ['TIMESTAMP']}+main")
# read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.rst"), encoding="utf-8") as f:
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
    version=version,
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
