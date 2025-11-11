=============
Basic Widgets
=============

This comprehensive tutorial demonstrates all the fundamental widgets in Widgetastic.core using the framework's real testing pages.
You'll learn to interact with web elements through practical examples using ``testing/html/testing_page.html`` - the same file used to test the framework itself.

In widgetastic, a widget represents any interactive or non-interactive element on a web page.
Unlike traditional automation approaches that work directly with raw elements, widgets provide a higher-level, object-oriented abstraction.

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Basic understanding of core widget
* ✅ Understand the widget read/fill interface
* ✅ Handle widget state and validation


Text Widget
============

The :py:class:`~widgetastic.widget.Text` widget extracts text content from web element.

**Basic Text Widget Examples**

.. literalinclude:: ../examples/basic-widgets/text_widget_basic.py
   :language: python
   :linenos:


.. note::

   While inline widget initialization (as shown above) works for learning and debugging, production code should use View classes to organize widgets.
   Views provide better structure, reusability, and maintainability for real automation projects.


Input Widgets
==============

Widgetastic provides specialized widgets for some types of HTML input elements. Each input widget is optimized for its specific use case while maintaining a consistent interface.

**TextInput Widget**

The :py:class:`~widgetastic.widget.TextInput` widget handles standard text input elements like text, email, number, textarea, etc.

Basic TextInput Operations:

.. literalinclude:: ../examples/basic-widgets/textinput_basic.py
   :language: python
   :linenos:


TextInput with Different Element Types

.. literalinclude:: ../examples/basic-widgets/textinput_different_types.py
   :language: python
   :linenos:

TextInput State Management

.. literalinclude:: ../examples/basic-widgets/textinput_state_management.py
   :language: python
   :linenos:

.. note::
   **Read/Fill Interface Guidelines:**

   * The ``fill()`` method MUST return ``True`` if it changed anything, ``False`` if no change occurred
   * Whatever is returned from ``read()`` must be compatible with ``fill()``
   * Round-trip requirement: ``widget.fill(widget.read())`` must work at any time
   * This ensures widgets can be read and restored to their previous state reliably


**FileInput Widget**

The :py:class:`~widgetastic.widget.FileInput` widget handles file upload inputs.

.. literalinclude:: ../examples/basic-widgets/fileinput.py
   :language: python
   :linenos:


**ColourInput Widget**

The :py:class:`~widgetastic.widget.ColourInput` widget handles HTML5 color picker inputs.

.. literalinclude:: ../examples/basic-widgets/colourinput.py
   :language: python
   :linenos:


Checkbox Widget
================

The :py:class:`~widgetastic.widget.Checkbox` widget handles checkbox elements.

.. literalinclude:: ../examples/basic-widgets/checkbox.py
   :language: python
   :linenos:


Select Widget
=============

The :py:class:`~widgetastic.widget.Select` widget handles HTML select elements.

.. literalinclude:: ../examples/basic-widgets/select_widget.py
   :language: python
   :linenos:


Image Widget
============

The :py:class:`~widgetastic.widget.Image` widget provides access to HTML image elements.

**Image Examples from Testing Page**

.. literalinclude:: ../examples/basic-widgets/image.py
   :language: python
   :linenos:
