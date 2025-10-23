.. _guidelines:

===========
Guidelines
===========

This document outlines essential guidelines for using Widgetastic.core effectively. Anyone using this library should consult these guidelines to ensure they are following best practices and not violating any framework conventions.

.. note::
   These guidelines are based on the framework's architecture and design principles. Following them ensures your code is maintainable, reliable, and consistent with the framework's expectations.

While Writing New Widgets
==========================

Read/Fill Interface
-------------------

All widgets should implement the standard read/fill interface:

**read() Method**

- **Return Type**: ``object``
- **Compatibility**: Whatever is returned from ``read()`` must be compatible with ``fill()``
- **Round-trip Requirement**: ``obj.fill(obj.read())`` must work at any time
- **Exception Handling**: ``read()`` may throw a ``DoNotReadThisWidget`` exception if reading the widget is pointless (e.g., in current form state it is hidden). This is achieved by invoking the ``do_not_read_this_widget()`` function.

**fill() Method**

- **Return Type**: ``True|False``
- **Input Compatibility**: ``fill(value)`` must be able to ingest whatever was returned by ``read()``
- **Round-trip Requirement**: ``obj.fill(obj.read())`` must work at any time
- **Exception**: An exception to this rule is only acceptable in the case where this 1:1 direct mapping would cause severe inconvenience
- **Return Value Rules**:
  - ``fill`` MUST return ``True`` if it changed anything during filling
  - ``fill`` MUST return ``False`` if it has not changed anything during filling

**Optional Methods**

- Any of these methods may be omitted if it is appropriate based on the UI widget interactions
- It is recommended that all widgets have at least ``read()`` but in cases like buttons where you don't read or fill, it is understandable that there is neither of those

**Example**

.. code-block:: python

    class MyWidget(Widget):
        def read(self):
            """Read current widget value."""
            return self.browser.text(self)

        def fill(self, value):
            """Fill widget with value."""
            current = self.read()
            if value == current:
                return False  # No change
            self.browser.fill(self, str(value))
            return True  # Changed

        # Verify round-trip works
        widget = MyWidget(browser, locator="#my-widget")
        value = widget.read()
        widget.fill(value)  # Should work without errors

Widget Initialization
---------------------

**Signature Pattern**

The ``__init__`` must follow the standard pattern:

- If you want your widget to accept parameters ``a`` and ``b``, you must create signature like this:
  - ``__init__(self, parent, a, b, logger=None)``

**Parent Class Initialization**

- The first line of the widget must call out to the root class in order to set things up properly:
  - ``Widget.__init__(self, parent, logger=logger)``

**Example**

.. code-block:: python

    class CustomInput(Widget):
        def __init__(self, parent, input_id, placeholder=None, logger=None):
            """Initialize custom input widget."""
            Widget.__init__(self, parent, logger=logger)
            self.input_id = input_id
            self.placeholder = placeholder

        def __locator__(self):
            return f"#input-{self.input_id}"

Locator Definition
------------------

**Requirement**

- Widgets MUST define ``__locator__`` in some way
- Views do not have to, but can do it to fence the element lookup in its child widgets

**Locator Return Types**

You can write ``__locator__`` method yourself. It should return anything that can be turned into a locator by ``smartloc.Locator``:

- ``'#foo'`` (CSS selector)
- ``'//div[@id="foo"]'`` (XPath)
- ``smartloc.Locator(xpath='...')`` (Locator object)
- et cetera

**Important Restrictions**

- ``__locator__`` MUST NOT return ``ElementHandle`` instances to prevent stale element issues

**Automatic Generation**

- If you use a ``ROOT`` class attribute, especially in combination with ``ParametrizedLocator``, a ``__locator__`` is generated automatically for you

**Example**

.. code-block:: python

    class MyWidget(Widget):
        # Option 1: Using ROOT attribute (automatic __locator__)
        ROOT = "#my-widget"

        # Option 2: Custom __locator__ method
        def __locator__(self):
            return f"#widget-{self.widget_id}"

        # Option 3: Using ParametrizedLocator
        ROOT = ParametrizedLocator(".//div[@id={@widget_id|quote}]")

State Management
----------------

**General Principle**

- Widgets should keep its internal state in reasonable size Ideally none, but e.g., caching header names of tables is perfectly acceptable
- Saving ``ElementHandle`` instances in the widget instance is not recommended

**Caching Guidelines**

- Think about what to cache and when to invalidate
- Never store ``ElementHandle`` objects
- Try to shorten the lifetime of any single ``ElementHandle`` as much as possible
- This will help against stale element issues


Logging
-------

**Standard Practice**

- Widgets shall log using ``self.logger``
- That ensures the log message is prefixed with the widget name and location
- This gives more insight about what is happening

**Example**

.. code-block:: python

    class MyWidget(Widget):
        def fill(self, value):
            self.logger.info(f"Filling widget with value: {value}")
            # ... fill logic ...
            self.logger.debug(f"Fill completed, new value: {self.read()}")

When Using Widgets (and Views)
================================

WidgetDescriptor and Lazy Creation
-----------------------------------

**Understanding WidgetDescriptor**

- Bear in mind that when you do ``MySuperWidget('foo', 'bar')`` in python interpreter, you are not getting an actual widget object, but rather an instance of ``WidgetDescriptor``

**Creating Real Widget Instances**

- In order to create a real widget object, you have to have widgetastic ``Browser`` instance around and prepend it to the arguments
- The call to create a real widget instance would look like:
  - ``MySuperWidget(wt_browser, 'foo', 'bar')``

**Automatic Browser Prepending**

- This browser prepending is done automatically by ``WidgetDescriptor`` when you access it on a ``View`` or another ``Widget``
- All of these means that the widget objects are created lazily

**Example**

.. code-block:: python

    class MyView(View):
        my_widget = MySuperWidget('foo', 'bar')

    view = MyView(browser)
    # When you access view.my_widget, WidgetDescriptor automatically:
    # 1. Prepends browser to arguments
    # 2. Creates the actual widget instance
    # 3. Returns the real widget object
    widget = view.my_widget  # Now it's a real widget instance

Nested Views
------------

**Filling and Reading**

- Views can be nested
- Filling and reading nested views is simple
- Each view is read/filled as a dictionary
- The required dictionary structure is exactly the same as the nested class structure

**Example**

.. code-block:: python

    class InnerView(View):
        field1 = TextInput("#field1")
        field2 = TextInput("#field2")

    class OuterView(View):
        inner = View.nested(InnerView)
        other_field = TextInput("#other")

    view = OuterView(browser)
    # Fill nested view
    view.fill({
        'inner': {
            'field1': 'value1',
            'field2': 'value2'
        },
        'other_field': 'value3'
    })

Widget Order and View.nested Decorator
--------------------------------------

**Order Preservation**

- Views remember the order in which the Widgets were placed on it
- Each ``WidgetDescriptor`` has a sequential number on it
- This is used when filling or reading widgets, ensuring proper filling order

**Nested Views Exception**

- This would normally also apply to Views since they are also descendants of ``Widget``
- But since you are not instantiating the view when creating nested views, this mechanism does not work

**Solution: @View.nested Decorator**

- You can ensure the ``View`` gets wrapped in a ``WidgetDescriptor`` and therefore in correct order by placing a ``@View.nested`` decorator on the nested view

**Example**

.. code-block:: python

    class InnerView(View):
        field1 = TextInput(id="field1")
        field2 = TextInput(id="field2")

    class OuterView(View):
        @View.nested
        class inner(View):
            field1 = TextInput(id="field1")
            field2 = TextInput(id="field2")

        other_field = TextInput(id="other")

View Lifecycle Hooks
--------------------

**Optional Methods**

- Views can optionally define ``before_fill(values)`` and ``after_fill(was_change)``

**before_fill**

- Invoked right before filling gets started
- You receive the filling dictionary in the values parameter
- You can act appropriately (e.g., validation, preparation)

**after_fill**

- Invoked right after the fill ended
- ``was_change`` tells you whether there was any change or not
- Useful for post-fill actions (e.g., waiting for updates, logging)

**Example**

.. code-block:: python

    class MyView(View):
        field1 = TextInput(id="field1")
        field2 = TextInput(id="field2")

        def before_fill(self, values):
            """Called before filling starts."""
            self.logger.info(f"About to fill with: {values}")
            # Could validate values here

        def after_fill(self, was_change):
            """Called after filling completes."""
            if was_change:
                self.logger.info("View was successfully filled")
            else:
                self.logger.debug("No changes were made")

When Using Browser (also applies when writing Widgets)
=======================================================

Use Widgetastic Browser Methods
--------------------------------

**General Rule**

- Ensure you use the widgetastic Browser methods rather than direct Playwright Locator methods where possible

**Example**

- Instead of ``locator.text_content()`` use ``browser.text(locator)``
- This applies for all such circumstances
- These calls usually do not invoke more than their original counterparts
- They only invoke some workarounds if some known issue arises
- Check what the ``Browser`` (sub)class offers and if you miss something, create a PR

**Example**

.. code-block:: python

    # BAD: Direct Playwright method
    element = browser.element("#my-element")
    text = element.text_content()

    # GOOD: Widgetastic Browser method
    text = browser.text("#my-element")

Automatic Parent Resolution
----------------------------

**Simplified Syntax**

- You don't necessarily have to specify ``self.browser.element(..., parent=self)`` when you are writing a query inside a widget implementation
- Widgetastic figures this out and does it automatically

**Example**

.. code-block:: python

    class MyWidget(Widget):
        def get_child_text(self):
            # Widgetastic automatically uses self as parent
            return self.browser.text(".//span", parent=self)
            # Can also be written as:
            # return self.browser.text(".//span")  # parent=self is automatic

Method Arguments and Element Resolution
----------------------------------------

**Simplified Method Calls**

- Most of the methods that implement the getters, that would normally be on the element object, take an argument or two for themselves
- The rest of ``*args`` and ``**kwargs`` is shoved inside ``element()`` method for resolution
- So constructs like ``self.browser.get_attribute('id', self.browser.element('locator', parent=foo))`` are not needed
- Just write ``self.browser.get_attribute('id', 'locator', parent=foo)``
- Check the method definitions on the ``Browser`` class to see that

**Example**

.. code-block:: python

    # BAD: Nested element() call
    element = self.browser.element('locator', parent=foo)
    attr = self.browser.get_attribute('id', element)

    # GOOD: Direct method call
    attr = self.browser.get_attribute('id', 'locator', parent=foo)

Intelligent Element Selection
------------------------------

**Automatic Filtering**

- ``element()`` method tries to apply a rudimentary intelligence on the element it resolves
- If a locator resolves to a single element, it returns it
- If the locator resolves to multiple elements, it tries to filter out the invisible elements and return the first visible one
- If none of them is visible, it just returns the first one
- Under normal circumstances, standard Playwright resolution returns all matching elements

**Example**

.. code-block:: python

    # If multiple elements match, widgetastic automatically:
    # 1. Filters out invisible elements
    # 2. Returns the first visible one
    # 3. Falls back to first element if none are visible
    element = browser.element(".//button")  # Intelligent selection

Avoid Nested Locator Calls
---------------------------

**Important Rule**

- DO NOT use nested locator calls
- Use ``self.browser.element('locator', parent=element)`` instead
- This approach is safer and more consistent with the framework architecture

**Example**

.. code-block:: python

    # BAD: Nested locator calls
    parent = browser.element("#parent")
    child = parent.locator(".//child")  # Don't do this!

    # GOOD: Use browser.element with parent parameter
    parent = browser.element("#parent")
    child = browser.element(".//child", parent=parent)

Summary
=======

These guidelines ensure that your Widgetastic code is:

* **Consistent**: Follows framework conventions and patterns
* **Maintainable**: Easy to understand and modify
* **Reliable**: Avoids common pitfalls like stale element issues
* **Efficient**: Uses framework features optimally

Remember: *No current exceptions are to be taken as a precedent.* Always follow these guidelines unless there's a compelling reason documented in the framework itself.
