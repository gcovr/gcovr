
.. _json_output:

JSON Output
===========

The ``gcovr`` command can also generate a JSON output using
the :option:`--json<gcovr --json>` and :option:`--json-pretty<gcovr --json-pretty>`
options::

    gcovr --json coverage.json

The :option:`--json-pretty<gcovr --json-pretty>` option generates an indented
JSON output that is easier to read.

If you just need a summary of the coverage information, similar to the tabulated
text based output, you can use :option:`--json-summary<gcovr --json-summary>`
instead (see :ref:`json_summary_output`).

Multiple JSON files can be merged into the coverage data
with sum of lines and branches execution, see :ref:`merging_coverage`.

See the :ref:`json_format` for a description of the file format.

.. _json_format:

JSON Format Reference
---------------------

The structure of the JSON input/output files
is based on the GCC gcov JSON intermediate format,
but with additional keys specific to gcovr.
Field names use ``snake_case``.
Gcovr-specific fields are prefixed with ``gcovr/...``.

The GCC gcov JSON format is documented at
`<https://gcc.gnu.org/onlinedocs/gcc/Invoking-Gcov.html#Invoking-Gcov>`_.

The **top level** of the file looks like the following::

    {
        "gcovr/format_version": version,
        "files": [file]
    }

gcovr/format_version: string
  A version number string for the gcovr JSON format.
  This is versioned independently from gcovr itself.
  Consumers of gcovr JSON reports should check that they are SemVer-compatible
  with the declared version.
  Gcovr itself will only consume input files that match the exact version.

files: list
  An unordered list of :ref:`file <json_format_file>` entries.

.. _json_format_file:

File entries
~~~~~~~~~~~~

Each **file** entry contains coverage data for one source file::

    {
        "file": filename,
        "lines": [line],
        "functions": [function]
    }

file: string
  Path to the source code file.
  If the source file is within the gcovr root directory,
  the path will be relative.

lines: list
  An unordered list of :ref:`line <json_format_line>` coverage entries.

functions: list
  An unordered list of :ref:`function <json_format_function>` entries.

.. _json_format_line:

Line entries
~~~~~~~~~~~~

Each **line** entry contains coverage data for one line::

    {
        "branches": [branch],
        "count": count,
        "line_number": line_number,
        "gcovr/excluded": excluded
        "gcovr/decision": decision
    }

branches: list
  A list of :ref:`branch <json_format_branch>` coverage entries.

count: int
  How often this line was executed.

line_number: int
  The 1-based line number to which this entry relates.

gcovr/excluded: boolean
  True if coverage data for this line was explicitly excluded,
  in particular with :ref:`exclusion markers`.
  May be absent if false.

gcovr/decision: object
  The :ref:`decision <json_format_decision>` entry for this line, if any.
  Absent if there is no decision to report.
  Requires that :option:`--decisions <gcovr --decisions>` coverage analysis was enabled.

If there is no line entry for a source code line,
it either means that the compiler did not generate any code for that line,
or that gcovr ignored this coverage data due to heuristics.

The line entry should be interpreted as follows:

* if ``gcovr/excluded`` is true, the line should not be included in coverage reports.
* if ``count`` is 0, the line is uncovered
* if ``count`` is nonzero, the line is covered

.. versionchanged:: NEXT
   The ``gcovr/excluded`` field can be absent if false.

.. versionchanged:: NEXT
   The ``gcovr/noncode`` field was removed.
   Instead of generating noncode entries, the entire line is skipped.

.. _json_format_branch:

Branch entries
~~~~~~~~~~~~~~

Each **branch** provides information about a branch on that line::

    {
      "count": count,
      "fallthrough": fallthrough,
      "throw": throw
    }

This exactly matches the GCC gcov format.

count: int
  How often this branch was taken.

fallthrough: boolean
  Whether this is the “fallthrough” branch.

throw: boolean
  Whether this is an exception-only branch.

.. _json_format_decision:

Decision entries
~~~~~~~~~~~~~~~~

Each **decision** summarizes the line's branch coverage data::

    {
      "type": "uncheckable"
    }

    {
      "type": "conditional",
      "count_true": count_true,
      "count_false": count_false
    }

    {
      "type": "switch",
      "count": count
    }

type: string
  A tag/discriminator for the type of the decision.

type: "uncheckable"
  Control flow was recognized on this line,
  but cannot be interpreted unambiguously.

  No further fields.

type: "conditional"
  This line represents simple control flow like an ``if`` or ``while``.

  count_true: int
    How often the decision evaluated to “true”.

  count_false: int
    How often the decision evaluated to “false”.

  Note that the true/false are heuristic guesses,
  and might also be inverted.

type: "switch"
  This line is a switch-case.

  count: int
    How often this case was taken.

.. _json_format_function:

Function entries
~~~~~~~~~~~~~~~~

Each **function** entry describes a line in the source file::

    {
      "name": name,
      "lineno": lineno,
      "execution_count": count,
    }

name: string
  The name of the function, mangled or demangled depending on compiler version.
  May be incompatible with upstream GCC gcov JSON.

lineno: int
  The line number (1-based) where this function was defined.
  Incompatible with GCC gcov JSON.

execution_count: int
  How often this function was called.

.. _json_summary_output:

JSON Summary Output
-------------------

The :option:`--json-summary<gcovr --json-summary>` option output coverage summary
in a machine-readable format for additional post processing.
The format corresponds to the normal JSON output :option:`--json<gcovr --json>` option,
but without line-level details
and with added aggregated statistics.
The :option:`--json-summary-pretty<gcovr --json-summary-pretty>` option
generates an indented JSON summary output that is easier to read.
Consider the following command:

.. include:: ../../examples/example_json_summary.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an indented JSON summary:

.. include:: ../../examples/example_json_summary.json
    :code: json

.. versionadded:: 5.0
   Added :option:`--json-summary<gcovr --json-summary>`
   and :option:`--json-summary-pretty<gcovr --json-summary-pretty>`.

.. json_summary_format:

JSON Summary Format Reference
-----------------------------

The summary format follows the general structure of the :ref:`json_format`,
but removes line-level information and adds aggregated statistics.

The **top-level** looks like::

    {
      "gcovr/summary_format_version": version,
      "files: [file],
      "root": path,
      ...statistics
    }

gcovr/summary_format_version: string
  A version number string for the summary format.
  This is versioned independently from gcovr and the full JSON format.
  Consumers of gcovr JSON Summary reports should check
  that they are SemVer-compatible with the declared version.

files: list
  Unordered list of :ref:`file summary entries <json_summary_format_file>`.

root: string
  Path to the gcovr root directory, useful for reconstructing the absolute path of source files.
  This root path is relative to the output file,
  or to the current working directory if the report is printed to stdout.

...statistics
  Project-level :ref:`aggregated statistics <json_summary_format_statistics>`.
  A NaN percentage (0/0) is reported as zero (``0.0``).

.. _json_summary_format_file:

File summary entries
~~~~~~~~~~~~~~~~~~~~

The **file summary** looks like::

    {
      "filename": path,
      ...statistics
    }

filename: string
  Path to the source file, relative to the gcovr root directory.

...statistics
  File-level :ref:`aggregated statistics <json_summary_format_statistics>`.
  A NaN percentage (0/0) is reported as ``null``.

.. _json_summary_format_statistics:

Summary statistics
~~~~~~~~~~~~~~~~~~

The root and file summaries contain the following additional fields::

    ...
    "branch_covered": ...,
    "branch_total": ...,
    "branch_percent": ...,

    "line_covered": ...,
    "line_total": ...,
    "line_percent": ...,

    "function_covered": ...,
    "function_total": ...,
    "function_percent": ...,
    ...

These fields can be described by the glob expression
``{branch,line,function}_{covered,total,percent}``.

ELEMENT_covered: int
  How many elements were covered or executed.

ELEMENT_total: int
  How many elements there are in total.

ELEMENT_percent: float
  Percentage of covered elements (covered/total)
  in the range 0 to 100.
  Note that the different contexts differ in their treatment of NaN values.
