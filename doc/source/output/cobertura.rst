.. program:: gcovr

.. _cobertura_output:

Cobertura XML Output
====================

The ``gcovr`` command can generate a
Cobertura XML output using the :option:`--cobertura`
and :option:`--cobertura-pretty` options:

.. literalinclude:: ../../examples/example_cobertura.sh
    :language: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an XML summary of the lines executed:

.. literalinclude:: ../../examples/example_cobertura.xml
    :language: xml

This XML format is described in the
`Cobertura XML DTD <https://github.com/gcovr/gcovr/blob/main/tests/cobertura.coverage-04.dtd>`__
suitable for import and display within the
`Jenkins <https://www.jenkins.io/>`__ and `Hudson <https://projects.eclipse.org/projects/technology.hudson>`__
continuous integration servers using the
`Jenkins Coverage Plugin <https://github.com/jenkinsci/coverage-plugin>`__.

The :option:`--cobertura` option generates a denser XML output, and the
:option:`--cobertura-pretty` option generates an indented
XML output that is easier to read. Note that the XML output contains more
information than the tabular summary.  The tabular summary shows the percentage
of covered lines, while the XML output includes branch statistics and the number
of times that each line was covered.  Consequently, XML output can be
used to support performance optimization in the same manner that
``gcov`` does.

.. versionadded:: 5.1

   The :option:`--cobertura` and :option:`--cobertura-pretty` options
   were added as an alias for :option:`-x`/\ :option:`--xml`
   and :option:`--xml-pretty`, respectively.
   This avoids confusion with other XML output formats
   like :ref:`sonarqube_xml_output`.
   The old options remain available for backwards compatibility.
