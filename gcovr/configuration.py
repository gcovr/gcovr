# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 7.0, a parsing and reporting tool for gcov.
# https://gcovr.com/en/stable
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

from __future__ import annotations
from argparse import ArgumentParser, ArgumentTypeError, SUPPRESS
from inspect import isclass
from locale import getpreferredencoding
import logging
from typing import Iterable, Any, List, Optional, Callable, TextIO, Dict
from dataclasses import dataclass
import datetime
import os
import re

from . import formats
from .options import (
    GcovrConfigOption,
    GcovrConfigOptionAction,
    GcovrDeprecatedConfigOptionAction,
    Options,
    OutputOrDefault,
    check_input_file,
    check_percentage,
    relative_path,
)
from .utils import FilterOption

LOGGER = logging.getLogger("gcovr")


def timestamp(value: str) -> datetime.datetime:
    from .timestamps import parse_timestamp  # lazy import

    try:
        return parse_timestamp(value)
    except ValueError as ex:
        raise ArgumentTypeError(f"{ex}: {value!r}") from None


def source_date_epoch() -> Optional[datetime.datetime]:
    """
    Load time from SOURCE_DATE_EPOCH, if it exists.
    See: <https://reproducible-builds.org/docs/source-date-epoch/>

    Examples:
    >>> monkeypatch = getfixture("monkeypatch")
    >>> caplog = getfixture("caplog")

    Example: can be empty
    >>> with monkeypatch.context() as mp:
    ...   mp.delenv("SOURCE_DATE_EPOCH", raising=False)
    ...   print(source_date_epoch())
    None

    Example: can contain timestamp
    >>> with monkeypatch.context() as mp:
    ...   mp.setenv("SOURCE_DATE_EPOCH", "1677067226")
    ...   print(source_date_epoch())
    2023-02-22 12:00:26+00:00

    Example: can contain invalid timestamp
    >>> with monkeypatch.context() as mp:
    ...   mp.setenv("SOURCE_DATE_EPOCH", "not a timestamp")
    ...   print(source_date_epoch())
    None
    >>> for m in caplog.messages: print(m)
    Ignoring invalid environment variable SOURCE_DATE_EPOCH='not a timestamp'
    """

    ts = os.environ.get("SOURCE_DATE_EPOCH")

    if ts:
        try:
            return datetime.datetime.fromtimestamp(int(ts), datetime.timezone.utc)
        except Exception:
            LOGGER.warning(
                "Ignoring invalid environment variable SOURCE_DATE_EPOCH=%r",
                ts,
            )

    return None


def argument_parser_setup(parser: ArgumentParser, default_group):
    r"""Add all options and groups to the given argparse parser."""

    # setup option groups
    groups = {}
    for group_def in GCOVR_CONFIG_OPTION_GROUPS:
        group = parser.add_argument_group(
            group_def["name"],
            description=group_def["description"],
        )
        groups[group_def["key"]] = group

    # create each option value
    for opt in GCOVR_CONFIG_OPTIONS:
        group = default_group if opt.group is None else groups[opt.group]

        kwargs: Dict[str, Any] = {
            "action": opt.action,
            "const": opt.const,
            "default": SUPPRESS,  # default will be assigned manually
            "help": opt.help,
            "metavar": opt.metavar,
        }

        # To avoid store_const problems, optionally set choices, nargs, type:
        if opt.choices is not None:
            kwargs["choices"] = opt.choices
        if opt.nargs is not None:
            kwargs["nargs"] = opt.nargs
        if opt.type is not None:
            kwargs["type"] = opt.type

        # We only want to set dest and required for non-positionals.
        if opt.flags:
            kwargs["dest"] = opt.name
            kwargs["required"] = opt.required  # only meaningful for flags
            group.add_argument(*opt.flags, **kwargs)

            # possibly add a negation flag
            if opt.const_negate is not None:
                kwargs["required"] = False
                kwargs["help"] = SUPPRESS  # don't show separate help entry
                kwargs["const"] = opt.const_negate
                group.add_argument(*opt.negate, **kwargs)

        elif opt.positional:
            group.add_argument(opt.name, **kwargs)


def parse_config_into_dict(
    config_entry_source: Iterable[ConfigEntry],
    all_options: Iterable[GcovrConfigOption] = None,
) -> Dict[str, Any]:
    cfg_dict: Dict[str, Any] = {}

    if all_options is None:
        all_options = GCOVR_CONFIG_OPTIONS

    options_lookup = {}
    for option in all_options:
        if option.config_keys is not None:
            for config_key in option.config_keys:
                options_lookup[config_key] = option

    for cfg_entry in config_entry_source:
        try:
            option: GcovrConfigOption = options_lookup[cfg_entry.key]
        except KeyError:
            raise cfg_entry.error("unknown config option") from None

        value = _get_value_from_config_entry(cfg_entry, option)
        _assign_value_to_dict(
            cfg_dict, value, option, cfg_entry_key=cfg_entry.key, is_single_value=True
        )

    return cfg_dict


def _get_value_from_config_entry(
    cfg_entry: ConfigEntry,
    option: GcovrConfigOption,
) -> Any:
    def get_boolean(silent_error: bool = False):
        try:
            return cfg_entry.value_as_bool
        except ValueError:
            if silent_error:
                return None
            raise

    # special case: store_const expects a boolean
    if option.action == "store_const":
        use_const = get_boolean()
    # special case: nargs=? optionally expects a boolean
    elif option.nargs == "?" and option.choices is None:
        use_const = get_boolean(silent_error=True)
    else:
        use_const = None  # marker to continue with parsing

    if use_const is True:
        return option.const
    if use_const is False:
        return option.default
    assert use_const is None

    # parse the value
    value: object
    if option.type is bool:
        value = cfg_entry.value_as_bool

    elif option.type is not None:
        assert (
            cfg_entry.filename is not None
        ), "conversion function must derive base directory from filename"
        basedir = os.path.dirname(cfg_entry.filename)
        converter = _get_converter_function(option.type, basedir=basedir)

        try:
            value = converter(cfg_entry.value)
        except (ValueError, ArgumentTypeError) as err:
            raise cfg_entry.error(str(err))

    elif option.name == "json_add_tracefile":  # Special case for patterns
        assert (
            cfg_entry.filename is not None
        ), "conversion function must derive base directory from filename"
        basedir = os.path.dirname(cfg_entry.filename)
        value = os.path.join(basedir, cfg_entry.value)
    else:
        value = cfg_entry.value

    # verify choices:
    if option.choices is not None:
        if value not in option.choices:
            raise cfg_entry.error(  # pylint: disable=raising-format-tuple
                "must be one of ({}) but got {!r}",
                ", ".join(repr(choice) for choice in option.choices),
                value,
            )

    return value


def _get_converter_function(
    option_type: Callable[[str], Any],
    *,
    basedir: str,
) -> Callable[[str], Any]:
    """
    Obtain a converter function that corresponds to `option.type`.

    Usually, `option.type` already is that converter function.
    But sometimes, it needs extra arguments that are injected here.
    """

    if isclass(option_type) and issubclass(option_type, FilterOption):
        return lambda value: FilterOption(value, basedir)

    if option_type is check_input_file:
        return lambda value: check_input_file(value, basedir)

    if option_type is relative_path:
        return lambda value: relative_path(value, basedir)

    if option_type is OutputOrDefault:
        return lambda value: OutputOrDefault(value, basedir)

    return option_type


def _assign_value_to_dict(
    namespace: Dict[str, Any],
    value: Any,
    option: GcovrConfigOption,
    is_single_value: bool,
    cfg_entry_key: str = None,
) -> None:
    if option.action == "append" or option.nargs == "*":
        append_target = namespace.setdefault(option.name, [])
        if is_single_value:
            append_target.append(value)
        else:
            append_target.extend(value)
        return

    if option.action in ("store", "store_const"):
        namespace[option.name] = value
        return

    if issubclass(option.action, GcovrConfigOptionAction):
        option.action(option.flags, option.name)(
            None, namespace, value, config=cfg_entry_key
        )
        return

    assert False, f"unexpected action for {option.name}: {option.action!r}"


def merge_options_and_set_defaults(
    partial_namespaces: List[Dict[str, Any]],
    all_options: List[GcovrConfigOption] = None,
) -> Options:
    assert partial_namespaces, "at least one namespace required"

    if all_options is None:
        all_options = GCOVR_CONFIG_OPTIONS

    target: Dict[str, Any] = {}
    for namespace in partial_namespaces:
        for option in all_options:

            if option.name not in namespace:
                continue

            _assign_value_to_dict(
                target, namespace[option.name], option, is_single_value=False
            )

    # if no value was provided, set the default.
    for option in all_options:
        target.setdefault(option.name, option.default)

    return Options(**target)


class UseSortUncoveredNumberAction(GcovrDeprecatedConfigOptionAction):
    option = "--sort-key"
    config = "sort-key"
    value = "uncovered-number"


class UseSortUncoveredPercentAction(GcovrDeprecatedConfigOptionAction):
    option = "--sort-key"
    config = "sort-key"
    value = "uncovered-percent"


GCOVR_CONFIG_OPTION_GROUPS = [
    {
        "key": "output_options",
        "name": "Output Options",
        "description": (
            "Gcovr prints a text report by default, but can switch to XML or HTML."
        ),
    },
    {
        "key": "filter_options",
        "name": "Filter Options",
        "description": (
            "Filters decide which files are included in the report. "
            "Any filter must match, and no exclude filter must match. "
            "A filter is a regular expression that matches a path. "
            "Filter paths use forward slashes, even on Windows. "
            "If the filter looks like an absolute path "
            "it is matched against an absolute path. "
            "Otherwise, the filter is matched against a relative path, "
            "where that path is relative to the current directory "
            "or if defined in a configuration file to the directory of the file."
        ),
    },
    {
        "key": "gcov_options",
        "name": "GCOV Options",
        "description": (
            "The 'gcov' tool turns raw coverage files (.gcda and .gcno) "
            "into .gcov files that are then processed by gcovr. "
            "The gcno files are generated by the compiler. "
            "The gcda files are generated when the instrumented program is "
            "executed."
        ),
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
        "verbose",
        ["-v", "--verbose"],
        help="Print progress messages. Please include this output in bug reports.",
        action="store_true",
    ),
    GcovrConfigOption(
        "root",
        ["-r", "--root"],
        help=(
            "The root directory of your source files. "
            "Defaults to '{default!s}', the current directory. "
            "File names are reported relative to this root. "
            "The --root is the default --filter."
        ),
        default=".",
        type=relative_path,
    ),
    GcovrConfigOption(
        "config",
        ["--config"],
        config=False,
        help=(
            "Load that configuration file. "
            "Defaults to gcovr.cfg in the --root directory."
        ),
        type=relative_path,
    ),
    GcovrConfigOption(
        "respect_exclusion_markers",
        ["--no-markers"],
        help=(
            "Turn off exclusion markers. Any exclusion markers "
            "specified in source files will be ignored."
        ),
        action="store_false",
    ),
    GcovrConfigOption(
        "fail_under_line",
        ["--fail-under-line"],
        type=check_percentage,
        metavar="MIN",
        help=(
            "Exit with a status of 2 "
            "if the total line coverage is less than MIN. "
            "Can be ORed with exit status of '--fail-under-branch', "
            "'--fail-under-decision', and '--fail-under-function' option."
        ),
        default=0.0,
    ),
    GcovrConfigOption(
        "fail_under_branch",
        ["--fail-under-branch"],
        type=check_percentage,
        metavar="MIN",
        help=(
            "Exit with a status of 4 "
            "if the total branch coverage is less than MIN. "
            "Can be ORed with exit status of '--fail-under-line', "
            "'--fail-under-decision', and '--fail-under-function' option."
        ),
        default=0.0,
    ),
    GcovrConfigOption(
        "fail_under_decision",
        ["--fail-under-decision"],
        type=check_percentage,
        metavar="MIN",
        help=(
            "Exit with a status of 8 "
            "if the total decision coverage is less than MIN. "
            "Can be ORed with exit status of '--fail-under-line', "
            "'--fail-under-branch', and '--fail-under-function' option."
        ),
        default=0.0,
    ),
    GcovrConfigOption(
        "fail_under_function",
        ["--fail-under-function"],
        type=check_percentage,
        metavar="MIN",
        help=(
            "Exit with a status of 16 "
            "if the total function coverage is less than MIN. "
            "Can be ORed with exit status of '--fail-under-line', "
            "'--fail-under-branch', and '--fail-under-decision' option."
        ),
        default=0.0,
    ),
    GcovrConfigOption(
        "source_encoding",
        ["--source-encoding"],
        help=(
            "Select the source file encoding. "
            "Defaults to the system default encoding ({default!s})."
        ),
        default=getpreferredencoding(),
    ),
    GcovrConfigOption(
        "output",
        ["-o", "--output"],
        group="output_options",
        help=(
            "Print output to this filename. Defaults to stdout. "
            "Individual output formats can override this."
        ),
        type=OutputOrDefault,
        default=None,
    ),
    GcovrConfigOption(
        "show_decision",
        ["--decisions"],
        group="output_options",
        help="Report the decision coverage. For HTML, JSON, and the summary report.",
        action="store_true",
    ),
    GcovrConfigOption(
        "exclude_calls",
        ["--calls"],
        group="output_options",
        help="Report the calls coverage. For HTML and the summary report.",
        action="store_false",
    ),
    GcovrConfigOption(
        "sort_branches",
        ["--sort-branches"],
        group="output_options",
        help=(
            "Sort entries by branches instead of lines. Can only be used together "
            "with --sort-uncovered or --sort-percent is used."
        ),
        action="store_true",
    ),
    GcovrConfigOption(
        "sort_key",
        ["--sort"],
        config="sort",
        group="output_options",
        help=(
            "Sort entries by filename, number or percent of uncovered lines or branches"
            "(if the option --sort-branches is given). "
            "The default order is increasing and can be changed by --sort-reverse. "
            "The secondary sort key (if values are identical) is always the ascending filename. "
            "For CSV, HTML, JSON, LCOV and text report."
        ),
        choices=["filename", "uncovered-number", "uncovered-percent"],
        default="filename",
    ),
    GcovrConfigOption(
        "sort_key",
        ["-u", "--sort-uncovered"],
        group="output_options",
        help=(
            "Deprecated, please use '--sort-key uncovered-number' instead. "
            "Sort entries by number of uncovered lines or branches (if the option "
            "--sort-branches is given). "
            "The default order is increasing and can be changed by --sort-reverse. "
            "The secondary sort key (if values are identical) is always the ascending filename. "
            "For CSV, HTML, JSON, LCOV and text report."
        ),
        nargs=0,
        action=UseSortUncoveredNumberAction,
    ),
    GcovrConfigOption(
        "sort_key",
        ["-p", "--sort-percentage"],
        group="output_options",
        help=(
            "Deprecated, please use '--sort-key uncovered-percent' instead. "
            "Sort entries by percentage of uncovered lines or branches (if the option "
            "--sort-branches is given). "
            "The default order is increasing and can be changed by --sort-reverse. "
            "The secondary sort key (if values are identical) is always the ascending filename. "
            "For CSV, HTML, JSON, LCOV and text report."
        ),
        nargs=0,
        action=UseSortUncoveredPercentAction,
    ),
    GcovrConfigOption(
        "sort_reverse",
        ["--sort-reverse"],
        config="sort_reverse",
        group="output_options",
        help="Sort entries in reverse order (see --sort).",
        action="store_true",
    ),
    *formats.get_options(),
    GcovrConfigOption(
        "timestamp",
        ["--timestamp"],
        group="output_options",
        help=(
            "Override current time for reproducible reports. "
            "Can use `YYYY-MM-DD hh:mm:ss` or epoch notation. "
            "Used by HTML, Coveralls, and Cobertura reports. "
            "Default is taken from environment variable SOURCE_DATE_EPOCH "
            "(see https://reproducible-builds.org/docs/source-date-epoch) "
            "or current time."
        ),
        type=timestamp,
        default=source_date_epoch() or datetime.datetime.now(),
    ),
    GcovrConfigOption(
        "filter",
        ["-f", "--filter"],
        group="filter_options",
        help=(
            "Keep only source files that match this filter. "
            "Can be specified multiple times. "
            "Relative filters are relative to the current working directory "
            "or if defined in a configuration file. "
            "If no filters are provided, defaults to --root."
        ),
        action="append",
        type=FilterOption,
        default=[],
    ),
    GcovrConfigOption(
        "exclude",
        ["-e", "--exclude"],
        group="filter_options",
        help=(
            "Exclude source files that match this filter. "
            "Can be specified multiple times."
        ),
        action="append",
        type=FilterOption.NonEmpty,
        default=[],
    ),
    GcovrConfigOption(
        "merge_mode_functions",
        ["--merge-mode-functions"],
        metavar="MERGE_MODE",
        group="gcov_options",
        choices=[
            "strict",
            "merge-use-line-0",
            "merge-use-line-min",
            "merge-use-line-max",
            "separate",
        ],
        default="strict",
        help=(
            "The merge mode for functions coverage from different gcov files for same sourcefile."
            "Default is '{default!s}'."
        ),
    ),
    GcovrConfigOption(
        "exclude_internal_functions",
        ["--include-internal-functions"],
        group="gcov_options",
        help=(
            "Include function coverage of compiler internal functions "
            "(starting with '__' or '_GLOBAL__sub_I_')."
        ),
        action="store_false",
    ),
    GcovrConfigOption(
        "exclude_unreachable_branches",
        ["--exclude-unreachable-branches"],
        group="gcov_options",
        help=(
            "Exclude branch coverage from lines without useful source code "
            "(often, compiler-generated 'dead' code)."
        ),
        action="store_true",
    ),
    GcovrConfigOption(
        "exclude_function_lines",
        ["--exclude-function-lines"],
        group="gcov_options",
        help="Exclude coverage from lines defining a function.",
        action="store_true",
    ),
    GcovrConfigOption(
        "exclude_noncode_lines",
        ["--exclude-noncode-lines"],
        config="exclude-noncode-lines",
        group="gcov_options",
        help="Exclude coverage from lines which seem to be non-code.",
        action="store_true",
        const_negate=False,
    ),
    GcovrConfigOption(
        "exclude_throw_branches",
        ["--exclude-throw-branches"],
        group="gcov_options",
        help=(
            "For branch coverage, exclude branches "
            "that the compiler generates for exception handling. "
            "This often leads to more 'sensible' coverage reports."
        ),
        action="store_true",
    ),
    GcovrConfigOption(
        "exclude_lines_by_pattern",
        ["--exclude-lines-by-pattern"],
        help="Exclude lines that match this regex.",
        type=str,
    ),
    GcovrConfigOption(
        "exclude_branches_by_pattern",
        ["--exclude-branches-by-pattern"],
        help="Exclude branches that match this regex.",
        type=str,
    ),
    GcovrConfigOption(
        "exclude_pattern_prefix",
        ["--exclude-pattern-prefix"],
        help=(
            "Define the regex prefix used in markers / line exclusions "
            "(i.e ..._EXCL_START, ..._EXCL_START, ..._EXCL_STOP)"
        ),
        type=str,
        default=r"[GL]COVR?",
    ),
    GcovrConfigOption(
        "search_paths",
        config="search-path",
        positional=True,
        nargs="*",
        help=(
            "Search paths for coverage files. "
            "Defaults to --root and --gcov-object-directory. "
            "If path is a file it is used directly."
        ),
        type=relative_path,
    ),
]


CONFIG_HASH_COMMENT = re.compile(r"(?:^|\s+) [#] .* $", re.X)
CONFIG_SEMICOLON_COMMENT = re.compile(r"(?:^|\s+) [;] .* $", re.X)

# kebab-case word, separated from value (rest of line) by "=" with optional space
CONFIG_KV = re.compile(r"^((?=\w)[\w-]+) \s* = \s* (.*) $", re.X)

# "$" followed by word, open brace, or open parenthesis
CONFIG_POSSIBLE_VARIABLE = re.compile(r"[$][\w{(]")


def parse_config_file(
    open_file: TextIO,
    filename: str,
    first_lineno: int = 1,
) -> Iterable[ConfigEntry]:
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

        def error(pattern: str, *args, **kwargs):
            # pylint: disable=cell-var-from-loop
            message = pattern.format(*args, **kwargs)
            message += "\non this line: " + line
            return SyntaxError(": ".join([filename, str(lineno), message]))

        # strip (trailing) comments
        line = CONFIG_HASH_COMMENT.sub("", line)

        if CONFIG_SEMICOLON_COMMENT.search(line):
            raise error("semicolon comment ; ... is reserved")

        if line.isspace() or not line:  # skip empty lines
            continue

        match = CONFIG_KV.match(line)
        if not match:
            raise error('expected "key = value" entry')

        key: str = match.group(1).strip()
        value: str = match.group(2)

        if value.startswith('"'):
            raise error('leading quote " is reserved')
        if value.startswith("'"):
            raise error("leading quote ' is reserved")
        if value.endswith("\\"):
            raise error("trailing backslash \\ is reserved")
        if CONFIG_POSSIBLE_VARIABLE.search(value):
            raise error(
                "variable substitution syntax ({example}) is reserved",
                example="${var}, $(var), or $var",
            )

        yield ConfigEntry(key, value, filename=filename, lineno=lineno)


@dataclass
class ConfigEntry:
    """A "key = value" config file entry."""

    key: str
    """The key. There might be other entries with the same key."""

    value: str
    """The un-parsed value."""

    filename: Optional[str] = None
    """Path of the config file, for error messages."""

    lineno: Optional[int] = None
    """Line of the entry in the config file, for error messages."""

    def __str__(self):
        r"""
        Display the config entry.

        >>> print(ConfigEntry("the-key", "value",
        ...                   filename="foo.cfg", lineno=17))
        foo.cfg: 17: the-key = value
        """
        filename = self.filename or "<config>"
        lineno = self.lineno or "??"
        key = self.key
        value = self.value or "# empty"
        return f"{filename}: {lineno}: {key} = {value}"

    @property
    def value_as_bool(self) -> bool:
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
        if value == "yes":
            return True
        if value == "no":
            return False
        raise self.error('boolean option must be "yes" or "no"')

    def error(self, pattern: str, *args, **kwargs) -> ValueError:
        r"""
        Format but NOT RAISE a ValueError.

        >>> entry = ConfigEntry('jobs', 'nun', lineno=3)
        >>> raise entry.error("expected number but got {value!r}")
        Traceback (most recent call last):
        ValueError: <config>: 3: jobs: expected number but got 'nun'
        """
        filename = self.filename or "<config>"
        lineno = str(self.lineno or "??")
        kwargs.update(key=self.key, value=self.value)
        message = pattern.format(*args, **kwargs)
        return ValueError(": ".join([filename, lineno, self.key, message]))
