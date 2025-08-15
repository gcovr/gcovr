.. program:: gcovr

.. _json_output:

JSON Output
===========

The ``gcovr`` command can generate JSON output using
the :option:`--json` and :option:`--json-pretty`
options:

.. include:: ../../examples/example_json.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an indented JSON report:

.. include:: ../../examples/example_json.json
    :literal:

The :option:`--json-pretty` option generates an indented
JSON output that is easier to read.

If you just need a summary of the coverage information, similar to the tabulated
text based output, you can use :option:`--json-summary`
instead (see :ref:`json_summary_output`).

Multiple JSON files can be merged into the coverage data
with sum of lines and branches execution, see :ref:`merging_coverage`.

See the :ref:`json_format` for a description of the file format.

.. versionchanged:: 8.0
   Order of keys changed from alphabetical to logical.

.. _json_format:

JSON Format Reference
---------------------

The structure of the JSON input/output files
is based on the GCC gcov JSON intermediate format,
but with additional keys specific to gcovr.
Field names use ``snake_case``.
Gcovr-specific fields are prefixed with ``gcovr/``.

The GCC gcov JSON format is documented at
`<https://gcc.gnu.org/onlinedocs/gcc-14.1.0/gcc/Invoking-Gcov.html>`_.

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

  The current version is:

  .. include:: ../../../src/gcovr/data_model/version.py
      :start-after: # BEGIN version
      :end-before: # END version

files: list
  An unordered list of :ref:`file <json_format_file>` entries.

.. _json_format_file:

File entries
~~~~~~~~~~~~

Each **file** entry contains coverage data for one source file::

    {
        "file": filename,
        "lines": [line],
        "functions": [function],
        "gcovr/data_sources": [data_source]
    }

file: string
  Path to the source code file.
  If the source file is within the gcovr root directory,
  the path will be relative.

lines: list
  An ordered list of :ref:`line <json_format_line>` coverage entries.

functions: list
  An ordered list of :ref:`function <json_format_function>` entries.

gcovr/data_sources: list
  A list of files from which the coverage object was populated.
  This entry is only available if :option:`--verbose` is given.

.. versionadded:: 8.3
   The ``gcovr/data_sources`` is added.

.. _json_format_line:

Line entries
~~~~~~~~~~~~

Each **line** entry contains coverage data for one line::

    {
        "line_number": line_number,
        "function_name": function_name,
        "block_ids", [block_ids],
        "count": count,
        "branches": [branch],
        "conditions", [condition]
        "gcovr/decision": decision,
        "calls": calls,
        "gcovr/md5": md5,
        "gcovr/excluded": excluded,
        "gcovr/data_sources": [data_source]
    }

The ordering and merge key is ``(line_number, function_name, number of branches, list of condition counts, list of block ids)``.

line_number: int
  The 1-based line number to which this entry relates.

function_name: str
  Contains the name of the function to which the line belongs to.
  If ``gcov`` JSON format is used it is always the mangled name. If the
  legacy ``gcov`` text format is used it contains the demangled name if
  supported by ``gcov``, else the mangled name. Can be missing for a
  line with an inlined statement.

block_ids: list
  The list of block ids defined in this line.

count: int
  How often this line was executed.

branches: list
  An ordered list of :ref:`branch <json_format_branch>` coverage entries.

conditions: list
  Only available if GCOV JSON format is used it contains an ordered list
  of :ref:`branch <json_format_condition>` coverage entries.

gcovr/decision: object
  The :ref:`decision <json_format_decision>` entry for this line, if any.
  Absent if there is no decision to report.
  Requires that :option:`--decisions` coverage analysis was enabled.

calls: object
  The :ref:`call <json_format_call>` for this line, if any.
  Absent if there is no call to report.

gcovr/md5: str
  The MD5 sum of the line.

gcovr/excluded: boolean
  True if coverage data for this line was explicitly excluded,
  in particular with :ref:`exclusion markers`.
  May be absent if false.

gcovr/data_sources: list
  A list of files from which the coverage object was populated.
  This entry is only available if :option:`--verbose` is given.


If there is no line entry for a source code line,
it either means that the compiler did not generate any code for that line,
or that gcovr ignored this coverage data due to heuristics.

The line entry should be interpreted as follows:

* if ``gcovr/excluded`` is true, the line should not be included in coverage reports.
* if ``count`` is 0, the line is uncovered
* if ``count`` is nonzero, the line is covered

.. versionadded:: NEXT
   The ``gcovr/data_sources`` is added.

.. versionadded:: 8.0
   The ``conditions`` is added.

.. versionadded:: 8.0
   The ``block_ids`` is added.

.. versionadded:: 8.0
   The ``function_name`` is added.

.. versionadded:: 8.0
   The ``gcovr/md5`` is added.

.. versionadded:: 6.0
   The ``gcovr/excluded`` field can be absent if false.

.. versionchanged:: 6.0
   The ``gcovr/noncode`` field was removed.
   Instead of generating noncode entries, the entire line is skipped.

.. _json_format_branch:

Branch entries
~~~~~~~~~~~~~~

Each **branch** provides information about a branch on that line::

    {
      "branchno": branchno,
      "count": count,
      "fallthrough": fallthrough,
      "throw": throw,
      "source_block_id": number,
      "destination_block_id": number,
      "gcovr/excluded": excluded,
      "gcovr/data_sources": [data_source]
    }

The ordering and merge key is ``(branchno, source_block_id, destination_block_id)``.

This exactly matches the GCC gcov format except ``branchno``.

branchno: int
  The branch number is only available if data is parsed from GCC gcov text format.

count: int
  How often this branch was taken.

fallthrough: boolean
  Whether this is the “fallthrough” branch.

throw: boolean
  Whether this is an exception-only branch.

source_block_id: int
  The source block of this branch.

destination_block_id: int
  The destination block of this branch.
  Only available if ``gcov`` JSON format is used.

gcovr/excluded: boolean
  True if coverage data for this line was explicitly excluded,
  in particular with :ref:`exclusion markers`.
  May be absent if false.

gcovr/data_sources: list
  A list of files from which the coverage object was populated.
  This entry is only available if :option:`--verbose` is given.

.. versionadded:: NEXT
   The ``branchno`` is added.

.. versionadded:: NEXT
   The ``gcovr/excluded`` is added.

.. versionadded:: NEXT
   The ``gcovr/data_sources`` is added.

.. versionadded:: 8.0
   Added ``destination_blockno`` field.

.. versionadded:: 8.3
   Added ``source_block_id`` field.

.. versionchanged:: 8.3
   Renamed ``destination_blockno`` to ``destination_block_id`` field.

.. _json_format_condition:

Condition entries
~~~~~~~~~~~~~~~~~

Each **condition** provides information about a condition on that line::

    {
      "conditionno": conditionno,
      "count": count,
      "covered": covered,
      "not_covered_false": not_covered_false,
      "not_covered_true": not_covered_true,
      "gcovr/excluded": excluded,
      "gcovr/data_sources": [data_source]
    }

The ordering and merge key is ``(conditionno, count)``.

This exactly matches the GCC gcov format except ``conditionno``.

conditionno: int
  The index number of the condition in GCC gcov output.

count: int
  Number of condition outcomes in this expression.

covered: int
  Number of covered condition outcomes in this expression.

not_covered_false: list[int]
  Terms, by index, not seen as false in this expression.

not_covered_true: list[int]
  Terms, by index, not seen as true in this expression.

gcovr/excluded: boolean
  True if coverage data for this line was explicitly excluded,
  in particular with :ref:`exclusion markers`.
  May be absent if false.

gcovr/data_sources: list
  A list of files from which the coverage object was populated.
  This entry is only available if :option:`--verbose` is given.

.. versionadded:: NEXT
   The ``conditionno`` is added.

.. versionadded:: NEXT
   New ``gcovr/excluded`` field.

.. versionadded:: NEXT
   The ``gcovr/data_sources`` is added.

.. _json_format_decision:

Decision entries
~~~~~~~~~~~~~~~~

Each **decision** summarizes the line's branch coverage data::

    {
      "type": "uncheckable",
      "gcovr/data_sources": [data_source]
    }

    {
      "type": "conditional",
      "count_true": count_true,
      "count_false": count_false,
      "gcovr/data_sources": [data_source]
    }

    {
      "type": "switch",
      "count": count,
      "gcovr/data_sources": [data_source]
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

gcovr/data_sources: list
  A list of files from which the coverage object was populated.
  This entry is only available if :option:`--verbose` is given.

.. versionadded:: NEXT
   The ``gcovr/data_sources`` is added.

.. _json_format_call:

Call entries
~~~~~~~~~~~~

Each **call** provides information about a call on that line::

    {
      "callno": callno,
      "source_block_id": source_block_id,
      "destination_block_id": destination_block_id,
      "returned": returned,
      "gcovr/excluded": excluded,
      "gcovr/data_sources": [data_source]
    }

The ordering and merge key is ``(callno, source_block_id, destination_block_id)``.

callno: int
  Only available if ``gcov`` text format is used.

source_block_id: int
  The source block number of the call.

destination_block_id: int
  Only available if ``gcov`` JSON format is used.

returned: int
  How often this call returned, if the value is 0 the call is uncovered.

gcovr/excluded: boolean
  True if coverage data for this line was explicitly excluded,
  in particular with :ref:`exclusion markers`.
  May be absent if false.

gcovr/data_sources: list
  A list of files from which the coverage object was populated.
  This entry is only available if :option:`--verbose` is given.

.. versionchanged:: NEXT
   New ``returned`` field is replacing the field ``covered``.

.. versionadded:: NEXT
   New ``gcovr/excluded`` field.

.. versionadded:: NEXT
   The ``gcovr/data_sources`` is added.

.. _json_format_function:

Function entries
~~~~~~~~~~~~~~~~

Each **function** entry describes a line in the source file::

    {
      "name": name,
      "demangled_name": demangled_name,
      "lineno": lineno,
      "execution_count": count,
      "branch_percent": percent,
      "pos": [
        "<start line>:<start column>",
        "<end line>:<end column>"
      ]
      "gcovr/excluded": excluded,
      "gcovr/data_sources": [data_source]
    }

The ordering and merge key is ``function_name``.

name: string
  The mangled name of the function if present. Is missing if GCOV text format is
  used and GCOV tool supports demangled names.

demangled_name: string
  The demangled name of the function if present. Is missing if GCOV text format is
  used and GCOV tool doesn't support demangled names.

lineno: int
  The line number (1-based) where this function was defined.
  Incompatible with GCC gcov JSON.

execution_count: int
  How often this function was called.

branch_percent: float
  The branch coverage in percent (0.0 to 100.0).

pos: list
  A list with start and end position of function (1-based). Both entries are string with
  line and column separated by ``:``. Only available if ``gcov`` JSON format is
  used.

gcovr/excluded: boolean
  True if coverage data for this function was explicitly excluded,
  in particular with :ref:`exclusion markers`.
  May be absent if false.

gcovr/data_sources: list
  A list of files from which the coverage object was populated.
  This entry is only available if :option:`--verbose` is given.

* if ``gcovr/excluded`` is true, the line should not be included in coverage reports.

.. versionadded:: NEXT
   The ``gcovr/data_sources`` is added.

.. versionadded:: 8.0
   Added ``pos`` field.

.. versionchanged:: 8.0
   The ``name`` is changed to contain the mangled name previous content is now
   available as ``demangled_name`` as it is in GCOV JSON format.

.. versionremoved:: 8.0
   Removed ``returned_count`` field because missing in ``gcov`` JSON format.

.. versionadded:: 7.0
   New ``returned_count`` and ``branch_percent`` field.

.. versionadded:: 6.0
   New ``gcovr/excluded`` field.

.. _merging_coverage:

JSON Format merging
-------------------

You can merge coverage data from multiple runs with :option:`--json-add-tracefile`.

For each run, generate :ref:`JSON output <json_output>`:

.. code-block:: bash

    ...  # compile and run first test case
    gcovr ... --json run-1.json
    ...  # compile and run second test case
    gcovr ... --json run-2.json


Next, merge the json files and generate the desired report::

    gcovr --json-add-tracefile run-1.json --json-add-tracefile run-2.json --html-details coverage.html

You can also use unix style wildcards to merge the json files without
duplicating :option:`--json-add-tracefile`. With this option
you have to place your pathnames with wildcards in double quotation marks::

    gcovr --json-add-tracefile "run-*.json" --html-details coverage.html

If you want to merge coverage reports generated in different :option:`--root` directories you
can use the :option:`--json-base` to get the same root directory for all reports.

If you have same function names defined on different line the default behavior is to abort.
With the :option:`--merge-mode-functions` you can change this:

- ``strict``: Abort if same function is defined on a different line (old behavior).
- ``merge-use-line-0``: Allow same function on different lines, in this case use line 0.
- ``merge-use-line-min``: Allow same function on different lines, in this case the minimum line.
- ``merge-use-line-max``: Allow same function on different lines, in this case use maximum line.
- ``separate``: Allow same function on different lines. Instead of merging keep the functions separate.

.. versionremoved:: NEXT

    Removed the option ``--merge-mode-conditions`` option.

.. versionadded:: 8.3

    The ``--merge-mode-conditions`` option.

.. versionadded:: 6.0

   The :option:`gcovr --json-base` option.
   The :option:`gcovr --merge-mode-functions` option.

.. _json_summary_output:

JSON Summary Output
-------------------

The :option:`--json-summary` option output coverage summary
in a machine-readable format for additional post processing.
The format corresponds to the normal JSON output :option:`--json` option,
but without line-level details
and with added aggregated statistics.
The :option:`--json-summary-pretty` option
generates an indented JSON summary output that is easier to read.
Consider the following command:

.. literalinclude:: ../../examples/example_json_summary.sh
    :language: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an indented JSON summary:

.. literalinclude:: ../../examples/example_json_summary.json
    :language: json

.. versionadded:: 5.0
   Added :option:`--json-summary`
   and :option:`--json-summary-pretty`.

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

  The current version is:

  .. include:: ../../../src/gcovr/formats/json/write.py
      :start-after: # BEGIN summary version
      :end-before: # END summary version

files: list
  List of :ref:`file summary entries <json_summary_format_file>`.

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
