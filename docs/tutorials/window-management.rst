==================
Window Management
==================

This tutorial demonstrates window and popup management in Widgetastic.core using the framework's test pages. You'll learn to handle multiple browser windows, tabs, and popups using ``popup_test_page.html`` and ``external_test_page.html``.

.. note::
   **Prerequisites**: Basic widgets tutorial
   **Test Pages Used**: ``popup_test_page.html``, ``external_test_page.html``, ``testing_page.html``

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Understand the WindowManager system
* ✅ Handle popup windows and new tabs
* ✅ Switch between multiple browser contexts
* ✅ Manage browser lifecycle and cleanup
* ✅ Handle cross-page automation workflows

Setting Up Window Management
============================

.. literalinclude:: ../examples/window-management/basic_windows_management.py
   :language: python
   :start-after: # Setup: Basic Windows Management
   :end-before: # End of Setup

Basic Window Operations
=======================

The WindowManager provides methods for creating and managing multiple browser windows:

**Creating New Windows**

.. literalinclude:: ../examples/window-management/basic_windows_management.py
   :language: python
   :start-after: # Example: Creating New Windows
   :end-before: # End of Example: Creating New Windows

**Switching Between Windows**

.. literalinclude:: ../examples/window-management/basic_windows_management.py
   :language: python
   :start-after: # Example: Switching Between Windows
   :end-before: # End of Example: Switching Between Windows


Handling Popups and New Tabs
============================

Manage popup windows and new tabs created by JavaScript. Widgetastic provides two approaches:
reliable detection using ``expect_new_page()`` context manager, and automatic detection via
``all_browsers`` property.

**Reliable Popup Detection with `expect_new_page()`**

The recommended approach for handling popups and new tabs is using the ``expect_new_page()``
context manager. This method uses Playwright's native ``expect_page()`` to reliably wait for
and capture new pages opened by JavaScript or links.

.. literalinclude:: ../examples/window-management/handling_popups.py
   :language: python
   :start-after: # Example: Handling Popups and New Tabs
   :end-before: # End of Example: Handling Popups and New Tabs


**Working with `all_browsers` Property**

The ``all_browsers`` property provides automatic cleanup and best-effort detection of new pages.
It's useful for listing all active browsers, but for reliable popup detection, use ``expect_new_page()``.

.. literalinclude:: ../examples/window-management/handling_popups.py
   :language: python
   :start-after: # Example: Working with all_browsers Property
   :end-before: # End of Example: Working with all_browsers Property
