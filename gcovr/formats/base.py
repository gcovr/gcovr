# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 6.0+master, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2023 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

from typing import List

from ..options import GcovrConfigOption, Options
from ..coverage import CovData


class BaseHandler:
    def get_options() -> List[GcovrConfigOption]:
        return []

    def __init__(self, options: Options):
        global_options = [
            "timestamp",
            "root",
            "root_dir",
            "root_filter",
            "show_decision",
            "sort_branches",
            "sort_key",
            "sort_reverse",
            "search_paths",
            "source_encoding",
            "starting_dir",
            "filter",
            "exclude",
        ]
        option_dict = {}
        for name in global_options + [
            o if isinstance(o, str) else o.name for o in self.__class__.get_options()
        ]:
            option_dict[name] = options.get(name)
        self.options = Options(**option_dict)

    def read_report(self) -> CovData:
        raise RuntimeError("Function 'read_report' not implemented.")

    def write_report(self, covdata: CovData, output_file: str) -> None:
        raise RuntimeError("Function 'write_report' not implemented.")

    def write_summary_report(self, covdata: CovData, output_file: str) -> None:
        raise RuntimeError("Function 'write_summary_report' not implemented.")
