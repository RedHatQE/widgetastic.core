==============================
Widgetastic.Core Documentation
==============================

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

Features
========

**Widget-Focused Approach**
   Individual interactive and non-interactive elements on web pages are represented as widgets;
   classes with defined behaviour that model your UI components as reusable objects with consistent
   read/fill interfaces. A good candidate for a widget might be something like a custom HTML button.

**View Organization**
   Widgets are grouped on Views. A View descends from the Widget class but is specifically designed
   to hold other widgets. Views can be nested, and they can define their root locators that are
   automatically honoured in element lookup for child widgets. This provides structure and context
   for organizing complex pages.

**Read/Fill Interface**
   All Widgets (including Views because they descend from them) have a read/fill interface useful
   for filling in forms etc. This interface works recursively. Widgets defined on Views are read/filled
   in the exact order that they were defined, making form automation straightforward and predictable.

**Built on Playwright**
   Includes a wrapper around Playwright functionality that tries to make the experience as hassle-free
   as possible. Leverage the speed, reliability, and modern web support of Microsoft Playwright with
   customizable hooks and built-in network activity monitoring.

**Intelligent Element Selection**
   Automatically finds visible, interactable elements when multiple matches exist. Smart locator
   detection supports CSS, XPath, and other locator types with Playwright compatibility, reducing
   the need for complex selector strategies.

**Robust Text Handling**
   Reliable text extraction from any element, regardless of CSS styling or positioning. Handles
   complex DOM structures and edge cases that traditional automation approaches struggle with.

**Advanced View Patterns**
   Supports :ref:`parametrized-views` for dynamic content and :ref:`switchable-conditional-views` for
   adaptive UIs. Handle complex UI structures with elegant, maintainable code.

**Version Picking**
   Supports :ref:`version-picking` to handle UI changes across product versions with intelligent
   widget selection. Write version-agnostic tests that adapt automatically to different UI versions.

**Object Support**
   Supports automatic :ref:`constructor-object-collapsing` for objects passed into widget constructors,
   enabling flexible, dynamic widget creation and form filling.

**Modern Python Support**
   Modern Python versions (specified in pyproject.toml) are officially supported and unit-tested in CI.
   Built with modern Python features and best practices in mind.

What This Project Does NOT Do
==============================

**Complete Testing Solution**
   In the spirit of modularity, we have intentionally designed our testing system to be modular, so if a
   different team likes one library, but wants to do other things a different way, the system does not
   stand in their way.

**UI Navigation**
   As per the previous point, it is up to you what you use for navigation. In CFME QE, we use a library
   called `navmazing <https://pypi.python.org/pypi/navmazing>`_, which is an evolution of the system
   we used before. You can devise your own system, use ours, or adapt something else.

**UI Models Representation**
   Doing nontrivial testing usually requires some sort of representation of the stuff in the product in
   the testing system. Usually, people use classes and instances of these with their methods corresponding
   to the real actions you can do with the entities in the UI. Widgetastic offers integration for such
   functionality, but does not provide any framework to use.

**Test Execution**
   We use pytest to drive our testing system. If you put the two previous points together and have a
   system of representing, navigating and interacting, then writing simple boilerplate code to make the
   system's usage from pytest straightforward is the last and possibly simplest thing to do.

Quick Example
=============

.. code-block:: python

    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput

    class LoginView(View):
        username = TextInput(name='username')
        password = TextInput(name='password')
        submit = Text(locator='.//div[text()="Log In"]')
        message = Text(locator='.//div[contains(@class, "flash-message")]')

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
        login.submit.click()  # Text widget inherits ClickableMixin so able to click.

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
   :caption: Tutorials

   tutorials/index
   tutorials/basic-widgets
   tutorials/views
   tutorials/fill-strategies
   tutorials/table-widget
   tutorials/iframe-handling
   tutorials/window-management
   tutorials/version-picking
   tutorials/ouia
   tutorials/guidelines

.. Uncomment when API reference is ready
.. .. toctree::
..    :maxdepth: 3
..    :caption: API Reference
..
..    api-reference/index

Community and Support
======================

* **GitHub Repository**: `RedHatQE/widgetastic.core <https://github.com/RedHatQE/widgetastic.core>`_
* **Issue Tracker**: `Report bugs and request features <https://github.com/RedHatQE/widgetastic.core/issues>`_
* **PyPI Package**: `widgetastic.core <https://pypi.org/project/widgetastic.core/>`_

Projects using Widgetastic
===========================

* ManageIQ `integration_tests <https://github.com/ManageIQ/integration_tests>`_
* Satellite `airgun <https://github.com/SatelliteQE/airgun>`_
* console.redhat.com (insights-qe)
* Windup `integration_test <https://github.com/windup/windup_integration_test>`_

License
=======

Licensed under Apache License, Version 2.0

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
