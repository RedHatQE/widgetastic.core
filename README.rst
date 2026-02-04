================
widgetastic.core
================


.. image:: https://img.shields.io/pypi/pyversions/widgetastic.core.svg?style=flat
    :target: https://pypi.org/project/widgetastic.core
    :alt: Python supported versions

.. image:: https://badge.fury.io/py/widgetastic.core.svg
    :target: https://pypi.org/project/widgetastic.core

.. image:: https://github.com/RedHatQE/widgetastic.core/workflows/%F0%9F%95%B5%EF%B8%8F%20Test%20suite/badge.svg?branch=master
    :target: https://github.com/RedHatQE/widgetastic.core/actions?query=workflow%3A%22%F0%9F%95%B5%EF%B8%8F+Test+suite%22

.. image:: https://codecov.io/gh/RedHatQE/widgetastic.core/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/RedHatQE/widgetastic.core

.. image:: https://readthedocs.org/projects/widgetastic/badge/?version=latest
    :target: http://widgetastic.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


Widgetastic - Making testing of UIs **fantastic**.

Written originally by Milan Falesnik (mfalesni@redhat.com, http://www.falesnik.net/) and
other contributors since 2016.

Licensed under Apache license, Version 2.0

Documentation
-------------
Full documentation is available at https://widgetastic.readthedocs.io/en/latest/

Browser Engine Support
----------------------
**Current Version (v2.x.x)**: Built on `Playwright <https://playwright.dev/>`_ for modern, reliable web automation.
The main branch contains the Playwright implementation and will receive all future updates and features.

**Legacy Version (v1.x.x)**: Based on Selenium WebDriver.
For projects still using Selenium, legacy support is maintained on the `legacy-selenium-support <https://github.com/RedHatQE/widgetastic.core/tree/legacy-selenium-support>`_ branch.
Please note that this branch receives only critical bug fixes and is not recommended for new projects.


Projects using widgetastic
---------------------------
- ManageIQ `integration_tests <https://github.com/ManageIQ/integration_tests>`_
- Satellite `airgun <https://github.com/SatelliteQE/airgun>`_
- Cloud Services (insights-qe)
- Windup `integration_test <https://github.com/windup/windup_integration_test>`_

Installation
------------

.. code-block:: bash

    pip install -U widgetastic.core


Contributing
------------
- Fork
- Clone
- Create a branch in your repository for your feature or fix
- Write the code, make sure you add unit tests.
- Use ``pre-commit`` when committing to enforce code style
- Run ``pytest`` to run unit tests
- Push to your fork and create a pull request
- Observe checks in GitHub for further docs and build testing
