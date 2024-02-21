.. _jacoco_output:

JaCoCo XML Output
=================

.. program:: gcovr

The ``gcovr`` command can generate a
JaCoCo XML output using the :option:`--jacoco`
and :option:`--jacoco-pretty` options:

    gcovr --jacoco jacoco.xml

This XML format is described in the
`JaCoCo XML <https://www.jacoco.org/jacoco/trunk/coverage/report.dtd>`__
DTD.

The :option:`--jacoco` option generates a denser XML output, and the
:option:`--jacoco-pretty` option generates an indented
XML output that is easier to read. Note that the XML output contains more
information than the tabular summary.  The tabular summary shows the percentage
of covered lines, while the XML output includes branch statistics and the number
of times that each line was covered.  Consequently, XML output can be
used to support performance optimization in the same manner that
``gcov`` does.

.. versionadded:: 7.0

   The :option:`--jacoco` and :option:`--jacoco-pretty`.
