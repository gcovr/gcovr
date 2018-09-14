# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# This module manages processing and validation of the configuration options
# passed into gcovr.
#
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.
from argparse import ArgumentTypeError, SUPPRESS
from locale import getpreferredencoding
from multiprocessing import cpu_count
import os


def check_percentage(value):
    r"""
    Check that the percentage is within a reasonable range and if so return it.
    """
    try:
        x = float(value)
        if not (0.0 <= x <= 100.0):
            raise ValueError()
    except ValueError:
        raise ArgumentTypeError(
            "{value} not in range [0.0, 100.0]".format(value=value))
    return x


def check_non_empty(value):
    if not value:
        raise ArgumentTypeError("value should not be empty")
    return value


class GcovrConfigOption(object):
    r"""
    Represents a single setting for a gcovr runtime parameter.

    Gcovr can be extensively configured through a series of options,
    representing these options as a simple class object allows them to be
    portabilty re-used in multiple configuration schemes. This is implemented
    in a way similar to how options are defined in argparse. The converter
    keyword argument is expected to return a valid conversion of a string
    value or throw an error.

    Arguments:
        name (str):
            Destination (options object field),
            must be valid Python identifier.
        flags (list of str, optional):
            Any command line flags. If empty, the option is positional.

    Keyword Arguments:
        action (str, optional):
            What to do when the option is parsed.
            See the available *argparse* actions. In particular:
            - store (default): store the option argument
            - store_const: store the const value
            - store_true, store_false: shortcuts for store_const
            - append: append the option argument
        choices (list):
            Value must be one of these after conversion.
        const (any, optional):
            Assigned by the "store_const" action.
        default (any, optional):
            Default value if the option is not found, defaults to None.
        group (str, optional):
            Name of the option group in GCOVR_CONFIG_OPTION_GROUPS.
            Only relevant for documentation purposes.
        help (str):
            Help message.
            Must display well on terminal *and* render as Restructured Text.
            Any named curly-brace placeholders
            are filled in from the option attributes via ``str.format()``.
        metavar (str, optional):
            Name of the value in help messages, defaults to the name.
        nargs (int or '+', '*', '?', optional):
            How often the option may occur.
            Special case for "?": if the option exists but has no value,
            the const value is stored.
        required (bool, optional):
            Whether this option is required, defaults to False.
        type (function, optional):
            Check and convert the option value, may throw exceptions.
    """

    def __init__(
        self, name, flags=None,
        action='store', choices=None, const=None, default=None, group=None,
        help=None, metavar=None, nargs=None, required=False, type=None,
    ):
        if flags is None:
            flags = []

        assert help is not None, "help required"

        # the store_true and store_false actions have hardcoded boolean
        # constants in their definitions so they need switched to the generic
        # store_const in order for the logic here to work correctly.
        if action == 'store_true':
            assert const is None, "action=store_true and const conflict"
            assert default is None, "action=store_true and default conflict"
            action = 'store_const'
            const = True
            default = False
        elif action == 'store_false':
            assert const is None, "action=store_false and const conflict"
            assert default is None, "action=store_false and default conflict"
            action = 'store_const'
            const = False
            default = True

        self.name = name
        self.flags = flags

        self.action = action
        self.choices = choices
        self.const = const
        self.default = default
        self.group = group
        self.help = None  # assigned later
        self.metavar = metavar
        self.nargs = nargs
        self.required = required
        self.type = type

        # format the help
        self.help = help.format(**self.__dict__)

    def __repr__(self):
        r"""String representation of instance."""

        kwargs = [
            '{k}={v!r}'.format(k=k, v=v)
            for k, v in sorted(self.__dict__.items())
            if k not in ('name', 'flags')]

        return "GcovrConfigOption({name!r}, [{flags}], {kwargs})".format(
            name=self.name,
            flags=', '.join(self.flags),
            kwargs=', '.join(kwargs),
        )


def argument_parser_setup(parser, default_group):
    r"""Add all options and groups to the given argparse parser."""

    # setup option groups
    groups = {}
    for group_def in GCOVR_CONFIG_OPTION_GROUPS:
        group = parser.add_argument_group(group_def["name"],
                                          description=group_def["description"])
        groups[group_def["key"]] = group

    # create each option value
    for opt in GCOVR_CONFIG_OPTIONS:
        group = default_group if opt.group is None else groups[opt.group]

        kwargs = {
            'action': opt.action,
            'const': opt.const,
            'default': SUPPRESS,  # default will be assigned manually
            'help': opt.help,
            'metavar': opt.metavar,
        }

        # To avoid store_const problems, optionally set choices, nargs, type:
        if opt.choices is not None:
            kwargs['choices'] = opt.choices
        if opt.nargs is not None:
            kwargs['nargs'] = opt.nargs
        if opt.type is not None:
            kwargs['type'] = opt.type

        # We only want to set dest and required for non-positionals.
        if opt.flags:
            kwargs["dest"] = opt.name
            kwargs["required"] = opt.required  # only meaningful for flags
            group.add_argument(*opt.flags, **kwargs)
        else:
            group.add_argument(opt.name, **kwargs)


GCOVR_CONFIG_OPTION_GROUPS = [
    {
        "key": "output_options",
        "name": "Output Options",
        "description":
            "Gcovr prints a text report by default, "
            "but can switch to XML or HTML.",
    }, {
        "key": "filter_options",
        "name": "Filter Options",
        "description":
            "Filters decide which files are included in the report. "
            "Any filter must match, and no exclude filter must match. "
            "A filter is a regular expression that matches a path. "
            "Filter paths use forward slashes, even on Windows.",
    }, {
        "key": "gcov_options",
        "name": "GCOV Options",
        "description":
            "The 'gcov' tool turns raw coverage files (.gcda and .gcno) "
            "into .gcov files that are then processed by gcovr. "
            "The gcno files are generated by the compiler. "
            "The gcda files are generated when the instrumented program is "
            "executed.",
    },
]


# Style guide for option descriptions:
# - Prefer complete sentences.
# - Phrase first sentence as a command:
#   “Print report”, not “Prints report”.
# - Must be readable on the command line,
#   AND parse as reStructured Text.

GCOVR_CONFIG_OPTIONS = [
    GcovrConfigOption(
        "verbose", ["-v", "--verbose"],
        help="Print progress messages. "
             "Please include this output in bug reports.",
        action="store_true",
    ),
    GcovrConfigOption(
        "root", ["-r", "--root"],
        help="The root directory of your source files. "
             "Defaults to '{default!s}', the current directory. "
             "File names are reported relative to this root. "
             "The --root is the default --filter.",
        default='.',
    ),
    GcovrConfigOption(
        'search_paths',
        help="Search these directories for coverage files. "
             "Defaults to --root and --object-directory.",
        nargs='*',
    ),
    GcovrConfigOption(
        "fail_under_line", ["--fail-under-line"],
        type=check_percentage,
        metavar="MIN",
        help="Exit with a status of 2 "
             "if the total line coverage is less than MIN. "
             "Can be ORed with exit status of '--fail-under-branch' option.",
        default=0.0,
    ),
    GcovrConfigOption(
        "fail_under_branch", ["--fail-under-branch"],
        type=check_percentage,
        metavar="MIN",
        help="Exit with a status of 4 "
             "if the total branch coverage is less than MIN. "
             "Can be ORed with exit status of '--fail-under-line' option.",
        default=0.0,
    ),
    GcovrConfigOption(
        'source_encoding', ['--source-encoding'],
        help="Select the source file encoding. "
             "Defaults to the system default encoding ({default!s}).",
        default=getpreferredencoding(),
    ),
    GcovrConfigOption(
        "output", ["-o", "--output"],
        group="output_options",
        help="Print output to this filename. Defaults to stdout. "
             "Required for --html-details.",
        default=None,
    ),
    GcovrConfigOption(
        "show_branch", ["-b", "--branches"],
        group="output_options",
        help="Report the branch coverage instead of the line coverage. "
             "For text report only.",
        action="store_true",
    ),
    GcovrConfigOption(
        "sort_uncovered", ["-u", "--sort-uncovered"],
        group="output_options",
        help="Sort entries by increasing number of uncovered lines. "
             "For text and HTML report.",
        action="store_true",
    ),
    GcovrConfigOption(
        "sort_percent", ["-p", "--sort-percentage"],
        group="output_options",
        help="Sort entries by increasing percentage of uncovered lines. "
             "For text and HTML report.",
        action="store_true",
    ),
    GcovrConfigOption(
        "xml", ["-x", "--xml"],
        group="output_options",
        help="Generate a Cobertura XML report.",
        action="store_true",
    ),
    GcovrConfigOption(
        "prettyxml", ["--xml-pretty"],
        group="output_options",
        help="Pretty-print the XML report. Implies --xml. Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "html", ["--html"],
        group="output_options",
        help="Generate a HTML report.",
        action="store_true",
    ),
    GcovrConfigOption(
        "html_details", ["--html-details"],
        group="output_options",
        help="Add annotated source code reports to the HTML report. "
             "Requires --output as a basename for the reports. "
             "Implies --html.",
        action="store_true",
    ),
    GcovrConfigOption(
        "html_title", ["--html-title"],
        group="output_options",
        metavar="TITLE",
        help="Use TITLE as title for the HTML report. Default is {default!s}.",
        default="Head",
    ),
    GcovrConfigOption(
        "html_medium_threshold", ["--html-medium-threshold"],
        group="output_options",
        type=check_percentage,
        metavar="MEDIUM",
        help="If the coverage is below MEDIUM, the value is marked "
             "as low coverage in the HTML report. "
             "MEDIUM has to be lower than or equal to value of --html-high-threshold. "
             "If MEDIUM is equal to value of --html-high-threshold the report has "
             "only high and low coverage. Default is {default!s}.",
        default=75.0,
    ),
    GcovrConfigOption(
        "html_high_threshold", ["--html-high-threshold"],
        group="output_options",
        type=check_percentage,
        metavar="HIGH",
        help="If the coverage is below HIGH, the value is marked "
             "as medium coverage in the HTML report. "
             "HIGH has to be greater than or equal to value of --html-medium-threshold. "
             "If HIGH is equal to value of --html-medium-threshold the report has "
             "only high and low coverage. Default is {default!s}.",
        default=90.0,
    ),
    GcovrConfigOption(
        "relative_anchors", ["--html-absolute-paths"],
        group="output_options",
        help="Use absolute paths to link the --html-details reports. "
             "Defaults to relative links.",
        action="store_false",
    ),
    GcovrConfigOption(
        'html_encoding', ['--html-encoding'],
        group="output_options",
        help="Override the declared HTML report encoding. "
             "Defaults to {default!s}. "
             "See also --source-encoding.",
        default='UTF-8',
    ),
    GcovrConfigOption(
        "print_summary", ["-s", "--print-summary"],
        group="output_options",
        help="Print a small report to stdout "
             "with line & branch percentage coverage. "
             "This is in addition to other reports. "
             "Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "filter", ["-f", "--filter"],
        group="filter_options",
        help="Keep only source files that match this filter. "
             "Can be specified multiple times. "
             "If no filters are provided, defaults to --root.",
        action="append",
        default=[],
    ),
    GcovrConfigOption(
        "exclude", ["-e", "--exclude"],
        group="filter_options",
        help="Exclude source files that match this filter. "
             "Can be specified multiple times.",
        action="append",
        type=check_non_empty,
        default=[],
    ),
    GcovrConfigOption(
        "gcov_filter", ["--gcov-filter"],
        group="filter_options",
        help="Keep only gcov data files that match this filter. "
             "Can be specified multiple times.",
        action="append",
        default=[],
    ),
    GcovrConfigOption(
        "gcov_exclude", ["--gcov-exclude"],
        group="filter_options",
        help="Exclude gcov data files that match this filter. "
             "Can be specified multiple times.",
        action="append",
        default=[],
    ),
    GcovrConfigOption(
        "exclude_dirs", ["--exclude-directories"],
        group="filter_options",
        help="Exclude directories that match this regex "
             "while searching raw coverage files. "
             "Can be specified multiple times.",
        action="append",
        type=check_non_empty,
        default=[],
    ),
    GcovrConfigOption(
        "gcov_cmd", ["--gcov-executable"],
        group="gcov_options",
        help="Use a particular gcov executable. "
             "Must match the compiler you are using, "
             "e.g. 'llvm-cov gcov' for Clang. "
             "Can include additional arguments. "
             "Defaults to the GCOV environment variable, "
             "or 'gcov': '{default!s}'.",
        default=os.environ.get('GCOV', 'gcov'),
    ),
    GcovrConfigOption(
        "exclude_unreachable_branches", ["--exclude-unreachable-branches"],
        group="gcov_options",
        help="Exclude branch coverage with LCOV/GCOV exclude markers. "
             "Additionally, exclude branch coverage from lines "
             "without useful source code "
             "(often, compiler-generated \"dead\" code). "
             "Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "gcov_files", ["-g", "--use-gcov-files"],
        group="gcov_options",
        help="Use existing gcov files for analysis. Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "gcov_ignore_parse_errors", ['--gcov-ignore-parse-errors'],
        group="gcov_options",
        help="Skip lines with parse errors in GCOV files "
             "instead of exiting with an error. "
             "A report will be shown on stderr. "
             "Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "objdir", ['--object-directory'],
        group="gcov_options",
        help="Override normal working directory detection. "
             "Gcovr needs to identify the path between gcda files "
             "and the directory where the compiler was originally run. "
             "Normally, gcovr can guess correctly. "
             "This option specifies either "
             "the path from gcc to the gcda file (i.e. gcc's '-o' option), "
             "or the path from the gcda file to gcc's working directory.",
    ),
    GcovrConfigOption(
        "keep", ["-k", "--keep"],
        group="gcov_options",
        help="Keep gcov files after processing. "
             "This applies both to files that were generated by gcovr, "
             "or were supplied via the --use-gcov-files option. "
             "Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "delete", ["-d", "--delete"],
        group="gcov_options",
        help="Delete gcda files after processing. Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "gcov_parallel", ["-j"],
        group="gcov_options",
        help="Set the number of threads to use in parallel.",
        nargs="?",
        const=cpu_count(),
        type=int,
        default=1,
    )
]
