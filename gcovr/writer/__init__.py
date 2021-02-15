# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 4.2, a parsing and reporting tool for gcov.
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

from ..configuration import GcovrConfigOption
from .json import Json
from .cobertura import Cobertura
from .html import Html
from .txt import Txt, print_report, print_summary_report
from .csv import Csv
from .sonarqube import Sonarqube
from .coveralls import Coveralls

WRITERS = [Json(), Txt(), Html(), Csv(), Cobertura(), Sonarqube(), Coveralls()]


class Writers:
    __options_called = False

    @classmethod
    def options(_cls):
        if not _cls.__options_called:
            _cls.__options_called = True
            for w in WRITERS:
                for o in w.options():
                    yield o

    @classmethod
    def check_options(_cls, options, logger):
        for w in WRITERS:
            w.check_options(options, logger)

    @classmethod
    def write(_cls, covdata, options, logger):
        writer_error_occurred = False
        reports_were_written = False
        default_output_used = False
        default_output = (
            GcovrConfigOption.OutputOrDefault(None)
            if options.output is None
            else options.output
        )

        for w in WRITERS:
            for output_choices, writer, on_no_output in w.writers(options, logger):
                output = GcovrConfigOption.OutputOrDefault.choose(
                    output_choices, default=default_output
                )
                if output is not None and output is default_output:
                    default_output_used = True
                    if not output.is_dir:
                        default_output = None
                if output is not None:
                    if writer(covdata, output.abspath, options):
                        writer_error_occurred = True
                    reports_were_written = True
                else:
                    on_no_output()

        if not reports_were_written:
            print_report(
                covdata,
                "-" if default_output is None else default_output.abspath,
                options,
            )
            default_output = None

        if (
            default_output is not None
            and default_output.value is not None
            and not default_output_used
        ):
            logger.warn(
                "--output={!r} option was provided but not used.", default_output.value
            )

        if options.print_summary:
            print_summary_report(covdata)

        if writer_error_occurred:
            raise RuntimeError("Error occurred while printing reports")
