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

.. code-block:: python

    from widgetastic.widget import Text

    # In-line Initialization of Text widget
    main_title = Text(parent=browser, locator= ".//h1[@id='wt-core-title']")

    # Widget operations
    main_title.is_displayed        # True
    main_title.is_enabled          # True
    main_title.text                # "Widgetastic.Core - Testing Page"
    main_title.read()              # "Widgetastic.Core - Testing Page"

    non_existing_element = Text(browser, locator='.//div[@id="non-existing-element"]')
    non_existing_element.is_displayed        # False
    non_existing_element.read()              # NoSuchElementException


.. note::

   While inline widget initialization (as shown above) works for learning and debugging, production code should use View classes to organize widgets.
   Views provide better structure, reusability, and maintainability for real automation projects.


Input Widgets
==============

Widgetastic provides specialized widgets for some types of HTML input elements. Each input widget is optimized for its specific use case while maintaining a consistent interface.

**TextInput Widget**

The :py:class:`~widgetastic.widget.TextInput` widget handles standard text input elements like text, email, number, textarea, etc.

Basic TextInput Operations:

.. code-block:: python

    from widgetastic.widget import TextInput

    # Inline initialization for learning
    text_input = TextInput(parent=browser, id="input")

    # Widget operations
    text_input.is_displayed         # True
    text_input.is_enabled           # True
    text_input.fill("Hello World")  # True
    text_input.value                # "Hello World"
    text_input.read()               # "Hello World"


TextInput with Different Element Types

.. code-block:: python

    # Number input
    number_input = TextInput(parent=browser, locator='.//input[@id="input_number"]')
    number_input.fill("42")
    number_input.read()               # 42

    # Textarea (multi-line)
    textarea = TextInput(parent=browser, id="textarea_input")
    multiline_text = "Line 1\nLine 2\nLine 3"
    textarea.fill(multiline_text)
    textarea.read()

TextInput State Management

.. code-block:: python

    # Check if element exists and is accessible
    enabled_input = TextInput(parent=browser, id="input1")
    disabled_input = TextInput(parent=browser, name="input1_disabled")

    enabled_input.is_displayed     # True
    enabled_input.is_enabled       # True
    disabled_input.is_enabled      # False

    # Fill success checking
    enabled_input.fill("new value")   # True (value changed)
    # Try to fill same value - no change detected and return False
    enabled_input.fill("new value")   # False (no change)

.. note::
   **Read/Fill Interface Guidelines:**
   
   * The ``fill()`` method MUST return ``True`` if it changed anything, ``False`` if no change occurred
   * Whatever is returned from ``read()`` must be compatible with ``fill()``
   * Round-trip requirement: ``widget.fill(widget.read())`` must work at any time
   * This ensures widgets can be read and restored to their previous state reliably


**FileInput Widget**

The :py:class:`~widgetastic.widget.FileInput` widget handles file upload inputs.

.. code-block:: python

    from widgetastic.widget import FileInput

    file_input = FileInput(browser, id="fileinput")
    file_input.is_displayed        # True
    file_input.is_enabled          # True

    # File upload operations
    file_input.fill("/etc/resolv.conf")  # True


**ColourInput Widget**

The :py:class:`~widgetastic.widget.ColourInput` widget handles HTML5 color picker inputs.

.. code-block:: python

    from widgetastic.widget import ColourInput

    colour_input = ColourInput(browser, id="colourinput")

    # Color operations
    colour_input.fill("#ff0000")      # True (Red color)
    colour_input.read()               # "#ff0000"

    # Set different colors but with colour setter property.
    colour_input.colour = "#00ff00"  # (Green)
    colour_input.colour              # "#00ff00"


Checkbox Widget
================

The :py:class:`~widgetastic.widget.Checkbox` widget handles checkbox elements.


.. code-block:: python
    from widgetastic.widget import Checkbox

    enabled_checkbox = Checkbox(browser, id="input2")
    disabled_checkbox = Checkbox(browser, id="input2_disabled")

    # Check is_displayed and is_enabled
    enabled_checkbox.is_displayed       # True
    disabled_checkbox.is_displayed      # True

    enabled_checkbox.is_enabled         # True
    disabled_checkbox.is_enabled        # False

    # Filling  and reading checkboxes
    enabled_checkbox.fill(True)    # True (checked)
    enabled_checkbox.read()        # True
    enabled_checkbox.fill(False)   # True (unchecked)
    enabled_checkbox.read()        # False


Select Widget
=============

The :py:class:`~widgetastic.widget.Select` widget handles HTML select elements.

.. code-block:: python

    from widgetastic.widget import Select

    single_select = Select(browser, name="testselect1")
    multi_select = Select(browser, name="testselect2")

    # Reading selected values
    single_select.read()    # "Foo"
    single_select.value     # "Foo"

    # Get all available options
    single_select.all_options     # [Option(text='Foo', value='foo'), Option(text='Bar', value='bar')]

    # Select by visible text
    single_select.fill("Bar")    # True

    # Select by value
    single_select.fill(("by_value", "foo"))    # True

    # Multiple selection
    multi_select.fill(["Foo", "Baz"])  # True
    multi_select.read()                # ["Foo", "Baz"]


Image Widget
============

The :py:class:`~widgetastic.widget.Image` widget provides access to HTML image elements.

**Image Examples from Testing Page**

.. code-block:: python

    from widgetastic.widget import Image

    full_image = Image(browser, locator="#test-image-full")
    # Check image visibility
    full_image.is_displayed  # True

    # Accessing image attributes
    full_image.src      # "data:image/svg+xml,%3Csvg width='100' height='50' xmlns='http://www.w3.org/2000/svg'%3E%3Crect width='100' height='50' fill='%234CAF50'/%3E%3C/svg%3E"
    full_image.alt      # "Green test image"
    full_image.title    # "Image title"
