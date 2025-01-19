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
import re
import sys

from argparse import ArgumentError, ArgumentParser, Namespace
from typing import Any, Optional
import traceback

from .configuration import (
    argument_parser_setup,
    config_entries_from_dict,
    merge_options_and_set_defaults,
    parse_config_file,
    parse_config_into_dict,
)
from .coverage import CoverageContainer
from .logging import (
    configure_logging,
    update_logging,
)
from .filter import (
    AlwaysMatchFilter,
    DirectoryPrefixFilter,
)
from .version import __version__

# formats
from . import formats as gcovr_formats

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

LOGGER = logging.getLogger("gcovr")


EXIT_SUCCESS = 0
EXIT_CMDLINE_ERROR = 1
EXIT_LINE_NOK = 2
EXIT_BRANCH_NOK = 4
EXIT_DECISION_NOK = 8
EXIT_FUNCTION_NOK = 16
EXIT_READ_ERROR = 64
EXIT_WRITE_ERROR = 128


#
# Exits with status 2 if below threshold
#
def get_exit_code(
    covdata: CoverageContainer,
    threshold_line: float,
    threshold_branch: float,
    threshold_decision: float,
    threshold_function: float,
) -> int:
    """Fail depending on the coverage result."""
    exit_code = 0

    if (
        threshold_line > 0.0
        or threshold_branch > 0.0
        or threshold_decision > 0.0
        or threshold_function > 0.0
    ):
        stats = covdata.stats

        line_nok = False
        if threshold_line > 0.0:
            # If there are no lines, mark as uncovered
            # (indicates no data at all, likely an error).
            percent_lines = stats.line.percent_or(0.0)

            if percent_lines < threshold_line:
                line_nok = True
                LOGGER.error(
                    f"failed minimum line coverage (got {percent_lines}%, minimum {threshold_line}%)"
                )

        branch_nok = False
        if threshold_branch > 0.0:
            # Allow data with no branches.
            percent_branches = stats.branch.percent_or(100.0)
            if percent_branches < threshold_branch:
                branch_nok = True
                LOGGER.error(
                    f"failed minimum branch coverage (got {percent_branches}%, minimum {threshold_branch}%)"
                )

        decision_nok = False
        if threshold_decision > 0.0:
            # Allow data with no decisions.
            percent_decision = stats.decision.percent_or(100.0)
            if percent_decision < threshold_decision:
                decision_nok = True
                LOGGER.error(
                    f"failed minimum decision coverage (got {percent_decision}%, minimum {threshold_decision}%)"
                )

        function_nok = False
        if threshold_function > 0.0:
            # Allow data with no functions.
            percent_function = stats.function.percent_or(100.0)
            if percent_function < threshold_function:
                function_nok = True
                LOGGER.error(
                    f"failed minimum function coverage (got {percent_function}%, minimum {threshold_function}%)"
                )

        if line_nok:
            exit_code |= EXIT_LINE_NOK
        if branch_nok:
            exit_code |= EXIT_BRANCH_NOK
        if decision_nok:
            exit_code |= EXIT_DECISION_NOK
        if function_nok:
            exit_code |= EXIT_FUNCTION_NOK

    return exit_code


def create_argument_parser() -> ArgumentParser:
    """Create the argument parser."""

    parser = ArgumentParser(add_help=False, exit_on_error=False)
    parser.usage = "gcovr [options] [search_paths...]"
    parser.description = (
        "A utility to run gcov and summarize the coverage in simple reports."
    )

    parser.epilog = "See <http://gcovr.com/> for the full manual."

    options = parser.add_argument_group("Options")
    options.add_argument(
        "-h", "--help", help="Show this help message, then exit.", action="help"
    )
    options.add_argument(
        "--version",
        help="Print the version number, then exit.",
        action="store_true",
        dest="version",
        default=False,
    )

    argument_parser_setup(parser, options)

    return parser


COPYRIGHT = (
    "Copyright (c) 2013-2025 the gcovr authors\n"
    "Copyright (c) 2013 Sandia Corporation.\n"
    "Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,\n"
    "the U.S. Government retains certain rights in this software.\n"
)


def find_config_name(root: str, filename: str) -> Optional[str]:
    """Find the configuration to use."""
    if root:
        filename = os.path.join(root, filename)

    if os.path.isfile(filename):
        return filename

    return None


def load_config(partial_options: Namespace) -> dict[str, Any]:
    """Load a config file if configured or found by default names"""
    filename = getattr(partial_options, "config", None)
    if filename is not None:
        with open(filename, encoding="UTF-8") as buf:
            return parse_config_into_dict(parse_config_file(buf, filename))

    root = getattr(partial_options, "root", "")
    if filename := find_config_name(root, "gcovr.cfg"):
        with open(filename, encoding="UTF-8") as buf:
            return parse_config_into_dict(parse_config_file(buf, filename))

    if filename := find_config_name(root, "gcovr.toml"):
        with open(filename, "rb") as buf:
            data = tomllib.load(buf)
        return parse_config_into_dict(config_entries_from_dict(data, filename))

    if filename := find_config_name(root, "pyproject.toml"):
        with open(filename, "rb") as buf:
            data = tomllib.load(buf)
        if (gcovr_section := data.get("tool", {}).get("gcovr")) is not None:
            return parse_config_into_dict(
                config_entries_from_dict(gcovr_section, filename)
            )

    return {}


def main(args: Optional[list[str]] = None) -> int:  # pylint: disable=too-many-return-statements
    """The main entry point of GCOVR."""
    configure_logging()
    try:
        parser = create_argument_parser()
        cli_options = parser.parse_args(args=args)
    except SystemExit as e:
        if e.code != 0:
            raise AssertionError("Sanity check failed, exitcode must be 0.") from e
        return EXIT_SUCCESS
    except ArgumentError as e:
        sys.stderr.write(f"gcovr: error: {e}\n")
        return EXIT_CMDLINE_ERROR

    if cli_options.version:
        sys.stdout.write(f"gcovr {__version__}\n\n{COPYRIGHT}")
        return EXIT_SUCCESS

    # load the config
    cfg_options = load_config(cli_options)
    options = merge_options_and_set_defaults([cfg_options, cli_options.__dict__])

    # Reconfigure the logging.
    update_logging(options)

    if options.sort_branches and options.sort_key not in [
        "uncovered-number",
        "uncovered-percent",
    ]:
        LOGGER.error(
            "the options --sort-branches without '--sort uncovered-number' or '--sort uncovered-percent' doesn't make sense."
        )
        return EXIT_CMDLINE_ERROR

    if options.html_title == "":
        LOGGER.error("an empty --html-title= is not allowed.")
        return EXIT_CMDLINE_ERROR

    for postfix in ["", "line", "branch"]:
        key_medium = "html_medium_threshold"
        key_high = "html_high_threshold"
        if postfix:
            key_medium += f"_{postfix}"
            key_high += f"_{postfix}"
        option_medium = f"--{key_medium.replace('_', '-')}"
        option_high = f"--{key_high.replace('_', '-')}"

        if getattr(options, key_medium) == 0:
            LOGGER.error(f"value of {option_medium}= should not be zero.")
            return EXIT_CMDLINE_ERROR

        # Inherit the defaults from the global coverage values if not set
        if postfix:
            if getattr(options, key_medium) is None:
                setattr(
                    options,
                    key_medium,
                    options.html_medium_threshold,
                )
                # To get the correct option in the error message below.
                option_medium = "--html-medium-threshold"
            if getattr(options, key_high) is None:
                setattr(
                    options,
                    key_high,
                    options.html_high_threshold,
                )
                # To get the correct option in the error message below.
                option_medium = "--html-high-threshold"

        if getattr(options, key_medium) > getattr(options, key_high):
            LOGGER.error(
                f"value of {option_medium}={getattr(options, key_medium)} should be\n"
                f"lower than or equal to the value of {option_high}={getattr(options, key_high)}."
            )
            return EXIT_CMDLINE_ERROR

    try:
        gcovr_formats.validate_options(options)
    except RuntimeError as exc:
        LOGGER.error(str(exc))
        return EXIT_CMDLINE_ERROR

    options.starting_dir = os.path.abspath(os.getcwd())
    options.root_dir = os.path.abspath(options.root)

    #
    # Setup filters
    #
    try:
        # The root filter isn't technically a filter,
        # but is used to turn absolute paths into relative paths
        options.root_filter = re.compile("^" + re.escape(options.root_dir + os.sep))

        options.filter = [f.build_filter() for f in options.filter]
        if not options.filter:
            options.filter = [DirectoryPrefixFilter(options.root_dir)]
        options.exclude = [f.build_filter() for f in options.exclude]
        options.include = [f.build_filter() for f in options.include]

        options.gcov_filter = [f.build_filter() for f in options.gcov_filter]
        if not options.gcov_filter:
            options.gcov_filter = [AlwaysMatchFilter()]
        options.gcov_exclude = [f.build_filter() for f in options.gcov_exclude]
        if options.gcov_exclude_dirs:
            options.gcov_exclude_dirs = [
                f.build_filter() for f in options.gcov_exclude_dirs
            ]

        options.exclude_functions = [
            (re.compile(f[1:-1] if f[0] == "/" and f[-1] == "/" else re.escape(f)))
            for f in options.exclude_functions
        ]
        # Output the filters for debugging
        for name, filters in [
            ("--root", [options.root_filter]),
            ("--filter", options.filter),
            ("--exclude", options.exclude),
            ("--include", options.include),
            ("--gcov-filter", options.gcov_filter),
            ("--gcov-exclude", options.gcov_exclude),
            ("--gcov-exclude-directories", options.gcov_exclude_dirs),
            ("--exclude-function", options.exclude_functions),
        ]:
            LOGGER.debug(f"Filters for {name}: ({len(filters)})")
            for f in filters:
                LOGGER.debug(f" - {f}")

    except re.error as e:
        LOGGER.error(f"Error setting up filter '{e.pattern!s}': {e}")
        return EXIT_CMDLINE_ERROR

    if options.exclude_lines_by_pattern:
        try:
            re.compile(options.exclude_lines_by_pattern)
        except re.error as e:
            # mypy is thinking that the pattern can be a byte string therefore we need to explicit use !s.
            # See also discussion https://github.com/gcovr/gcovr/pull/1028#discussion_r1855437452
            LOGGER.error(
                "--exclude-lines-by-pattern: "
                f"Invalid regular expression: {options.exclude_lines_by_pattern!s}, error: {e}"
            )
            return EXIT_CMDLINE_ERROR

    if options.exclude_branches_by_pattern:
        try:
            re.compile(options.exclude_branches_by_pattern)
        except re.error as e:
            LOGGER.error(
                "--exclude-branches-by-pattern: "
                f"Invalid regular expression: {repr(options.exclude_branches_by_pattern)}, error: {e}"
            )
            return EXIT_CMDLINE_ERROR

    if options.fail_under_decision > 0.0 and not options.show_decision:
        LOGGER.error("--fail-under-decision need also option --decision.")
        return EXIT_CMDLINE_ERROR

    if options.show_decision:
        LOGGER.info(
            "Attention, the decision analysis is experimental. "
            "It uses a fragile heuristic and depends on the code format."
        )

    LOGGER.info("Reading coverage data...")
    try:
        covdata = gcovr_formats.read_reports(options)
    except Exception:  # pylint: disable=broad-exception-caught
        LOGGER.error(f"Error occurred while reading reports:\n{traceback.format_exc()}")
        return EXIT_READ_ERROR

    LOGGER.info("Writing coverage report...")
    try:
        gcovr_formats.write_reports(covdata, options)
    except Exception:  # pylint: disable=broad-exception-caught
        LOGGER.error(
            f"Error occurred while printing reports:\n{traceback.format_exc()}"
        )
        return EXIT_WRITE_ERROR

    return get_exit_code(
        covdata,
        options.fail_under_line,
        options.fail_under_branch,
        options.fail_under_decision,
        options.fail_under_function,
    )


if __name__ == "__main__":
    sys.exit(main())
