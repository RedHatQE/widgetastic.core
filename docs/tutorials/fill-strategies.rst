================
Fill Strategies
================

This tutorial explains Widgetastic's built-in fill strategies for handling form filling operations. You'll learn about ``DefaultFillViewStrategy`` and ``WaitFillViewStrategy``, how they work, and when to use each one.

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Understand how fill strategies work in Widgetastic
* ✅ Learn when to use ``DefaultFillViewStrategy`` vs ``WaitFillViewStrategy``
* ✅ Use ``respect_parent`` for strategy inheritance in nested views

Understanding Fill Strategies
==============================

Fill strategies control how widgets are filled in a View. When you call ``view.fill(values)``, the view uses its configured fill strategy to determine:

* The order widgets should be filled
* Whether to wait for widgets to appear before filling
* How to handle errors during filling
* What to log during fill operations

Widgetastic provides two built-in fill strategies:

**Built-in Fill Strategies**

* **DefaultFillViewStrategy**: Fills widgets sequentially without waiting
* **WaitFillViewStrategy**: Waits for each widget to be displayed before filling

DefaultFillViewStrategy
========================

``DefaultFillViewStrategy`` is the default strategy used by all Views. It fills widgets in the order they appear in the view's ``widget_names`` attribute.

**Key Features:**

* Fills widgets sequentially in order
* No waiting for widgets to appear
* Skips widgets with ``None`` values
* Warns about extra keys that don't match widgets
* Handles widgets without fill methods gracefully
* Returns ``True`` if any widget value changed

**Basic Usage:**

.. literalinclude:: ../examples/fill-strategies/default_fill_strategy_examples.py
   :language: python
   :start-after: # Example: Basic Usage
   :end-before: # End Example: Basic Usage


**Filtering None Values:**

Values set to ``None`` are automatically filtered out:

.. literalinclude:: ../examples/fill-strategies/default_fill_strategy_examples.py
   :language: python
   :start-after: # Example: Filtering None Values
   :end-before: # End Example: Filtering None Values


**Handling Extra Keys:**

The strategy warns about keys in your fill data that don't correspond to widgets:

.. literalinclude:: ../examples/fill-strategies/default_fill_strategy_examples.py
   :language: python
   :start-after: # Example: Handling Extra Keys
   :end-before: # End Example: Handling Extra Keys

**Handling Widgets Without Fill Methods:**

Widgets that don't have a ``fill()`` method are skipped with a warning:

.. literalinclude:: ../examples/fill-strategies/default_fill_strategy_examples.py
   :language: python
   :start-after: # Example: Handling Widgets Without Fill
   :end-before: # End Example: Handling Widgets Without Fill

**Change Detection:**

The strategy returns ``True`` only if at least one widget value actually changed:

.. literalinclude:: ../examples/fill-strategies/default_fill_strategy_examples.py
   :language: python
   :start-after: # Example: Change Detection
   :end-before: # End Example: Change Detection


WaitFillViewStrategy
====================

``WaitFillViewStrategy`` extends ``DefaultFillViewStrategy`` by adding wait functionality. Before filling each widget, it waits for the widget to be displayed.

**Key Features:**
* Inherits all features from ``DefaultFillViewStrategy``
* Waits for each widget to be displayed before filling
* Configurable wait timeout per widget
* Ideal for dynamic content that appears after user interactions
* Handles Single Page Applications (SPAs) with async loading

**When to Use:**

Use ``WaitFillViewStrategy`` when:
* Widgets may appear dynamically after page load
* Forms have conditional fields that appear based on selections
* Widgets are inside iframes that load slowly
* Forms have progressive revelation of fields

**Basic Usage:**

.. literalinclude:: ../examples/fill-strategies/wait_fill_strategy_examples.py
   :language: python
   :start-after: # Example: Basic Usage
   :end-before: # End Example: Basic Usage

**Custom Wait Timeout:**

Configure how long to wait for each widget:

.. literalinclude:: ../examples/fill-strategies/wait_fill_strategy_examples.py
   :language: python
   :start-after: # Example: Custom Wait Timeout
   :end-before: # End Example: Custom Wait Timeout


Strategy Inheritance with respect_parent
========================================

Both fill strategies support the ``respect_parent`` parameter, which controls whether child views inherit the parent's fill strategy.

**Understanding respect_parent:**

* ``respect_parent=False`` (default): Child views get their own default strategy
* ``respect_parent=True``: Child views inherit parent's strategy

**Example Without Inheritance:**

.. literalinclude:: ../examples/fill-strategies/strategy_inheritance_examples.py
   :language: python
   :start-after: # Example: Without Inheritance
   :end-before: # End Example: Without Inheritance

**Example With Inheritance:**

.. literalinclude:: ../examples/fill-strategies/strategy_inheritance_examples.py
   :language: python
   :start-after: # Example: With Inheritance
   :end-before: # End Example: With Inheritance



Key takeaways:

* Views automatically use ``DefaultFillViewStrategy`` if none specified
* Use ``WaitFillViewStrategy`` for dynamic content that may not be immediately available
* Fill strategies handle error cases gracefully (skipping widgets without fill methods)
* Strategies respect widget order and filter None values automatically


This completes the fill strategies tutorial. You now understand how to use Widgetastic's built-in fill strategies effectively in your automation tests.
