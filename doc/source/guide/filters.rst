.. program is needed to resolve :option: references
.. program:: gcovr

.. _filters:

Using Filters
=============

Gcovr tries to only report coverage for files within your project,
not for your libraries. This is influenced by the following options:

-   :option:`-r`/\ :option:`--root`
-   :option:`-f`/\ :option:`--filter`
-   :option:`-e`/\ :option:`--exclude`
-   :option:`--gcov-filter`
-   :option:`--gcov-exclude`
-   :option:`--gcov-exclude-directories`
-   (the current working directory where gcovr is invoked)

NOTE: Filters can also be specified in the gcovr :ref:`configuration file <configuration>`.

These options take filters.
A filter is a regular expression that matches a file path.
Because filters are regular expressions,
you will have to escape “special” characters with a backslash ``\``.

Always use forward slashes ``/`` as path separators, even on Windows:

-   wrong:   ``--filter C:\project\src\``
-   correct: ``--filter C:/project/src/``

If the filter looks like an absolute path,
it is matched against an absolute path.
Otherwise, the filter is matched against a relative path,
where that path is relative to the current directory
or if defined in a configuration file to the directory of the file.

Examples of relative filters:

-   ``--filter sub-dir/`` matches only that subdirectory

-   ``--filter '\.\./src/'`` matches a sibling directory ``../src``.
    But because a dot ``.`` matches any character in a regex,
    we have to escape it.
    You have to use additional shell escaping.
    This example uses single quotes for Bash or POSIX shell.

-   ``--filter '(.+/)?foo\.c$'`` matches only files called ``foo.c``.
    The regex must match from the start of the relative path,
    so we ignore any leading directory parts with ``(.+/)?``.
    The ``$`` at the end ensures that the path ends here.

If no :option:`-f/--filter <--filter>` is provided,
the :option:`-r/--root <--root>` is turned into a default filter.
Therefore, files outside of the :option:`-r/--root <--root>`
directory are excluded.

To be included in a report, the source file must match any
:option:`-f/--filter <--filter>`,
and must not match any :option:`-e/--exclude <--exclude>` filter.

The :option:`--gcov-filter` and :option:`--gcov-exclude` filters apply to the
``.gcov`` / ``.json.gz`` files created by ``gcov``.
This is useful mostly when running gcov yourself,
and then invoking gcovr with :option:`-g/--gcov-use-existing-files <--gcov-use-existing-files>`.
But these filters also apply when gcov is launched by gcovr.


Speeding up coverage data search
--------------------------------

The :option:`--gcov-exclude-directories` filter is used
while searching for raw coverage data (or for existing ``.gcov`` files when
:option:`-g/--gcov-use-existing-files <--gcov-use-existing-files>` is active).
This filter is matched against directory paths, not file paths.
If a directory matches,
all its contents (files and subdirectories) will be excluded from the search.
For example, consider this build directory::

    build/
    ├─ main.o
    ├─ main.gcda
    ├─ main.gcno
    ├─ a/
    │  ├─ awesome_code.o
    │  ├─ awesome_code.gcda
    │  └─ awesome_code.gcno
    └─ b/
       ├─ better_code.o
       ├─ better_code.gcda
       └─ better_code.gcno

If we run ``gcovr --gcov-exclude-directories 'build/a$'``,
this will exclude anything in the ``build/a`` directory
but will use the coverage data for ``better_code.o`` and ``main.o``.

This can speed up gcovr when you have a complicated build directory structure.
Consider also using the :option:`search_paths`
or :option:`--gcov-object-directory` arguments to specify
where gcovr starts searching. Here you can also specify the ``gcda`` or ``gcov`` file
directly to get the coverage data for a specific file without searching a whole tree.
If you are unsure which directories are being searched,
run gcovr in :option:`-v/--verbose <--verbose>` mode.

For each found coverage data file gcovr will invoke the ``gcov`` tool.
This is typically the slowest part,
and other filters can only be applied *after* this step.
In some cases, parallel execution with the :option:`-j` option
might be helpful to speed up processing.

.. versionadded:: 7.0

   :option:`search_paths` also accept specific files.


Filters for symlinks
--------------------

Gcovr matches filters against *real paths*
that have all their symlinks resolved.
E.g. consider this project layout::

    /home/you/
    ├─ project/  (pwd)
    │  ├─ src/
    │  ├─ relevant-library/ -> ../external-library/
    │  └─ ignore-this/
    └─ external-library/
       └─ src/

.. compare the filter-relative-lib test case

Here, the ``relevant-library``
has the real path ``/home/you/external-library``.

To write a filter that includes both ``src/`` and ``relevant-library/src/``,
we cannot use ``--filter relevant-library/src/``
because that contains a symlink.
Instead, we have to use an absolute path to the real name::

    gcovr --filter src/ --filter /home/you/external-library/src/

or a relative path to the real path::

    gcovr --filter src/ --filter '\.\./external-library/src/'

.. versionadded:: 5.1

   gcovr also supports symlinks/junctions/drive substitutions on Windows.

More examples for filters
-------------------------

Excluding files inside build directory via :option:`--exclude`
with absolute path (Unix only):

.. code-block:: bash

    gcovr --exclude '/.*/build/'

Excluding files inside build directory via :option:`--filter`
with relative path:

.. code-block:: bash

    gcovr --filter '\.\./'
