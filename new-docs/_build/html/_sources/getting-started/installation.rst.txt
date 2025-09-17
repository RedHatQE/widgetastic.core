============
Installation
============

Requirements
============

**Python Version**
   Widgetastic.core requires Python 3 (For specific versions please check pyproject.toml). We recommend using the latest stable version of Python.

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

.. code-block:: python

    # test_installation.py
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text

    class TestView(View):
        title = Text('title')

    def test_widgetastic():
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto('https://example.com')

            wt_browser = Browser(page)
            view = TestView(wt_browser)

            print(f"Page title: {view.title.text}")
            print("✅ Widgetastic is working correctly!")

            browser.close()

    if __name__ == "__main__":
        test_widgetastic()

Run the script:

.. code-block:: bash

    python test_installation.py

If you see "✅ Widgetastic is working correctly!" along with the page title, your installation is successful.


Optional Dependencies
=====================

For additional functionality, you can install optional dependencies:

**Documentation Building**

.. code-block:: bash

    pip install "widgetastic.core[docs]"

**Development Tools**

.. code-block:: bash

    pip install "widgetastic.core[dev]"

**Testing Dependencies**

.. code-block:: bash

    pip install "widgetastic.core[test]"

Next Steps
==========

Now that you have widgetastic.core installed:

1. :doc:`concepts` - Learn the core concepts and terminology
2. :doc:`first-steps` - Write your first widgetastic automation script
3. :doc:`../quickstart/index` - Jump into practical examples
