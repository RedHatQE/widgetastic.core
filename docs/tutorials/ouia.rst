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

.. literalinclude:: ../examples/ouia/creating_ouia_widgets.py
   :language: python
   :linenos:

Creating OUIA Views
===================

OUIA views are containers that use OUIA attributes for identification. They're perfect for
organizing multiple OUIA widgets together.

.. literalinclude:: ../examples/ouia/creating_ouia_views.py
   :language: python
   :linenos:

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

.. literalinclude:: ../examples/ouia/ouia_safety_attribute.py
   :language: python
   :linenos:

Complete Example
================

Here's a complete example using OUIA widgets from the testing page:

.. literalinclude:: ../examples/ouia/ouia_complete_example.py
   :language: python
   :linenos:


Key Points
==========

* Use ``OUIAGenericWidget`` for individual components (buttons, inputs, etc.)
* Use ``OUIAGenericView`` for container components (forms, sections, selects)
* Define ``OUIA_COMPONENT_TYPE`` in widget classes to match ``data-ouia-component-type``
* Use ``component_id`` parameter to match ``data-ouia-component-id`` attribute
* No manual locators needed - they're automatically generated
* Component types and IDs are case-sensitive - match exactly
