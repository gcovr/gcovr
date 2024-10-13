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

from __future__ import annotations
from argparse import ArgumentTypeError
import argparse
import logging
from typing import Any, List, Optional, Union, Callable
import os

LOGGER = logging.getLogger("gcovr")


def check_percentage(value: str) -> float:
    r"""
    Check that the percentage is within a reasonable range and if so return it.
    """

    # strip trailing percent sign if present, useful for config files
    if value.endswith("%"):
        value = value[:-1]

    try:
        x = float(value)
        if not (0.0 <= x <= 100.0):
            raise ValueError()
    except ValueError:
        raise ArgumentTypeError(f"{value} not in range [0.0, 100.0]") from None
    return x


def check_input_file(value: str, basedir: str = None) -> str:
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
            f"Should be a file that already exists: {value!r}"
        ) from None

    return os.path.abspath(value)


def relative_path(value: str, basedir: str = None) -> str:
    r"""
    Make a absolute path if value is a relative path.
    """
    if not value:
        raise ArgumentTypeError("Should not be set to an empty string.") from None

    if basedir is None:
        basedir = os.getcwd()

    if not os.path.isabs(value):
        value = os.path.join(basedir, value)
    value = os.path.normpath(value)
    return os.path.relpath(value, os.getcwd())


class OutputOrDefault:
    """An output path that may be empty.

    - ``None``: the option is not set
    - ``OutputOrDefault(None)``: fall back to some default value
    - ``OutputOrDefault(path)``: use that path
    """

    def __init__(self, value: Optional[str], basedir: str = None) -> None:
        self.value = value
        self._check_output_and_make_abspath(os.getcwd() if basedir is None else basedir)

    def __repr__(self):
        name = self.__class__.__name__
        value = self.value
        return f"{name}({value!r})"

    def _check_output_and_make_abspath(self, basedir: str) -> None:
        r"""
        Check if the output file can be created.
        """

        if self.value in (None, "-"):
            self.abspath = "-"
            self.is_dir = False
        else:
            # Replace / and \ with the os path separator.
            value = str(self.value).replace("\\", os.sep).replace("/", os.sep)
            # Save if it is a directory
            self.is_dir = value.endswith(os.sep)
            value = os.path.normpath(value)
            if self.is_dir:
                value += os.sep

            if not os.path.isabs(value):
                value = os.path.join(basedir, value)
            self.abspath = value

            if self.is_dir:
                # Now normalize and add the trailing slash after creating the directory.
                if not os.path.isdir(value):
                    try:
                        os.mkdir(value)
                    except OSError as e:
                        raise ArgumentTypeError(
                            f"Could not create output directory {self.value!r}: {e.strerror}"
                        ) from None
            else:
                try:
                    with open(value, "w", encoding="utf-8") as _:
                        pass
                except OSError as e:
                    raise ArgumentTypeError(
                        f"Could not create output file {self.value!r}: {e.strerror}"
                    ) from None
                os.unlink(value)

    @classmethod
    def choose(
        cls,
        choices: List[Optional[OutputOrDefault]],
        default: Optional[OutputOrDefault] = None,
    ) -> Optional[OutputOrDefault]:
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

        Example: chooses default when only given false values:
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
                raise TypeError(f"expected OutputOrDefault instance, got: {choice}")
            if choice.value is not None:
                return choice
        return default


class Options(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get(self, name: str) -> Any:
        """Function to get an option by name."""
        return self.__dict__.get(name)


class GcovrConfigOptionAction(argparse.Action):
    pass


class GcovrDeprecatedConfigOptionAction(GcovrConfigOptionAction):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None, config=None):
        if option_string is not None:
            LOGGER.warning(
                f"Deprecated option {option_string} used, please use '{self.option} {self.value}' instead."
            )
        if config is not None:
            LOGGER.warning(
                f"Deprecated config key {config} used, please use '{self.config}={self.value}' instead."
            )
        # This part is used when merging configurations
        if isinstance(namespace, dict):
            namespace[self.dest] = values
        # We are called from argparse
        else:
            setattr(namespace, self.dest, self.value)


class GcovrConfigOption:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-few-public-methods
    # pylint: disable=redefined-builtin
    r"""
    Represents a single setting for a gcovr runtime parameter.

    Gcovr can be extensively configured through a series of options,
    representing these options as a simple class object allows them to be
    portability re-used in multiple configuration schemes. This is implemented
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
        self,
        name: str,
        flags: Optional[List[str]] = None,
        *,
        help: str,
        action: str = "store",
        choices: list = None,
        const: Any = None,
        const_negate: Any = None,
        config: Union[str, bool] = True,
        default: Any = None,
        group: str = None,
        metavar: str = None,
        nargs: Union[int, str] = None,
        positional: bool = False,
        required: bool = False,
        type: Callable[[str], Any] = None,
    ) -> None:
        if flags is None:
            flags = []

        if flags and positional:
            raise AssertionError("Option cannot have flags and be positional")

        config_keys = _derive_configuration_key(config, flags=flags)
        del config

        if not (flags or positional or config_keys):
            raise AssertionError(
                "Option must be named, positional, or config argument."
            )

        negate: List[str] = []
        if flags and const_negate is not None:
            negate = ["--no-" + f[2:] for f in flags if f.startswith("--")]
            if not negate:
                raise AssertionError("Cannot autogenerate negation")

        if not help:
            raise AssertionError("help required")
        if negate:
            help += " Negation: {}.".format(", ".join(negate))
        if (flags or positional) and config_keys:
            config_keys_help = []
            for config_key in config_keys:
                config_keys_help.append(config_key)
            help += f" Config key(s): {', '.join(config_keys_help)}."

        # the store_true and store_false actions have hardcoded boolean
        # constants in their definitions so they need switched to the generic
        # store_const in order for the logic here to work correctly.
        if action == "store_true":
            if const is not None:
                raise AssertionError("action=store_true and const conflict")
            if default is not None:
                raise AssertionError("action=store_true and default conflict")
            action = "store_const"
            const = True
            default = False
        elif action == "store_false":
            if const is not None:
                raise AssertionError("action=store_false and const conflict")
            if default is not None:
                raise AssertionError("action=store_false and default conflict")
            action = "store_const"
            const = False
            default = True

        if not (
            action in ("store", "store_const", "append")
            or issubclass(action, GcovrConfigOptionAction)
        ):
            raise AssertionError(f"Unknown action {action!r}")

        self.name = name
        self.flags = flags

        self.action = action
        self.choices = choices
        self.config_keys = config_keys
        self.const = const
        self.const_negate = const_negate
        self.default = default
        self.group = group
        self.help = ""  # assigned later
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

        >>> GcovrConfigOption('foo', ['-f', '--foo'], help="foo text.")
        GcovrConfigOption('foo', [-f, --foo], ..., help='foo text. Config key(s): foo.', ...)
        """
        name = self.name
        flags = ", ".join(self.flags)
        kwargs = ", ".join(
            f"{k}={v!r}"
            for k, v in sorted(self.__dict__.items())
            if k not in ("name", "flags")
        )

        return f"GcovrConfigOption({name!r}, [{flags}], {kwargs})"


def _derive_configuration_key(
    config: Union[str, bool],
    *,
    flags: List[str],
) -> Optional[List[str]]:
    if config is True:
        config_keys = []
        for flag in flags:
            if flag.startswith("--"):
                config_keys.append(flag.lstrip("-"))
        if not config_keys:
            raise AssertionError("Could not autogenerate config key from {flags!r}.")
        return config_keys
    elif config is False:
        return None
    elif isinstance(config, str):
        return [config]

    raise AssertionError(
        f"Oops, sanity check failed: Unexpected config entry type {config!r}"
    )
