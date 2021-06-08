Gcovr User Guide
================

.. github display

    This file does not render correctly on GitHub.
    Please view the user guide for the latest gcovr release at
    http://gcovr.com/guide.html

.. include:: ../../README.rst
    :start-after: .. begin abstract
    :end-before: .. end abstract

The `Gcovr Home Page <http://gcovr.com>`__ is
`<http://gcovr.com>`__.
Automated test results are available through
`GitHub Actions <https://github.com/gcovr/gcovr/actions?query=branch:master>`.
Gcovr is available under the
`BSD <http://www.gnu.org/licenses/bsd.html>`__ license.

This documentation describes Gcovr |release|.

This User Guide provides the following sections:

.. contents::
    :local:
    :depth: 2

Related documents:

- :doc:`installation`
- :doc:`contributing` (includes instructions for bug reports)
- :doc:`cookbook`
- :doc:`faq`
- :doc:`changelog`
- :doc:`license`

Getting Started
---------------

The ``gcovr`` command provides a summary of the lines that have been
executed in a program.  Code coverage statistics help you discover
untested parts of a program, which is particularly important when
assessing code quality.  Well-tested code is a characteristic of
high quality code, and software developers often assess code coverage
statistics when deciding if software is ready for a release.

The ``gcovr`` command can be used to analyze programs compiled with
GCC.   The following sections illustrate the application of ``gcovr``
to test coverage of the following program:

.. include:: ../examples/example.cpp
    :code: cpp
    :number-lines: 1

This code executes several subroutines in this program,
but some lines in the program are not executed.

Tabular Output of Code Coverage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We compile ``example1.cpp`` with the GCC compiler as follows:

.. include:: ../examples/example.sh
    :code: bash
    :start-after: #BEGIN compile
    :end-before: #END compile

(If you are using CMake,
also see :ref:`oos cmake`.)

Note that we compile this program without optimization, because
optimization may combine lines of code and otherwise change the
flow of execution in the program.  Additionally, we compile with
the ``-fprofile-arcs -ftest-coverage -fPIC`` compiler options, which
add logic to generate output files that can be processed by the
``gcov`` command.

The compiler generates the ``program`` executable.  When we execute this command:

.. include:: ../examples/example.sh
    :code: bash
    :start-after: #BEGIN run
    :end-before: #END run

the files ``example1.gcno`` and ``example1.gcda`` are generated.  These
files are processed by ``gcov`` to generate code coverage statistics.
The ``gcovr`` command calls ``gcov`` and summarizes these
code coverage statistics in various formats.  For example:

.. include:: ../examples/example.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

generates a text summary of the lines executed:

.. include:: ../examples/example.txt
    :literal:

The same result can be achieved when explicit :option:`--txt<gcovr --txt>`
option is set. For example::

    gcovr -r . --txt

generates the same text summary.

Each line of this output includes a summary for a given source file,
including the number of lines instrumented, the number of lines
executed, the percentage of lines executed, and a summary of the
line numbers that were not executed.  To improve clarity, gcovr
uses an aggressive approach to grouping uncovered lines and will
combine uncovered lines separated by "non-code" lines (blank,
freestanding braces, and single-line comments) into a single region.
As a result, the number of lines listed in the "Missing" list may
be greater than the difference of the "Lines" and "Exec" columns.

The :option:`-r/--root<gcovr --root>` option specifies the root directory
for the files that are being analyzed.  This allows ``gcovr`` to generate
a simpler report (without absolute path names), and it allows system header files
to be excluded from the analysis.

Note that ``gcov`` accumulates statistics by line.  Consequently, it
works best with a programming style that places only one statement
on each line.

..
    In ``example.cpp``, the ``MACRO`` macro executes a
    branch, but ``gcov`` cannot discern which branch is executed.


Tabular Output of Branch Coverage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``gcovr`` command can also summarize branch coverage using
the :option:`-b/--branches<gcovr --branches>` option:

.. include:: ../examples/example_branches.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates a tabular output that summarizes the number of branches, the number of
branches taken and the branches that were not completely covered:

.. include:: ../examples/example_branches.txt
    :literal:

The same result can be achieved when explicit :option:`--txt<gcovr --txt>`
option is set. For example::

    gcovr -r . --branches --txt

print the same tabular output.

.. versionadded:: 5.0
   Added :option:`--txt<gcovr --txt>`.


Cobertura XML Output
~~~~~~~~~~~~~~~~~~~~

The default output format for ``gcovr`` is to generate a tabular
summary in plain text.  The ``gcovr`` command can also generate an
XML output using the :option:`-x/--xml<gcovr --xml>`
and :option:`--xml-pretty<gcovr --xml-pretty>` options:

.. include:: ../examples/example_xml.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an XML summary of the lines executed:

.. include:: ../examples/example_xml.xml
    :code: xml

This XML format is in the
`Cobertura XML <http://cobertura.sourceforge.net/xml/coverage-04.dtd>`__
format suitable for import and display within the
`Jenkins <http://www.jenkins-ci.org/>`__ and `Hudson <http://www.hudson-ci.org/>`__
continuous integration servers using the
`Cobertura Plugin <https://wiki.jenkins-ci.org/display/JENKINS/Cobertura+Plugin>`__.
Gcovr also supports a `Sonarqube XML Output`_

The :option:`-x/--xml<gcovr --xml>` option generates a denser XML output, and the
:option:`--xml-pretty<gcovr --xml-pretty>` option generates an indented
XML output that is easier to read. Note that the XML output contains more
information than the tabular summary.  The tabular summary shows the percentage
of covered lines, while the XML output includes branch statistics and the number
of times that each line was covered.  Consequently, XML output can be
used to support performance optimization in the same manner that
``gcov`` does.


HTML Output
~~~~~~~~~~~

The ``gcovr`` command can also generate a simple
HTML output using the :option:`--html<gcovr --html>` option:

.. include:: ../examples/example_html.sh
    :code: bash
    :start-after: #BEGIN gcovr html
    :end-before: #END gcovr html

This generates a HTML summary of the lines executed.  In this
example, the file ``example1.html`` is generated, which has the
following output:

.. image:: ../images/screenshot-html.png
    :align: center

The default behavior of the :option:`--html<gcovr --html>` option is to generate
HTML for a single webpage that summarizes the coverage for all files.  The
HTML is printed to standard output, but the :option:`-o/--output<gcovr --output>`
option is used to specify a file that stores the HTML output.

The :option:`--html-details<gcovr --html-details>` option is used to create
a separate web page for each file.  Each of these web pages includes
the contents of file with annotations that summarize code coverage.  Consider
the following command:

.. include:: ../examples/example_html.sh
    :code: bash
    :start-after: #BEGIN gcovr html details
    :end-before: #END gcovr html details

This generates the following HTML page for the file ``example1.cpp``:

.. image:: ../images/screenshot-html-details.example.cpp.png
    :align: center

Note that the :option:`--html-details<gcovr --html-details>` option needs
a named output, e.g. via the the :option:`-o/--output<gcovr --output>` option.
For example, if the output is named ``coverage.html``,
then the web pages generated for each file will have names of the form
``coverage.<filename>.html``.

The :option:`--html-self-contained<gcovr --html-self-contained>` option controls
whether assets like CSS styles are bundled into the HTML file.
The :option:`--html<gcovr --html>` report defaults to self-contained mode.
but :option:`--html-details<gcovr --html-details>` defaults to
:option:`--no-html-self-contained<gcovr --html-self-contained>`
in order to avoid problems with the `Content Security Policy <CSP_>`_
of some servers, especially Jenkins.

.. _CSP: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP

.. versionadded:: 5.0
   Added :option:`--html-self-contained<gcovr --html-self-contained>`
   and :option:`--no-html-self-contained<gcovr --html-self-contained>`.

.. versionchanged:: 5.0
   Default to external CSS file for :option:`--html-details<gcovr --html-details>`.


.. _sonarqube_xml_output:

Sonarqube XML Output
~~~~~~~~~~~~~~~~~~~~

If you are using Sonarqube, you can get a coverage report
in a suitable XML format via the :option:`--sonarqube<gcovr --sonarqube>` option::

    gcovr --sonarqube coverage.xml

The Sonarqube XML format is documented at
`<https://docs.sonarqube.org/latest/analysis/generic-test/>`_.

.. _json_output:

JSON Output
~~~~~~~~~~~

The ``gcovr`` command can also generate a JSON output using
the :option:`--json<gcovr --json>` and :option:`--json-pretty<gcovr --json-pretty>`
options::

    gcovr --json coverage.json

The :option:`--json-pretty<gcovr --json-pretty>` option generates an indented
JSON output that is easier to read.

Structure of file is based on gcov JSON intermediate format
with additional key names specific to gcovr.

Structure of the JSON is following:
::

    {
        "gcovr/format_version": gcovr_json_version
        "files": [file]
    }

*gcovr_json_version*: version of gcovr JSON format

Each *file* has the following form:
::

    {
        "file": file
        "lines": [line]
    }

*file*: path to source code file, relative to gcovr
root directory.

Each *line* has the following form:
::

    {
        "branches": [branch]
        "count": count
        "line_number": line_number
        "gcovr/noncode": gcovr_noncode
    }

*gcovr_noncode*: if True coverage info on this line should be ignored

Each *branch* has the following form:
::

    {
      "count": count
      "fallthrough": fallthrough
      "throw": throw
    }

*file*, *line* and *branch* have the structure defined in gcov
intermediate format. This format is documented at
`<https://gcc.gnu.org/onlinedocs/gcc/Invoking-Gcov.html#Invoking-Gcov>`_.

If you just need a summary of the coverage information, similar to the tabulated
text based output, you can use :option:`--json-summary<gcovr --json-summary>`
instead.

Multiple JSON files can be merged into the coverage data
with sum of lines and branches execution.


.. _json_summary_output:

JSON Summary Output
~~~~~~~~~~~~~~~~~~~

The :option:`--json-summary<gcovr --json-summary>` option output coverage summary
in a machine-readable format for additional post processing. 
The format is identical to JSON output :option:`--json<gcovr --json>` option
without detailed ``lines`` information.
The :option:`--json-summary-pretty<gcovr --json-summary-pretty>` option
generates an indented JSON summary output that is easier to read.
Consider the following command:

.. include:: ../examples/example_json_summary.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an indented JSON summary:

.. include:: ../examples/example_json_summary.json
    :code: json

.. versionadded:: 5.0
   Added :option:`--json-summary<gcovr --json-summary>`
   and :option:`--json-summary-pretty<gcovr --json-summary-pretty>`.


.. _csv_output:

CSV Output
~~~~~~~~~~

The :option:`--csv<gcovr --csv>` option output comma-separated values
summarizing the coverage of each file. Consider the following command:

.. include:: ../examples/example_csv.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an CSV:

.. include:: ../examples/example_csv.csv
    :literal:

.. versionadded:: 5.0
   Added :option:`--csv<gcovr --csv>`.


.. _coveralls_output:

Coveralls JSON Output
~~~~~~~~~~~~~~~~~~~~~

If you are using Coveralls, you can get a coverage report
in a suitable JSON format via the :option:`--coveralls<gcovr --coveralls>` option::

    gcovr --coveralls coverage.json

The :option:`--coveralls-pretty<gcovr --coveralls-pretty>` option generates
an indented JSON output that is easier to read.

Keep in mind that the output contains the checksums of the source files. If you are
using different OSes, the line endings shall be the same.

If available, environment variable COVERALLS_REPO_TOKEN will be
consumed and baked into the JSON output.

If running in a CI additional variables are used:

- In Travis CI:

  - TRAVIS_JOB_ID
  - TRAVIS_BUILD_NUMBER
  - TRAVIS_PULL_REQUEST
  - TRAVIS_COMMIT
  - TRAVIS_BRANCH

- In Appveyor:

  - APPVEYOR_JOB_ID
  - APPVEYOR_JOB_NUMBER
  - APPVEYOR_PULL_REQUEST_NUMBER
  - APPVEYOR_REPO_COMMIT
  - APPVEYOR_REPO_BRANCH

- In Jenkins CI:

  - JOB_NAME
  - BUILD_ID
  - CHANGE_ID
  - GIT_COMMIT (if available)
  - BRANCH_NAME

- In GitHub Actions:

  - GITHUB_WORKFLOW
  - GITHUB_RUN_ID
  - GITHUB_SHA
  - GITHUB_HEAD_REF (if available)
  - GITHUB_REF

The Coveralls JSON format is documented at
`<https://docs.coveralls.io/api-introduction>`_.

.. versionadded:: 5.0
   Added :option:`--coveralls<gcovr --coveralls>`
   and :option:`--coveralls-pretty<gcovr --coveralls-pretty>`.


.. _multiple output formats:

Multiple Output Formats
~~~~~~~~~~~~~~~~~~~~~~~

You can write multiple report formats with one gcovr invocation
by passing the output filename directly to the report format flag.
If no filename is specified for the format,
the value from :option:`-o/--output<gcovr --output>` is used by default,
which itself defaults to stdout.

The following report format flags can take an optional output file name:

- :option:`gcovr --csv`
- :option:`gcovr --txt`
- :option:`gcovr --xml`
- :option:`gcovr --html`
- :option:`gcovr --html-details`
- :option:`gcovr --sonarqube`
- :option:`gcovr --json`
- :option:`gcovr --json-summary`
- :option:`gcovr --coveralls`

If the value given to the output option ends with a path seperator (``/`` or ``\``)
it is used a directory which is created first and a default filename depending
on the format is used.

Note that :option:`--html-details<gcovr --html-details>` overrides any value of
:option:`--html<gcovr --html>` if it is present.

.. _combining_tracefiles:

Combining Tracefiles
~~~~~~~~~~~~~~~~~~~~

You can merge coverage data from multiple runs with
:option:`-a/--add-tracefile<gcovr --add-tracefile>`.

For each run, generate :ref:`JSON output <json_output>`:

.. code-block:: bash

    ...  # compile and run first test case
    gcovr ... --json run-1.json
    ...  # compile and run second test case
    gcovr ... --json run-2.json


Next, merge the json files and generate the desired report::

    gcovr --add-tracefile run-1.json --add-tracefile run-2.json --html-details coverage.html

You can also use unix style wildcards to merge the json files without
duplicating :option:`-a/--add-tracefile<gcovr --add-tracefile>`. With this option
you have to place your pathnames with wildcards in double quotation marks::

    gcovr --add-tracefile "run-*.json" --html-details coverage.html

The gcovr Command
-----------------

The ``gcovr`` command recursively searches a directory tree to find
``gcov`` coverage files, and generates a text summary of the code
coverage.  The :option:`-h/--help<gcovr --help>` option generates the following
summary of the ``gcovr`` command line options:

.. autoprogram:: gcovr.__main__:create_argument_parser()
    :prog: gcovr
    :groups:

The above `Getting Started`_ guide
illustrates the use of some command line options.
`Using Filters`_ is discussed below.


Using Filters
-------------

Gcovr tries to only report coverage for files within your project,
not for your libraries. This is influenced by the following options:

-   :option:`-r`, :option:`--root`
-   :option:`-f`, :option:`--filter`
-   :option:`-e`, :option:`--exclude`
-   :option:`--gcov-filter`
-   :option:`--gcov-exclude`
-   :option:`--exclude-directories`
-   (the current working directory where gcovr is invoked)

These options take filters.
A filter is a regular expression that matches a file path.
Because filters are regexes,
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

-   ``--filter subdir/`` matches only that subdirectory

-   ``--filter '\.\./src/'`` matches a sibling directory ``../src``.
    But because a dot ``.`` matches any character in a regex,
    we have to escape it.
    You have to use additional shell escaping.
    This example uses single quotes for Bash or POSIX shell.

-   ``--filter '(.+/)?foo\.c$'`` matches only files called ``foo.c``.
    The regex must match from the start of the relative path,
    so we ignore any leading directory parts with ``(.+/)?``.
    The ``$`` at the end ensures that the path ends here.

If no :option:`-f/--filter<gcovr --filter>` is provided,
the :option:`-r/--root<gcovr --root>` is turned into a default filter.
Therefore, files outside of the :option:`-r/--root<gcovr --root>`
directory are excluded.

To be included in a report, the source file must match any
:option:`-f/--filter<gcovr --filter>`,
and must not match any :option:`-e/--exclude<gcovr --exclude>` filter.

The :option:`--gcov-filter<gcovr --gcov-filter>`
and :option:`--gcov-exclude<gcovr --gcov-exclude>` filters apply to the
``.gcov`` files created by ``gcov``.
This is useful mostly when running gcov yourself,
and then invoking gcovr with :option:`-g/--use-gcov-files<gcovr --use-gcov-files>`.
But these filters also apply when gcov is launched by gcovr.

Speeding up coverage data search
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :option:`--exclude-directories<gcovr --exclude-directories>` filter is used
while searching for raw coverage data (or for existing ``.gcov`` files when
:option:`-g/--use-gcov-files<gcovr --use-gcov-files>` is active).
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

If we run ``gcovr --exclude-directories 'build/a$'``,
this will exclude anything in the ``build/a`` directory
but will use the coverage data for ``better_code.o`` and ``main.o``.

This can speed up gcovr when you have a complicated build directory structure.
Consider also using the :option:`search_paths`
or :option:`--object-directory<gcovr --object-directory>` arguments to specify
where gcovr starts searching.
If you are unsure which directories are being searched,
run gcovr in :option:`-v/--verbose<gcovr --verbose>` mode.

For each found coverage data file gcovr will invoke the ``gcov`` tool.
This is typically the slowest part,
and other filters can only be applied *after* this step.
In some cases, parallel execution with the :option:`-j<gcovr -j>` option
might be helpful to speed up processing.

Filters for symlinks
~~~~~~~~~~~~~~~~~~~~

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

.. note::
    This section discusses symlinks on Unix systems.
    The behavior under Windows is unclear.
    If you have more insight,
    please update this section by submitting a pull request
    (see our :doc:`contributing guide <contributing>`).


.. _configuration:

Configuration Files
-------------------

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


.. _exclusion markers:

Exclusion Markers
-----------------

You can exclude parts of your code from coverage metrics.

-   If ``GCOVR_EXCL_LINE`` appears within a line,
    that line is ignored.
-   If ``GCOVR_EXCL_START`` appears within a line,
    all following lines (including the current line) are ignored
    until a ``GCOVR_EXCL_STOP`` marker is encountered.

Instead of ``GCOVR_*``,
the markers may also start with ``GCOV_*`` or ``LCOV_*``.
However, start and stop markers must use the same style.
The markers are not configurable.

In the excluded regions, *any* coverage is excluded.
It is not currently possible to exclude only branch coverage in that region.
In particular, lcov's EXCL_BR markers are not supported
(see issue :issue:`121`).


Acknowledgements
----------------

.. include:: ../../AUTHORS.txt

The development of Gcovr has been partially supported
by Sandia National Laboratories.  Sandia National Laboratories is
a multi-program laboratory managed and operated by Sandia Corporation,
a wholly owned subsidiary of Lockheed Martin Corporation, for the
U.S.  Department of Energy's National Nuclear Security Administration
under contract DE-AC04-94AL85000.
