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

import gzip
import pathlib
import sys


def main(json_file: str, json_gz_file: str) -> None:
    """Main entry point."""
    with pathlib.Path(json_file).open("rt", encoding="UTF-8") as fh_in:
        with gzip.open(json_gz_file, "wt", encoding="UTF-8") as fh_out:
            fh_out.write(
                fh_in.read().replace("$__PWD__$", pathlib.Path.cwd().as_posix())
            )


if __name__ == "__main__":
    main(*sys.argv[1:])
