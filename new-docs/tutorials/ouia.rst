==========================
Open UI Automation (OUIA)
==========================

Widgetastic provides comprehensive support for `OUIA (Open UI Automation) <https://ouia.readthedocs.io>`_
compatible components. OUIA is a specification that standardizes component identification through
HTML data attributes, making automation more reliable and maintainable.

In order to start creating an OUIA compatible widget or view, just inherit from the appropriate base class.
Children classes should define the ``OUIA_COMPONENT_TYPE`` class attribute to match the value of
``data-ouia-component-type`` attribute of the root HTML element.

The key advantage is that **you don't need to specify any locator**. If a component complies with OUIA
spec, the locator can be automatically generated from the OUIA attributes.

OUIA Base Classes
=================

Widgetastic provides three base classes for OUIA support:

* :py:class:`widgetastic.ouia.OUIABase`: Core OUIA functionality
* :py:class:`widgetastic.ouia.OUIAGenericWidget`: Base for OUIA-compatible widgets
* :py:class:`widgetastic.ouia.OUIAGenericView`: Base for OUIA-compatible views

Creating OUIA Widgets
======================

Consider this HTML excerpt:

.. code-block:: html

    <button data-ouia-component-type="PF/Button" data-ouia-component-id="This is a button">
        This is a button
    </button>

According to OUIA, this is a ``Button`` component in the ``PF`` namespace with id ``This is a button``.
Based on that information, we can create the following widget:

.. code-block:: python

    from widgetastic.ouia import OUIAGenericWidget

    class Button(OUIAGenericWidget):
        """OUIA Button widget following PF (PatternFly) namespace."""
        OUIA_COMPONENT_TYPE = "PF/Button"

As you can see, you don't need to specify any locator. The only argument you may provide is ``component_id``.

After that, you can add this class to some view and use it in automation:

.. code-block:: python

    from widgetastic.widget import View

    class Details(View):
        ROOT = ".//div[@id='some_id']"
        button = Button(component_id="This is a button")

    view = Details(browser)
    view.button.click()

Creating OUIA Views
===================

OUIA views are containers that use OUIA attributes for identification. They're perfect for
organizing multiple OUIA widgets together.

.. code-block:: python

    from widgetastic.ouia import OUIAGenericView

    class TestView(OUIAGenericView):
        """OUIA view containing multiple OUIA widgets."""
        OUIA_COMPONENT_TYPE = "TestView"
        OUIA_ID = "ouia"  # Optional: default component_id for the view

        button = Button(component_id="This is a button")
        # ... other widgets

    view = TestView(browser)

    # OUIA_COMPONENT_TYPE is used to generate ROOT for this view. which will limit scope of this view to only OUIA widgets with type "TestView"
    print(f"ROOT locator for this view: {view.ROOT.locator}")
    view.button.click()

Existing OUIA Widgets
=====================

Widgetastic provides some basic pre-built OUIA widgets that you can use directly:

* :py:class:`widgetastic.ouia.input.TextInput` - OUIA version of TextInput widget
* :py:class:`widgetastic.ouia.checkbox.Checkbox` - OUIA version of Checkbox widget
* :py:class:`widgetastic.ouia.text.Text` - OUIA version of Text widget

OUIA Safety Attribute
=====================

The ``data-ouia-safe`` attribute indicates whether a component is in a static state (no animations).
This is useful for waiting until components are ready for interaction.

.. code-block:: python

    button = OUIAGenericWidget(parent=browser, component_id="This is a button", component_type="PF/Button")
    button.is_safe  # False (button has data-ouia-safe="false")

    select = OUIAGenericWidget(parent=browser, component_id="some_id", component_type="PF/Select")
    select.is_safe  # True (select has data-ouia-safe="true")

Complete Example
================

Here's a complete example using OUIA widgets from the testing page:

.. code-block:: python

    from widgetastic.ouia import OUIAGenericView, OUIAGenericWidget
    from widgetastic.ouia.checkbox import Checkbox
    from widgetastic.ouia.input import TextInput
    from widgetastic.ouia.text import Text

    # Define custom OUIA widget
    class Button(OUIAGenericWidget):
        OUIA_COMPONENT_TYPE = "PF/Button"

    # Create comprehensive OUIA view
    class TestView(OUIAGenericView):
        OUIA_COMPONENT_TYPE = "TestView"
        OUIA_ID = "ouia"

        button = Button(component_id="This is a button")
        text = Text(component_id="unique_id", component_type="Text")
        text_input = TextInput(component_id="unique_id", component_type="TextInput")
        checkbox = Checkbox(component_id="unique_id", component_type="CheckBox")

    # Use the view
    view = TestView(browser)
    view.button.click()
    print("Button clicked successfully")

    view.text_input.fill("Test")
    print(f"Text input value: {view.text_input.read()}")

    view.checkbox.fill(True)
    print(f"Checkbox checked: {view.checkbox.read()}")


Key Points
==========

* Use ``OUIAGenericWidget`` for individual components (buttons, inputs, etc.)
* Use ``OUIAGenericView`` for container components (forms, sections, selects)
* Define ``OUIA_COMPONENT_TYPE`` in widget classes to match ``data-ouia-component-type``
* Use ``component_id`` parameter to match ``data-ouia-component-id`` attribute
* No manual locators needed - they're automatically generated
* Component types and IDs are case-sensitive - match exactly
