.. program:: gcovr

.. _sonarqube_xml_output:

SonarQube XML Output
====================

If you are using SonarQube, you can get a coverage report
in a suitable XML format via the :option:`--sonarqube` option::

    gcovr --sonarqube coverage.xml

The SonarQube XML format is documented at
`<https://docs.sonarsource.com/sonarqube-server/2025.2/analyzing-source-code/test-coverage/generic-test-data/>`_.

Coverage Metrics
----------------

By default the coverage report contains metrics for line and branch coverage. You can adjust the metrics available in the report with the ``--sonarqube-metric`` option. The following options are available:

.. list-table::
   :header-rows: 1

   * - Option
     - Description

   * - ``--sonarqube-metric=line``
     - The generated XML contains only line coverage information

   * - ``--sonarqube-metric=branch``
     - The generated XML contains line and branch coverage information

   * - ``--sonarqube-metric=condition``
     - The generated XML contains line and branch coverage information, but the branch coverage is actually condition coverage. Requires GCC 14 or newer and the code to be compiled with ``-fcondition-coverage``.

   * - ``--sonarqube-metric=decision``
     - The generated XML contains line and branch coverage information, but the branch coverage is actually decision coverage. Requires the option ``--decisions`` to be enabled
