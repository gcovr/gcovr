.. _cobertura_output:

Cobertura XML Output
====================

The default output format for ``gcovr`` is to generate a tabular
summary in plain text.  The ``gcovr`` command can also generate an
XML output using the :option:`-x/--xml<gcovr --xml>`
and :option:`--xml-pretty<gcovr --xml-pretty>` options:

.. include:: ../../examples/example_xml.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an XML summary of the lines executed:

.. include:: ../../examples/example_xml.xml
    :code: xml

This XML format is in the
`Cobertura XML <http://cobertura.sourceforge.net/xml/coverage-04.dtd>`__
format suitable for import and display within the
`Jenkins <http://www.jenkins-ci.org/>`__ and `Hudson <http://www.hudson-ci.org/>`__
continuous integration servers using the
`Cobertura Plugin <https://wiki.jenkins-ci.org/display/JENKINS/Cobertura+Plugin>`__.
Gcovr also supports a :ref:`sonarqube_xml_output`.

The :option:`-x/--xml<gcovr --xml>` option generates a denser XML output, and the
:option:`--xml-pretty<gcovr --xml-pretty>` option generates an indented
XML output that is easier to read. Note that the XML output contains more
information than the tabular summary.  The tabular summary shows the percentage
of covered lines, while the XML output includes branch statistics and the number
of times that each line was covered.  Consequently, XML output can be
used to support performance optimization in the same manner that
``gcov`` does.
