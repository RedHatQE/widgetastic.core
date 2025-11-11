================
IFrame Handling
================

This tutorial demonstrates how to work with iframes in Widgetastic.core using the framework's test pages.
You'll learn to navigate iframe hierarchies, switch contexts, and handle nested frame structures using ``iframe_page.html`` and ``iframe_page2.html``.

.. note::
   **Prerequisites**: Basic widgets tutorial
   **Test Pages Used**: ``testing/html/testing_page.html``, ``iframe_page.html``, ``iframe_page2.html``

Learning Objectives
===================

* ✅ Understand iframe context switching
* ✅ Navigate nested iframe hierarchies
* ✅ Handle iframe isolation and cross-context access

Understanding IFrames in Web Automation
=======================================

IFrames (inline frames) embed another HTML document within the current page.
They create isolated contexts that require special handling in web automation:

* **Context Isolation**: Elements inside iframes aren't accessible from the main page context
* **Frame Switching**: You must explicitly switch context to interact with iframe content
* **Nested Frames**: IFrames can contain other iframes, creating complex hierarchies
* **Security Boundaries**: Cross-origin iframes may have additional restrictions


Basic IFrame Access
===================

The testing page contains an iframe that loads ``iframe_page.html``. Here's how to access it:

**Simple IFrame View**

.. literalinclude:: ../examples/iframe-handling/basic_iframe.py
   :language: python
   :linenos:

Nested IFrame Navigation
========================

The iframe testing setup includes nested iframes. Here's how to handle complex hierarchies:

**Nested IFrame Structure**

.. literalinclude:: ../examples/iframe-handling/nested_iframe.py
   :language: python
   :linenos:

IFrame Context Isolation
========================

IFrame contexts are completely isolated. Elements in different frames cannot directly interact:

**Demonstrating Context Isolation**

.. literalinclude:: ../examples/iframe-handling/context_isolation.py
   :language: python
   :linenos:
