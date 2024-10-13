# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.2, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.2
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

import logging
from typing import Callable, List, Optional, Tuple

from ..options import GcovrConfigOption, Options

from ..coverage import CovData

# the handler
from .gcov import GcovHandler
from .clover import CloverHandler
from .cobertura import CoberturaHandler
from .coveralls import CoverallsHandler
from .csv import CsvHandler
from .html import HtmlHandler
from .jacoco import JaCoCoHandler
from .json import JsonHandler
from .lcov import LcovHandler
from .sonarqube import SonarqubeHandler
from .txt import TxtHandler

LOGGER = logging.getLogger("gcovr")


def get_options() -> List[GcovrConfigOption]:
    return [
        o
        for o in [
            *GcovHandler.get_options(),
            *CloverHandler.get_options(),
            *CoberturaHandler.get_options(),
            *CoverallsHandler.get_options(),
            *CsvHandler.get_options(),
            *HtmlHandler.get_options(),
            *JaCoCoHandler.get_options(),
            *JsonHandler.get_options(),
            *LcovHandler.get_options(),
            *SonarqubeHandler.get_options(),
            *TxtHandler.get_options(),
        ]
        if not isinstance(o, str)
    ]


def validate_options(options) -> CovData:
    for handler in [
        GcovHandler,
        CloverHandler,
        CoberturaHandler,
        CoverallsHandler,
        CsvHandler,
        HtmlHandler,
        JaCoCoHandler,
        JsonHandler,
        LcovHandler,
        SonarqubeHandler,
        TxtHandler,
    ]:
        handler(options).validate_options()


def read_reports(options) -> CovData:
    if options.json_add_tracefile or options.cobertura_add_tracefile:
        covdata: CovData = JsonHandler(options).read_report() or {}
        covdata.update(CoberturaHandler(options).read_report() or {})
    else:
        covdata = GcovHandler(options).read_report()

    return covdata


def write_reports(covdata: CovData, options: Options):
    from ..configuration import OutputOrDefault

    Generator = Tuple[
        List[Optional[OutputOrDefault]],
        Callable[[CovData, str], bool],
        Callable[[], None],
    ]
    generators: List[Generator] = []

    if options.clover or options.clover_pretty:
        generators.append(
            (
                [options.clover],
                CloverHandler(options).write_report,
                lambda: LOGGER.warning(
                    "Clover output skipped - "
                    "consider providing an output file with `--clover=OUTPUT`."
                ),
            )
        )

    if options.cobertura or options.cobertura_pretty:
        generators.append(
            (
                [options.cobertura],
                CoberturaHandler(options).write_report,
                lambda: LOGGER.warning(
                    "Cobertura output skipped - "
                    "consider providing an output file with `--cobertura=OUTPUT`."
                ),
            )
        )

    if options.coveralls or options.coveralls_pretty:
        generators.append(
            (
                [options.coveralls],
                CoverallsHandler(options).write_report,
                lambda: LOGGER.warning(
                    "Coveralls output skipped - "
                    "consider providing an output file with `--coveralls=OUTPUT`."
                ),
            )
        )

    if options.csv:
        generators.append(
            (
                [options.csv],
                CsvHandler(options).write_report,
                lambda: LOGGER.warning(
                    "CSV output skipped - "
                    "consider providing an output file with `--csv=OUTPUT`."
                ),
            )
        )

    if options.html or options.html_details or options.html_nested:
        generators.append(
            (
                [options.html, options.html_details, options.html_nested],
                HtmlHandler(options).write_report,
                lambda: LOGGER.warning(
                    "HTML output skipped - "
                    "consider providing an output file with `--html=OUTPUT`."
                ),
            )
        )

    if options.jacoco or options.jacoco_pretty:
        generators.append(
            (
                [options.jacoco],
                JaCoCoHandler(options).write_report,
                lambda: LOGGER.warning(
                    "JaCoCo output skipped - "
                    "consider providing an output file with `--jacoco=OUTPUT`."
                ),
            )
        )

    if options.json or options.json_pretty:
        generators.append(
            (
                [options.json],
                JsonHandler(options).write_report,
                lambda: LOGGER.warning(
                    "JSON output skipped - "
                    "consider providing an output file with `--json=OUTPUT`."
                ),
            )
        )

    if options.json_summary or options.json_summary_pretty:
        generators.append(
            (
                [options.json_summary],
                JsonHandler(options).write_summary_report,
                lambda: LOGGER.warning(
                    "JSON summary output skipped - "
                    "consider providing an output file with `--json-summary=OUTPUT`."
                ),
            )
        )

    if options.lcov:
        generators.append(
            (
                [options.lcov],
                LcovHandler(options).write_report,
                lambda: LOGGER.warning(
                    "LCOV output skipped - "
                    "consider providing an output file with `--lcov=OUTPUT`."
                ),
            )
        )

    if options.sonarqube:
        generators.append(
            (
                [options.sonarqube],
                SonarqubeHandler(options).write_report,
                lambda: LOGGER.warning(
                    "SonarQube output skipped - "
                    "consider providing an output file with `--sonarqube=OUTPUT`."
                ),
            )
        )

    if options.txt:
        generators.append(
            (
                [options.txt],
                TxtHandler(options).write_report,
                lambda: LOGGER.warning(
                    "Text output skipped - "
                    "consider providing an output file with `--txt=OUTPUT`."
                ),
            )
        )

    writer_errors = []
    reports_were_written = False
    default_output_used = False
    default_output = OutputOrDefault(None) if options.output is None else options.output

    for output_choices, format_writer, on_no_output in generators:
        output = OutputOrDefault.choose(output_choices, default=default_output)
        if output is not None and output is default_output:
            default_output_used = True
            if not output.is_dir:
                default_output = None
        if output is not None:
            try:
                format_writer(covdata, output.abspath)
            except RuntimeError as e:
                writer_errors.append(str(e))
            reports_were_written = True
        else:
            on_no_output()

    if not reports_were_written:
        output_path = "-" if default_output is None else default_output.abspath
        default_output = None
        try:
            TxtHandler(options).write_report(covdata, output_path)
        except RuntimeError as e:
            writer_errors.append(str(e))

    if (
        default_output is not None
        and default_output.value is not None
        and not default_output_used
    ):
        LOGGER.warning(
            f"--output={repr(default_output.value)} option was provided but not used."
        )

    if options.txt_summary:
        try:
            TxtHandler(options).write_summary_report(covdata, "-")
        except RuntimeError as e:
            writer_errors.append(str(e))

    if writer_errors:
        errors_as_string = "\n".join(writer_errors)
        raise RuntimeError(
            f"Not all output files where written successful:\n{errors_as_string}"
        )
