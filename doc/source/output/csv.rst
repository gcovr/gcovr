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

Be carefule if you print the output of a CSV to STDOUT and redirect it to
a file. According to `RFC4180 <RFC4180_>`_ the line endings must be CRLF.

.. _RFC4180: https://datatracker.ietf.org/doc/html/rfc4180

.. versionadded:: 5.0
   Added :option:`--csv<gcovr --csv>`.
