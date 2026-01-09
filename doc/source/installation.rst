Installation
============

.. include:: ../../README.rst
    :start-after: .. begin installation
    :end-before: .. end installation

Which environments does ``gcovr`` support?

Python:
    3.10+.

    The automated tests run on CPython (versions 3.10, 3.11, 3.12, 3.13)
    and a compatible PyPy3.
    Gcovr will only run on Python versions with upstream support.

    Last gcovr release for old Python versions:

    ====== =====
    Python gcovr
    ====== =====
    2.6    3.4
    2.7    4.2
    3.4    4.1
    3.5    4.2
    3.6    5.0
    3.7    6.0
    3.8    8.2
    3.9    8.5
    ====== =====

Operating System:
    Linux, Windows, and macOS.

    The automated tests run on:

    - Ubuntu 20.04, 22.04 and 24.04
    - Windows Server 2022 and 2025
    - MacOS 14 and 15.

Compiler:
    GCC and Clang. The versions used for development tests are
    documented in the :ref:`contribution guide <development environment>`.
