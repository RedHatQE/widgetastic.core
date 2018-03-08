================
widgetastic.core
================

.. image:: https://travis-ci.org/RedHatQE/widgetastic.core.svg?branch=master
    :target: https://travis-ci.org/RedHatQE/widgetastic.core

.. image:: https://coveralls.io/repos/github/RedHatQE/widgetastic.core/badge.svg?branch=master
    :target: https://coveralls.io/github/RedHatQE/widgetastic.core?branch=master

.. image:: https://readthedocs.org/projects/widgetasticcore/badge/?version=latest
    :target: http://widgetasticcore.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://www.quantifiedcode.com/api/v1/project/2f1c121257cc44acb1241aa640c4d266/badge.svg
  :target: https://www.quantifiedcode.com/app/project/2f1c121257cc44acb1241aa640c4d266
  :alt: Code issues

Widgetastic - Making testing of UIs **fantastic**.

Written originally by Milan Falesnik (mfalesni@redhat.com, http://www.falesnik.net/) and
other contributors since 2016.

Licensed under Apache license, Version 2.0

*WARNING:* Until this library reaches v1.0, the interfaces may change!

Currently the documentation build on RTD is broken. You can generate and browse it like
this:

.. code-block:: bash

    cd widgetastic.core/    # Your git repository's root folder
    tox -e docs
    google-chrome build/htmldocs/index.html   # Or a browser of your choice

I have set up `my Jenkins <https://up.falesnik.net/wt-doc/>`_ to build docs on new releases while
RTD can't build the documentation.


Projects using widgetastic
--------------------------
- ManageIQ integration_tests: https://github.com/ManageIQ/integration_tests

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
- Run ``tox`` to ensure your change does not break other things
- Push
- Create a pull request
