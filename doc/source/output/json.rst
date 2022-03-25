
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


JSON Format Reference
---------------------

Structure of file is based on gcov JSON intermediate format
with additional key names specific to gcovr.

Structure of the JSON is following:
::

    {
        "gcovr/format_version": gcovr_json_version
        "files": [file]
    }

*gcovr_json_version*: version of gcovr JSON format.
This is independently versioned from gcovr itself.

Each *file* has the following form:
::

    {
        "file": file
        "lines": [line]
    }

*file*: path to source code file, relative to gcovr
root directory.

Each **line** has the following form:
::

    {
        "branches": [branch]
        "count": count
        "line_number": line_number
        "gcovr/noncode": gcovr_noncode
    }

*gcovr_noncode*: if True coverage info on this line should be ignored

Each **branch** has the following form:
::

    {
      "count": count
      "fallthrough": fallthrough
      "throw": throw
    }

*file*, *line* and *branch* have the structure defined in gcov
intermediate format. This format is documented at
`<https://gcc.gnu.org/onlinedocs/gcc/Invoking-Gcov.html#Invoking-Gcov>`_.


.. _json_summary_output:

JSON Summary Output
-------------------

The :option:`--json-summary<gcovr --json-summary>` option output coverage summary
in a machine-readable format for additional post processing.
The format is identical to JSON output :option:`--json<gcovr --json>` option
without detailed ``lines`` information.
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
