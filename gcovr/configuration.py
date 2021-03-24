# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 5.0, a parsing and reporting tool for gcov.
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

from argparse import ArgumentTypeError, SUPPRESS
from locale import getpreferredencoding
from multiprocessing import cpu_count
from typing import Iterable, Any
import os
import re

from .utils import FilterOption
from .writer.html import CssRenderer


def check_percentage(value):
    r"""
    Check that the percentage is within a reasonable range and if so return it.
    """

    # strip trailing percent sign if present, useful for config files
    if value.endswith('%'):
        value = value[:-1]

    try:
        x = float(value)
        if not (0.0 <= x <= 100.0):
            raise ValueError()
    except ValueError:
        raise ArgumentTypeError(
            "{value} not in range [0.0, 100.0]".format(value=value))
    return x


def check_input_file(value, basedir=None):
    r"""
    Check that the input file is present. Return the full path.
    """
    if basedir is None:
        basedir = os.getcwd()

    if not os.path.isabs(value):
        value = os.path.join(basedir, value)
    value = os.path.normpath(value)

    if not os.path.isfile(value):
        raise ArgumentTypeError(
            "Should be a file that already exists: {value!r}".format(value=value))

    return os.path.abspath(value)


class OutputOrDefault(object):
    """An output path that may be empty.

    - ``None``: the option is not set
    - ``OutputOrDefault(None)``: fall back to some default value
    - ``OutputOrDefault(path)``: use that path
    """

    def __init__(self, value, basedir=None):
        self.value = value
        self._check_output_and_make_abspath(os.getcwd() if basedir is None else basedir)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.value)

    def _check_output_and_make_abspath(self, basedir):
        r"""
        Check if the output file can be created.
        """

        if self.value in (None, '-'):
            self.abspath = '-'
            self.is_dir = False
        else:
            # Replace / and \ with the os path separator.
            value = str(self.value).replace('\\', os.sep).replace('/', os.sep)
            # Save if it is a directory
            self.is_dir = True if value.endswith(os.sep) else False
            value = os.path.normpath(value)
            if self.is_dir:
                value += os.sep

            if not os.path.isabs(value):
                value = os.path.join(basedir, value)
            self.abspath = value

            if self.is_dir:
                # Now mormalize and add the trailing slash after creating the directory.
                if not os.path.isdir(value):
                    try:
                        os.mkdir(value)
                    except OSError as e:
                        raise ArgumentTypeError("Could not create output directory {value!r}: {error}".format(value=self.value, error=e.strerror))
            else:
                try:
                    with open(value, 'w') as _:
                        pass
                except OSError as e:
                    raise ArgumentTypeError("Could not create output file {value!r}: {error}".format(value=self.value, error=e.strerror))
                os.unlink(value)

    @classmethod
    def choose(_cls, choices, default=None):
        """select the first choice that contains a value

        Example: chooses a truthy value over None:
        >>> OutputOrDefault.choose([None, OutputOrDefault(42)])
        OutputOrDefault(42)

        Example: chooses a truthy value over empty value:
        >>> OutputOrDefault.choose([OutputOrDefault(None), OutputOrDefault('x')])
        OutputOrDefault('x')

        Example: chooses default when given empty list
        >>> OutputOrDefault.choose([], default=OutputOrDefault('default'))
        OutputOrDefault('default')

        Example: chooses default when only given falsey values:
        >>> OutputOrDefault.choose(
        ...     [None, OutputOrDefault(None)],
        ...     default=OutputOrDefault('default'))
        OutputOrDefault('default')

        Example: throws when given other value
        >>> OutputOrDefault.choose([True])
        Traceback (most recent call last):
          ...
        TypeError: ...
        """
        for choice in choices:
            if choice is None:
                continue
            if not isinstance(choice, OutputOrDefault):
                raise TypeError(
                    "expected OutputOrDefault instance, got: {}".format(choice))
            if choice.value is not None:
                return choice
        return default


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
            Any command line flags.

    Keyword Arguments:
        action (str, optional):
            What to do when the option is parsed:
            - store (default): store the option argument
            - store_const: store the const value
            - store_true, store_false: shortcuts for store_const
            - append: append the option argument
            (Compare also the *argparse* documentation.)
        choices (list, optional):
            Value must be one of these after conversion.
        config (str or bool, optional):
            Configuration file key.
            If absent, the first ``--flag`` is used without the leading dashes.
            If explicitly set to False,
            the option cannot be set from a config file.
        const (any, optional):
            Assigned by the "store_const" action.
        const_negate (any, optional):
            Generate a "--no-foo" negation flag with the given "const" value.
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
        negate (str, optional):
            Name of the negation if any.
            Autogenerated as "--no-flag" if const_negate is provided.
        positional (bool, optional):
            Whether this is a positional option, defaults to False.
            A positional argument cannot have flags.
        required (bool, optional):
            Whether this option is required, defaults to False.
        type (function, optional):
            Check and convert the option value, may throw exceptions.

    Constraint: an option must be either have a flag or be positional
    or have a config key, or a combination thereof.
    """

    def __init__(
        self, name, flags=None,
        action='store', choices=None, const=None, const_negate=None,
        config=None, default=None, group=None,
        help=None, metavar=None, nargs=None, negate=None, positional=False,
        required=False, type=None,
    ):
        if flags is None:
            flags = []

        assert not (flags and positional), \
            "option cannot have flags and be positional"

        if config is None:
            for flag in flags:
                if not flag.startswith('--'):
                    continue
                config = flag.lstrip('-')
                break
        elif config is False:
            config = None

        assert config is None or isinstance(config, str)

        assert flags or positional or config, \
            "option must be named, positional, or config argument."

        if negate is None and flags and const_negate is not None:
            negate = ['--no-' + f[2:] for f in flags if f.startswith('--')]
            assert negate, "cannot autogenerate negation"

        assert help is not None, "help required"
        if negate:
            help += ' Negation: {}.'.format(', '.join(negate))
        if (flags or positional) and config and '--' + config not in flags:
            help += ' Config key: {config}.'

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

        assert action in ('store', 'store_const', 'append')

        self.name = name
        self.flags = flags

        self.action = action
        self.choices = choices
        self.config = config
        self.const = const
        self.const_negate = const_negate
        self.default = default
        self.group = group
        self.help = None  # assigned later
        self.metavar = metavar
        self.nargs = nargs
        self.negate = negate
        self.positional = positional
        self.required = required
        self.type = type

        # format the help
        self.help = help.format(**self.__dict__)

    def __repr__(self):
        r"""String representation of instance.

        >>> GcovrConfigOption('foo', ['-f', '--foo'], help="fooify")
        GcovrConfigOption('foo', [-f, --foo], ..., help='fooify', ...)
        """
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

            # possibly add a negation flag
            if opt.const_negate is not None:
                kwargs['required'] = False
                kwargs['help'] = SUPPRESS  # don't show separate help entry
                kwargs['const'] = opt.const_negate
                group.add_argument(*opt.negate, **kwargs)

        elif opt.positional:
            group.add_argument(opt.name, **kwargs)


def parse_config_into_dict(config_entry_source, all_options=None):
    # type: (Iterable[ConfigEntry], Iterable[GcovrConfigOption]) -> Any
    cfg_dict = {}

    if all_options is None:
        all_options = GCOVR_CONFIG_OPTIONS

    options_lookup = {}
    for option in all_options:
        if option.config is not None:
            options_lookup[option.config] = option

    for cfg_entry in config_entry_source:  # type: ConfigEntry
        try:
            option = options_lookup[cfg_entry.key]  # type: GcovrConfigOption
        except KeyError:
            raise cfg_entry.error("unknown config option")

        value = _get_value_from_config_entry(cfg_entry, option)
        _assign_value_to_dict(cfg_dict, value, option, is_single_value=True)

    return cfg_dict


def _get_value_from_config_entry(cfg_entry, option):

    def get_boolean(silent_error=False):
        try:
            return cfg_entry.value_as_bool
        except ValueError:
            if silent_error:
                return None
            raise

    # special case: store_const expects a boolean
    if option.action == 'store_const':
        use_const = get_boolean()
    # special case: nargs=? optionally expects a boolean
    elif option.nargs == '?':
        use_const = get_boolean(silent_error=True)
    else:
        use_const = None  # marker to continue with parsing

    if use_const is True:
        return option.const
    if use_const is False:
        return option.default
    assert use_const is None

    # parse the value
    if option.type is bool:
        value = cfg_entry.value_as_bool

    elif option.type is not None:

        value = cfg_entry.value
        args = ()
        if option.type is FilterOption:
            args = [os.path.dirname(cfg_entry.filename)]
        elif option.type is check_input_file:
            value = check_input_file(value, os.path.dirname(cfg_entry.filename))
        elif option.type is OutputOrDefault:
            args = [os.path.dirname(cfg_entry.filename)]

        try:
            value = option.type(value, *args)
        except (ValueError, ArgumentTypeError) as err:
            raise cfg_entry.error(str(err))

    else:
        value = cfg_entry.value

    # verify choices:
    if option.choices is not None:
        if value not in option.choices:
            raise cfg_entry.error(  # pylint: disable=raising-format-tuple
                "must be one of ({}) but got {!r}",
                ', '.join(repr(choice) for choice in option.choices),
                value)

    return value


def _assign_value_to_dict(namespace, value, option, is_single_value):

    if option.action in ('store', 'store_const'):
        namespace[option.name] = value
        return

    if option.action == 'append':
        append_target = namespace.setdefault(option.name, [])
        if is_single_value:
            append_target.append(value)
        else:
            append_target.extend(value)
        return

    assert False, "unexpected action for {name}: {action!r}".format(
        name=option.name, action=option.action)


def merge_options_and_set_defaults(partial_namespaces, all_options=None):
    assert partial_namespaces, "at least one namespace required"

    if all_options is None:
        all_options = GCOVR_CONFIG_OPTIONS

    target = {}
    for namespace in partial_namespaces:
        for option in all_options:

            if option.name not in namespace:
                continue

            _assign_value_to_dict(
                target, namespace[option.name], option, is_single_value=False)

    # if no value was provided, set the default.
    for option in all_options:
        target.setdefault(option.name, option.default)

    return target


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
            "Filter paths use forward slashes, even on Windows. "
            "If the filter looks like an absolute path "
            "it is matched against an absolute path. "
            "Otherwise, the filter is matched against a relative path, "
            "where that path is relative to the current directory "
            "or if defined in a configuration file to the directory of the file.",

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
        "add_tracefile", ["-a", "--add-tracefile"],
        help="Combine the coverage data from JSON files. "
             "Coverage files contains source files structure relative "
             "to root directory. Those structures are combined "
             "in the output relative to the current root directory. "
             "Unix style wildcards can be used to add the pathnames "
             "matching a specified pattern. In this case pattern "
             "must be set in double quotation marks. "
             "Option can be specified multiple times. "
             "When option is used gcov is not run to collect "
             "the new coverage data.",
        action="append",
        default=[],
    ),
    GcovrConfigOption(
        'search_paths', config='search-path',
        positional=True, nargs='*',
        help="Search these directories for coverage files. "
             "Defaults to --root and --object-directory.",
    ),
    GcovrConfigOption(
        'config', ['--config'], config=False,
        help="Load that configuration file. "
             "Defaults to gcovr.cfg in the --root directory.",
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
        "Individual output formats can override this.",
        type=OutputOrDefault,
        default=None,
    ),
    GcovrConfigOption(
        "show_branch", ["-b", "--branches"], config='txt-branch',
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
        "txt", ["--txt"],
        group="output_options",
        metavar='OUTPUT',
        help="Generate a text report. "
             "OUTPUT is optional and defaults to --output.",
        nargs='?',
        type=OutputOrDefault,
        default=None,
        const=OutputOrDefault(None),
    ),
    GcovrConfigOption(
        "xml", ["-x", "--xml"],
        group="output_options",
        metavar='OUTPUT',
        help="Generate a Cobertura XML report. "
             "OUTPUT is optional and defaults to --output.",
        nargs='?',
        type=OutputOrDefault,
        default=None,
        const=OutputOrDefault(None),
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
        metavar='OUTPUT',
        help="Generate a HTML report. "
             "OUTPUT is optional and defaults to --output.",
        nargs='?',
        type=OutputOrDefault,
        default=None,
        const=OutputOrDefault(None),
    ),
    GcovrConfigOption(
        "html_details", ["--html-details"],
        group="output_options",
        metavar="OUTPUT",
        help="Add annotated source code reports to the HTML report. "
             "Implies --html. "
             "OUTPUT is optional and defaults to --output.",
        nargs='?',
        type=OutputOrDefault,
        default=None,
        const=OutputOrDefault(None),
    ),
    GcovrConfigOption(
        "html_details_syntax_highlighting", ["--html-details-syntax-highlighting"],
        group="output_options",
        help="Use syntax highlighting in HTML details page. "
             "Enabled by default.",
        action="store_const",
        default=True,
        const=True,
        const_negate=False,  # autogenerates --no-NAME with action const=False
    ),
    GcovrConfigOption(
        "html_theme", ["--html-theme"],
        group="output_options",
        type=str,
        choices=CssRenderer.get_themes(),
        metavar="THEME",
        help="Override the default color theme for the HTML report. Default is {default!s}.",
        default=CssRenderer.get_default_theme()
    ),
    GcovrConfigOption(
        "html_css", ["--html-css"],
        group="output_options",
        type=check_input_file,
        metavar="CSS",
        help="Override the default style sheet for the HTML report.",
        default=None
    ),
    GcovrConfigOption(
        "html_title", ["--html-title"],
        group="output_options",
        metavar="TITLE",
        help="Use TITLE as title for the HTML report. Default is '{default!s}'.",
        default="GCC Code Coverage Report",
    ),
    GcovrConfigOption(
        "html_medium_threshold", ["--html-medium-threshold"],
        group="output_options",
        type=check_percentage,
        metavar="MEDIUM",
        help="If the coverage is below MEDIUM, the value is marked "
             "as low coverage in the HTML report. "
             "MEDIUM has to be lower than or equal to value of --html-high-threshold "
             "and greater than 0. "
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
        'html_tab_size', ['--html-tab-size'],
        group="output_options",
        help="Used spaces for a tab in a source file. Default is {default!s}",
        type=int,
        default=4,
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
        'html_self_contained', ['--html-self-contained'],
        group="output_options",
        help="Control whether the HTML report bundles resources like CSS styles. "
             "Self-contained reports can be sent via email, "
             "but conflict with the Content Security Policy of some web servers. "
             "Defaults to self-contained reports unless --html-details is used.",
        action='store_const',
        default=None,
        const=True,
        const_negate=False,
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
        "sonarqube", ["--sonarqube"],
        group="output_options",
        metavar='OUTPUT',
        help="Generate sonarqube generic coverage report in this file name. "
             "OUTPUT is optional and defaults to --output.",
        nargs='?',
        type=OutputOrDefault,
        default=None,
        const=OutputOrDefault(None),
    ),
    GcovrConfigOption(
        "json", ["--json"],
        group="output_options",
        metavar='OUTPUT',
        help="Generate a JSON report. "
             "OUTPUT is optional and defaults to --output.",
        nargs='?',
        type=OutputOrDefault,
        default=None,
        const=OutputOrDefault(None),
    ),
    GcovrConfigOption(
        "json_pretty", ["--json-pretty"],
        group="output_options",
        help="Pretty-print the JSON report. Implies --json. Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "json_summary", ["--json-summary"],
        group="output_options",
        metavar='OUTPUT',
        help="Generate a JSON summary report. "
             "OUTPUT is optional and defaults to --output.",
        nargs='?',
        type=OutputOrDefault,
        default=None,
        const=OutputOrDefault(None),
    ),
    GcovrConfigOption(
        "json_summary_pretty", ["--json-summary-pretty"],
        group="output_options",
        help="Pretty-print the JSON SUMMARY report. Implies --json-summary. Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "csv", ["--csv"],
        group="output_options",
        metavar='OUTPUT',
        help="Generate a CSV summary report. "
             "OUTPUT is optional and defaults to --output.",
        nargs='?',
        type=OutputOrDefault,
        default=None,
        const=OutputOrDefault(None),
    ),
    GcovrConfigOption(
        "coveralls", ["--coveralls"],
        group="output_options",
        metavar='OUTPUT',
        help="Generate Coveralls API coverage report in this file name. "
             "OUTPUT is optional and defaults to --output.",
        nargs='?',
        type=OutputOrDefault,
        default=None,
        const=OutputOrDefault(None),
    ),
    GcovrConfigOption(
        "coveralls_pretty", ["--coveralls-pretty"],
        group="output_options",
        help="Pretty-print the coveralls report. Implies --coveralls. Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "filter", ["-f", "--filter"],
        group="filter_options",
        help="Keep only source files that match this filter. "
             "Can be specified multiple times. "
             "Relative filters are relative to the current working directory "
             "or if defined in a configuration file. "
             "If no filters are provided, defaults to --root.",
        action="append",
        type=FilterOption,
        default=[],
    ),
    GcovrConfigOption(
        "exclude", ["-e", "--exclude"],
        group="filter_options",
        help="Exclude source files that match this filter. "
             "Can be specified multiple times.",
        action="append",
        type=FilterOption.NonEmpty,
        default=[],
    ),
    GcovrConfigOption(
        "gcov_filter", ["--gcov-filter"],
        group="filter_options",
        help="Keep only gcov data files that match this filter. "
             "Can be specified multiple times.",
        action="append",
        type=FilterOption,
        default=[],
    ),
    GcovrConfigOption(
        "gcov_exclude", ["--gcov-exclude"],
        group="filter_options",
        help="Exclude gcov data files that match this filter. "
             "Can be specified multiple times.",
        action="append",
        type=FilterOption,
        default=[],
    ),
    GcovrConfigOption(
        "exclude_dirs", ["--exclude-directories"],
        group="filter_options",
        help="Exclude directories that match this regex "
             "while searching raw coverage files. "
             "Can be specified multiple times.",
        action="append",
        type=FilterOption.NonEmpty,
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
        help="Exclude branch coverage from lines without useful source code "
             "(often, compiler-generated \"dead\" code). "
             "Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "exclude_function_lines", ['--exclude-function-lines'],
        group="gcov_options",
        help="Exclude coverage from lines defining a function "
             "Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "exclude_throw_branches", ["--exclude-throw-branches"],
        group="gcov_options",
        help="For branch coverage, exclude branches "
             "that the compiler generates for exception handling. "
             "This often leads to more \"sensible\" coverage reports. "
             "Default: {default!s}.",
        action="store_true"
    ),
    GcovrConfigOption(
        "exclude_lines_by_pattern", ["--exclude-lines-by-pattern"],
        group="gcov_options",
        help="Exclude lines that match this regex.",
        default='.*[GL]COVR?_EXCL_LINE.*',
        type=str
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
        "keep", ["-k", "--keep"], config='keep-gcov-files',
        group="gcov_options",
        help="Keep gcov files after processing. "
             "This applies both to files that were generated by gcovr, "
             "or were supplied via the --use-gcov-files option. "
             "Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "delete", ["-d", "--delete"], config='delete-gcov-files',
        group="gcov_options",
        help="Delete gcda files after processing. Default: {default!s}.",
        action="store_true",
    ),
    GcovrConfigOption(
        "gcov_parallel", ["-j"], config='gcov-parallel',
        group="gcov_options",
        help="Set the number of threads to use in parallel.",
        nargs="?",
        const=cpu_count(),
        type=int,
        default=1,
    )
]


CONFIG_HASH_COMMENT = re.compile(
    r'(?:^|\s+) [#] .* $', re.X)
CONFIG_SEMICOLON_COMMENT = re.compile(
    r'(?:^|\s+) [;] .* $', re.X)
CONFIG_KV = re.compile(
    r'^((?=\w)[\w-]+) \s* = \s* (.*) $', re.X)
CONFIG_POSSIBLE_VARIABLE = re.compile(
    r'[$][\w{(]')  # "$" followed by word, open brace, or open parenthesis.


def parse_config_file(open_file, filename, first_lineno=1):
    r"""
    Parse an ini-style configuration format.

    Yields: ConfigEntry

    Example: basic syntax.

    >>> import io
    >>> cfg = u'''
    ... # this is a comment
    ... key =   value  # trailing comment
    ... # the next line is empty
    ...
    ... key = can have multiple values
    ... another-key =  # can be empty
    ... optional=spaces
    ... '''
    >>> open_file = io.StringIO(cfg[1:])
    >>> for entry in parse_config_file(open_file, 'test.cfg'):
    ...     print(entry)
    test.cfg: 2: key = value
    test.cfg: 5: key = can have multiple values
    test.cfg: 6: another-key = # empty
    test.cfg: 7: optional = spaces
    """

    for lineno, line in enumerate(open_file, first_lineno):
        line = line.rstrip()

        def error(pattern, *args, **kwargs):
            # pylint: disable=cell-var-from-loop
            message = pattern.format(*args, **kwargs)
            message += "\non this line: " + line
            return SyntaxError(': '.join([filename, str(lineno), message]))

        # strip (trailing) comments
        line = CONFIG_HASH_COMMENT.sub('', line)

        if CONFIG_SEMICOLON_COMMENT.search(line):
            raise error("semicolon comment ; ... is reserved")

        if line.isspace() or not line:  # skip empty lines
            continue

        match = CONFIG_KV.match(line)
        if not match:
            raise error('expected "key = value" entry')

        key, value = match.group(1, 2)  # type: str, str
        value = value.strip()

        if value.startswith('"'):
            raise error("leading quote \" is reserved")
        if value.startswith("'"):
            raise error("leading quote \' is reserved")
        if value.endswith('\\'):
            raise error("trailing backslash \\ is reserved")
        if CONFIG_POSSIBLE_VARIABLE.search(value):
            raise error("variable substitution syntax "
                        "(${{var}}, $(var), or $var) is reserved")

        yield ConfigEntry(key, value, filename=filename, lineno=lineno)


class ConfigEntry(object):
    r"""
    A "key = value" config file entry.

    Attributes:
        key (str):
            The key. There might be other entries with the same key.
        value (str):
            The un-parsed value.
        filename (str, optional):
            path of the config file, for error messages.
        lineno (int, optional):
            Line of the entry in the config file, for error messages.
    """
    def __init__(self, key, value, filename=None, lineno=None):
        self.key = key
        self.value = value
        self.filename = filename
        self.lineno = lineno

    def __str__(self):
        r"""
        Display the config entry.

        >>> print(ConfigEntry("the-key", "value",
        ...                   filename="foo.cfg", lineno=17))
        foo.cfg: 17: the-key = value
        """
        return '{filename}: {lineno}: {key} = {value}'.format(
            filename=self.filename or '<config>',
            lineno=self.lineno or '??',
            key=self.key,
            value=self.value or "# empty")

    @property
    def value_as_bool(self):
        r"""
        The value converted to a boolean.

        >>> ConfigEntry("k", "yes").value_as_bool
        True

        >>> ConfigEntry("k", "no").value_as_bool
        False

        >>> ConfigEntry("k", "foo").value_as_bool
        Traceback (most recent call last):
        ValueError: <config>: ??: k: boolean option must be "yes" or "no"
        """
        value = self.value
        if value == 'yes':
            return True
        if value == 'no':
            return False
        raise self.error('boolean option must be "yes" or "no"')

    def error(self, pattern, *args, **kwargs):
        r"""
        Format but NOT RAISE a ValueError.

        >>> entry = ConfigEntry('jobs', 'nun', lineno=3)
        >>> raise entry.error("expected number but got {value!r}")
        Traceback (most recent call last):
        ValueError: <config>: 3: jobs: expected number but got 'nun'
        """
        filename = self.filename or '<config>'
        lineno = str(self.lineno or '??')
        kwargs.update(key=self.key, value=self.value)
        message = pattern.format(*args, **kwargs)
        return ValueError(': '.join([filename, lineno, self.key, message]))
