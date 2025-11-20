============
Installation
============

Requirements
============

**Python Version**
   Widgetastic.core requires Python 3.10 or higher. We recommend using the latest stable version of Python.

**System Requirements**
   * Windows, macOS, or Linux
   * Internet connection for browser downloads (first-time setup)

Installation Methods
====================

PyPI Installation (Recommended)
--------------------------------

The easiest way to install widgetastic.core is using pip:

.. code-block:: bash

    pip install widgetastic.core

This will install the core library with all required dependencies.

Development Installation
------------------------

If you want to contribute to the project or need the latest development features:

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/RedHatQE/widgetastic.core.git
    cd widgetastic.core

    # Create virtual environment and activate it
    python -m venv .venv_wt
    source .venv_wt/bin/activate

    # Install in editable mode
    pip install -e .

    # Or with development dependencies
    pip install -e ".[dev]"



Playwright Setup
================

Widgetastic.core uses Playwright as its browser automation engine. After installing widgetastic.core,
you need to install browser binaries:

.. code-block:: bash

    # Install browser binaries (required for first-time setup)
    playwright install

    # Or install specific browsers only like chromium / firefox
    playwright install chromium

.. note::
   Browser installation may take several minutes and requires internet connectivity.

Verifying Installation
======================

Create a simple test script to verify everything is working:

.. literalinclude:: ../examples/getting-started/test_installation.py
   :language: python
   :linenos:

Run the script:

.. code-block:: bash

    python test_installation.py

If you see "✅ Widgetastic is working correctly!" along with the page title, your installation is successful.


Optional Dependencies
=====================

For additional functionality, you can install optional dependencies:

**Development Tools**

.. code-block:: bash

    pip install "widgetastic.core[dev]"

**Testing Dependencies**

.. code-block:: bash

    pip install "widgetastic.core[test]"

**Documentation Building**

.. code-block:: bash

    pip install "widgetastic.core[docs]"
