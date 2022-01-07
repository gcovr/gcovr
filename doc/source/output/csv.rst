.. _csv_output:

CSV Output
==========

The :option:`--csv<gcovr --csv>` option output comma-separated values
summarizing the coverage of each file. Consider the following command:

.. include:: ../../examples/example_csv.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an CSV:

.. include:: ../../examples/example_csv.csv
    :literal:

.. versionadded:: 5.0
   Added :option:`--csv<gcovr --csv>`.
