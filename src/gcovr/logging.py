# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3, a parsing and reporting tool for gcov.
# https://gcovr.com/en/8.3
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

import logging
import os
import sys
from typing import Any, Optional
from colorlog import ColoredFormatter

from .options import Options

LOGGER = logging.getLogger("gcovr")
DEFAULT_LOGGING_HANDLER = logging.StreamHandler(sys.stderr)

LOG_FORMAT = "(%(levelname)s) %(message)s"
LOG_FORMAT_THREADS = "(%(levelname)s) - %(threadName)s - %(message)s"
COLOR_LOG_FORMAT = f"%(log_color)s{LOG_FORMAT}"
COLOR_LOG_FORMAT_THREADS = f"%(log_color)s{LOG_FORMAT_THREADS}"


def __colored_formatter(options: Optional[Options] = None) -> ColoredFormatter:
    """Configure the colored logging formatter."""
    if options is not None:
        log_format = (
            COLOR_LOG_FORMAT_THREADS if options.gcov_parallel > 1 else COLOR_LOG_FORMAT
        )
        force_color = getattr(options, "force_color", False)
        no_color = getattr(options, "no_color", False)
    else:
        log_format = COLOR_LOG_FORMAT
        force_color = False
        no_color = False

    return ColoredFormatter(
        log_format,
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
        force_color=force_color,
        no_color=no_color,
        stream=sys.stderr,
    )


def configure_logging() -> None:
    """Configure the logging module."""
    DEFAULT_LOGGING_HANDLER.setFormatter(__colored_formatter())
    logging.basicConfig(level=logging.INFO, handlers=[DEFAULT_LOGGING_HANDLER])
    ci_logging_prefixes = None
    if "TF_BUILD" in os.environ:
        ci_logging_prefixes = {
            logging.WARNING: "##vso[task.logissue type=warning]",
            logging.ERROR: "##vso[task.logissue type=error]",
        }
    elif "GITHUB_ACTIONS" in os.environ:
        ci_logging_prefixes = {
            logging.WARNING: "::warning::",
            logging.ERROR: "::error::",
        }

    if ci_logging_prefixes is not None:

        class CiFormatter(logging.Formatter):
            """Formatter to format messages to be captured in Azure"""

            def __init__(self) -> None:
                super().__init__(fmt=LOG_FORMAT)

            def format(self, record: logging.LogRecord) -> str:
                if (
                    ci_logging_prefixes is not None
                    and record.levelno in ci_logging_prefixes
                ):
                    result = (
                        f"{ci_logging_prefixes[record.levelno]}{super().format(record)}"
                    )
                else:
                    result = ""

                return result

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(CiFormatter())
        logging.getLogger().addHandler(handler)

    def exception_hook(exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        logging.exception(
            "Uncaught EXCEPTION", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = exception_hook


def update_logging(options: Options) -> None:
    """Update the logger configuration depending on the options."""
    if options.verbose:
        LOGGER.setLevel(logging.DEBUG)

    # Update the formatter of the default logger depending on options
    DEFAULT_LOGGING_HANDLER.setFormatter(__colored_formatter(options))
