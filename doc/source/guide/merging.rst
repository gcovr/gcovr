
.. program is needed to resolve option links
.. program::  gcovr

.. _merging_coverage:

Merging Coverage Data
=====================

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

If you want to merge coverage reports generated in different `--root` directories you
can use the :option:`--json-base` to get the same root directory for all reports.

.. versionadded:: NEXT

   The :option:`gcovr --json-base` option.
