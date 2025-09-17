===========================
Widgetastic.Core Documentation
===========================

.. image:: https://img.shields.io/pypi/pyversions/widgetastic.core.svg?style=flat
    :target: https://pypi.org/project/widgetastic.core
    :alt: Python supported versions

.. image:: https://badge.fury.io/py/widgetastic.core.svg
    :target: https://pypi.org/project/widgetastic.core

.. image:: https://github.com/RedHatQE/widgetastic.core/workflows/%F0%9F%95%B5%EF%B8%8F%20Test%20suite/badge.svg?branch=master
    :target: https://github.com/RedHatQE/widgetastic.core/actions?query=workflow%3A%22%F0%9F%95%B5%EF%B8%8F+Test+suite%22

**Making testing of UIs fantastic.**

Widgetastic is a Python library designed to abstract web UI widgets into a nice object-oriented layer.
This library includes the core classes and some basic widgets that are universal enough to exist in this
core repository.

Built on top of Microsoft's **Playwright**, Widgetastic provides a robust, modern approach to web UI automation
that handles the complexities of modern web applications while maintaining clean, readable test code.

.. note::
   This documentation covers widgetastic.core, the foundation library. For framework-specific widgets
   (like those for PatternFly, Bootstrap, etc.), check out the ecosystem of widgetastic extensions.

Why Widgetastic?
================

**🎯 Widget-Focused Approach**
   Model your UI components as reusable widgets with consistent read/fill interfaces

**🚀 Built on Playwright**
   Leverage the speed, reliability, and modern web support of Microsoft Playwright

**🧩 Intelligent Element Selection**
   Automatically finds visible, interactable elements when multiple matches exist

**📊 Robust Text Handling**
   Reliable text extraction from any element, regardless of CSS styling or positioning

**⚡ Smart Locators**
   Automatic detection of CSS, XPath, and other locator types with Playwright compatibility

**🔄 Version Picking**
   Handle UI changes across product versions with intelligent widget selection

**🎭 Advanced Views**
   Support for parametrized, conditional, and nested views for complex UI patterns

Quick Example
=============

.. code-block:: python

    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput, Button

    class LoginView(View):
        username = TextInput(name='username')
        password = TextInput(name='password')
        submit = Button('Log In')
        message = Text('.flash-message')

    # Initialize with Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        wt_browser = Browser(page)

        # Use the view
        login = LoginView(wt_browser)
        login.fill({
            'username': 'admin',
            'password': 'secret'
        })
        login.submit.click()

        if login.message.is_displayed:
            print(f"Login result: {login.message.text}")

Documentation Contents
======================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting-started/installation
   getting-started/concepts
   getting-started/first-steps

.. toctree::
   :maxdepth: 2
   :caption: Quick Start

   quickstart/index
   quickstart/basic-example
   quickstart/common-patterns

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   tutorials/index
   tutorials/basic-widgets
   tutorials/views-and-navigation
   tutorials/browser-methods
   tutorials/fill-strategies
   tutorials/advanced-widgets
   tutorials/iframe-handling
   tutorials/window-management
   tutorials/ouia-automation
   tutorials/version-picking
   tutorials/custom-widgets

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   api-reference/index

Community and Support
======================

* **GitHub Repository**: `RedHatQE/widgetastic.core <https://github.com/RedHatQE/widgetastic.core>`_
* **Issue Tracker**: `Report bugs and request features <https://github.com/RedHatQE/widgetastic.core/issues>`_
* **PyPI Package**: `widgetastic.core <https://pypi.org/project/widgetastic.core/>`_

Projects using Widgetastic
===========================

* ManageIQ `integration_tests <https://github.com/ManageIQ/integration_tests>`_
* Satellite `airgun <https://github.com/SatelliteQE/airgun>`_
* Cloud Services (insights-qe)
* Windup `integration_test <https://github.com/windup/windup_integration_test>`_

License
=======

Licensed under Apache License, Version 2.0

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
