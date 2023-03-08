
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

If you have same function names defined on different line the default behaviour is to abort.
With the :option:`--merge-mode-functions` you can change this:

- ``strict``: Abort if same function is defined on a different line (old behaviour).
- ``merge-use-line-0``: Allow same function on different lines, in this case use line 0.
- ``merge-use-line-min``: Allow same function on different lines, in this case the minimum line.
- ``merge-use-line-max``: Allow same function on different lines, in this case use maximum line.
- ``separate``: Allow same function on different lines. Instead of merging keep the functions separate.

.. versionadded:: 6.0

   The :option:`gcovr --json-base` option.
   The :option:`gcovr --merge-mode-functions` option.
