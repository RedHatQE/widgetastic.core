=========
Tutorials
=========

Welcome to the Widgetastic.Core tutorials! These step-by-step guides will take you from basic concepts to advanced
automation patterns. Each tutorial builds on the previous ones, so we recommend following them in order.

.. note::
   **Prerequisites**: Basic Python knowledge and familiarity with HTML/web concepts.

Complete Learning Path
======================

Follow these tutorials in order to learn widgetastic from foundation to advanced patterns. Each topic builds essential knowledge needed for the next level.

These comprehensive tutorials cover everything from basic widget usage to advanced automation patterns. Each tutorial includes working examples using the widgetastic test page.

**Ready to begin?** Start with Basic Widgets and follow the sequence.

**Support**: Most examples use elements from ``testing/html/testing_page.html``, with some tutorials using specialized pages (``iframe_page.html``, ``popup_test_page.html``) for specific features - you can test everything yourself!

Setting Up Your Environment
============================

**Browser Setup Using Testing Page**

All examples in these tutorials use a common browser setup defined as:

.. literalinclude:: ../examples/browser_setup.py
   :language: python
   :linenos:

This setup:

- Initializes Playwright with Chrome browser
- Navigates to the widgetastic testing page (``testing/html/testing_page.html``)
- Returns a ``Browser`` instance ready for use



Understanding the Testing Page Structure
=========================================

The ``testing_page.html`` contains comprehensive examples:

* **Element Visibility & State Testing**: Hidden/visible elements, interactive buttons with click tracking
* **Input Widgets & Controls**: Text inputs, file uploads, color pickers, editable content, textareas
* **Form Elements & Input States**: Mixed input types, radio button groups, enabled/disabled states
* **Table Widget Examples**: Standard tables with headers, tables without proper headers, embedded widgets
* **Image Widget Testing**: Images with src, alt, and title attributes
* **Locator & Element Finding**: Ambiguous vs specific locators, batch operations, element dimensions
* **Drag and Drop Testing**: Interactive drag/drop elements, sortable lists, position tracking
* **Advanced Table Operations**: Tables with embedded widgets, switchable content, dynamic content
* **Multiple TBody Table Structure**: Complex table structures with multiple tbody sections
* **View Testing**: Normal views, parametrized views, conditional switchable views
* **IFrame & Nested Content**: Embedded iframe testing
* **OUIA Integration**: Open UI Automation components with standardized attributes
