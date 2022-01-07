.. _configuration:

Configuration Files
===================

.. warning::
    Config files are an experimental feature
    and may be subject to change without prior notice.

Defaults for the command line options can be set in a configuration file.
Example::

    filter = src/
    html-details = yes  # info about each source file
    output = build/coverage.html

How the configuration file is found:
If a :option:`--config<gcovr --config>` option is provided, that file is used.
Otherwise, a ``gcovr.cfg`` file in the :option:`-r/--root<gcovr --root>`
directory is used, if that file exists.

Each line contains a ``key = value`` pair.
Space around the ``=`` is optional.
The value may be empty.
Comments start with a hash ``#`` and ignore the rest of the line,
but cannot start within a word.
Empty lines are also ignored.

The available config keys correspond closely to the command line options,
and are parsed similarly.
In most cases, the name of a long command line option
can be used as a config key.
If not, this is documented in the option's help message.
For example, :option:`--gcov-executable<gcovr --gcov-executable>`
can be set via the ``gcov-executable`` config key.
But :option:`-b/--branches<gcovr --branches>` is set via ``txt-branch``.

Just like command line options,
the config keys can be specified multiple times.
Depending on the option the last one wins or a list will be built.
For example, :option:`-f/--filter<gcovr --filter>` can be provided multiple times::

    # Only show coverage for files in src/, lib/foo, or for main.cpp files.
    filter = src/
    filter = lib/foo/
    filter = *./main\.cpp

Note that relative filters specified in config files will be interpreted
relative to the location of the config file itself.

Option arguments are parsed with the following precedence:

-   First the config file is parsed, if any.
-   Then, all command line arguments are added.
-   Finally, if an option was specified
    neither in a config file nor on the command line,
    its documented default value is used.

Therefore, it doesn't matter
whether a value is provided in the config file or the command line.

Boolean flags are treated specially.
When their config value is “yes” they are enabled,
as if the flag had been provided on the command line.
When their value is “no”, they are explicitly disabled
by assigning their default value.
The :option:`-j<gcovr -j>` flag is special as it takes an optional argument.
In the config file,
``gcov-parallel = yes`` would refer to the no-argument form,
whereas ``gcov-parallel = 4`` would provide an explicit argument.

Some config file syntax is explicitly reserved for future extensions:
Semicolon comments, INI-style sections, multi-line values, quoted values,
variable substitutions, alternative key–value separators, …
