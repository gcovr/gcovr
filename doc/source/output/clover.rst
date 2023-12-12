.. _clover_output:

Clover XML Output
=================

.. program:: gcovr

The ``gcovr`` command can generate a
Cobertura XML output using the :option:`--clover`
and :option:`--clover-pretty` options:

.. include:: ../../examples/example_clover.sh
    :code: bash
    :start-after: #BEGIN gcovr
    :end-before: #END gcovr

This generates an XML summary of the lines executed:

.. include:: ../../examples/example_clover.xml
    :code: xml

This XML format is described in the
`Clover XML <https://bitbucket.org/atlassian/clover/src/master/etc/schema/clover.xsd>`__
XSD suitable for import and display within the
`Atlassian Bamboo <https://www.atlassian.com/de/software/bamboo>`__
continuous integration servers.

The :option:`--clover` option generates a denser XML output, and the
:option:`--clover-pretty` option generates an indented
XML output that is easier to read.

.. versionadded:: NEXT

    Add :option:`--clover` and :option:`--clover-pretty`.