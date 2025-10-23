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

.. code-block:: python

    from widgetastic.utils import DefaultFillViewStrategy
    from widgetastic.widget import View, TextInput, Checkbox

    class BasicForm(View):
        input1 = TextInput(name="input1")
        input2 = TextInput(name="fill_with_2")
        checkbox1 = Checkbox(id="input2")

        # Explicitly set the default strategy (optional - it's the default)
        fill_strategy = DefaultFillViewStrategy()

    # Create view instance
    view = BasicForm(browser)

    # Fill multiple widgets at once
    changed = view.fill({
        'input1': 'test_value',
        'checkbox1': True
    })

    # Returns True if any widget value changed
    print(f"Fill changed values: {changed}")


**Filtering None Values:**

Values set to ``None`` are automatically filtered out:

.. code-block:: python

    values_with_none = {
        "input1": "value1",
        "input2": None,  # This will be filtered out
        "checkbox1": True
    }

    view.fill(values_with_none)


**Handling Extra Keys:**

The strategy warns about keys in your fill data that don't correspond to widgets:

.. code-block:: python

    import logging
    logging.basicConfig(level=logging.WARNING)

    values_with_extras = {
        "input1": "value1",
        "nonexistent_widget": "value2",  # This doesn't exist
        "another_extra": "value3"         # This doesn't exist either
    }

    # When filling, you'll get a warning:
    # "Extra values that have no corresponding fill fields passed: another_extra, nonexistent_widget"
    view.fill(values_with_extras)

**Handling Widgets Without Fill Methods:**

Widgets that don't have a ``fill()`` method are skipped with a warning:

.. code-block:: python

    from widgetastic.widget import Widget

    class NoFillWidget(Widget):
        """Widget without fill method."""
        pass

    class TestForm(View):
        input1 = TextInput(name="input1")
        no_fill_widget = NoFillWidget()
        input2 = TextInput(name="fill_with_2")

        fill_strategy = DefaultFillViewStrategy()

    view = TestForm(browser)

    # Fill operation will skip no_fill_widget and log a warning
    values = {
        "input1": "value1",
        "no_fill_widget": "will_skip",  # This will be skipped
        "input2": "value2"
    }

    # The fill succeeds for input1 and input2, but logs:
    # "Widget 'no_fill_widget' doesn't have fill method"
    result = view.fill(values)
    assert result is True  # Other widgets filled successfully

**Change Detection:**

The strategy returns ``True`` only if at least one widget value actually changed:

.. code-block:: python

    # First fill - values are new, so returns True
    result1 = view.fill({"input1": "test_value", "checkbox1": True})
    assert result1 is True

    # Second fill with same values - no change, returns False
    result2 = view.fill({"input1": "test_value", "checkbox1": True})
    assert result2 is False


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

.. code-block:: python

    from widgetastic.utils import WaitFillViewStrategy
    from widgetastic.widget import View, TextInput, Checkbox

    class DynamicForm(View):
        input1 = TextInput(name="input1")
        checkbox1 = Checkbox(id="input2")

        # Use wait strategy with default 5-second timeout
        fill_strategy = WaitFillViewStrategy()

    view = DynamicForm(browser)

    # Fill operation will wait for each widget to be displayed
    changed = view.fill({
        'input1': 'wait_test_value',
        'checkbox1': True
    })

**Custom Wait Timeout:**

Configure how long to wait for each widget:

.. code-block:: python

    class DynamicForm(View):
        input1 = TextInput(name="input1")
        input2 = TextInput(name="fill_with_2")
        checkbox1 = Checkbox(id="input2")

        # Custom 10-second timeout per widget
        fill_strategy = WaitFillViewStrategy(wait_widget="10s")

    view = DynamicForm(browser)

    # Each widget will wait up to 10 seconds to be displayed
    view.fill({"input1": "custom_wait_test"})


Strategy Inheritance with respect_parent
========================================

Both fill strategies support the ``respect_parent`` parameter, which controls whether child views inherit the parent's fill strategy.

**Understanding respect_parent:**

* ``respect_parent=False`` (default): Child views get their own default strategy
* ``respect_parent=True``: Child views inherit parent's strategy

**Example: Parent Without Inheritance:**

.. code-block:: python

    from widgetastic.utils import WaitFillViewStrategy, DefaultFillViewStrategy
    from widgetastic.widget import View, TextInput

    class ParentView(View):
        # Parent has wait strategy but doesn't respect parent
        fill_strategy = WaitFillViewStrategy(wait_widget="10s")  # respect_parent=False by default

        @View.nested
        class ChildView(View):
            input1 = TextInput(name="input1")
            # No fill_strategy specified

    parent_view = ParentView(browser)

    # Child gets its own default strategy (not parent's)
    assert isinstance(parent_view.fill_strategy, WaitFillViewStrategy)
    assert isinstance(parent_view.ChildView.fill_strategy, DefaultFillViewStrategy)


**Example: Parent With Inheritance:**

.. code-block:: python

    from widgetastic.utils import WaitFillViewStrategy, DefaultFillViewStrategy
    from widgetastic.widget import View, TextInput

    class ParentView(View):
        # Parent has wait strategy but doesn't respect parent
        fill_strategy = WaitFillViewStrategy(respect_parent=True, wait_widget="10s")  # respect_parent=False by default

        @View.nested
        class ChildView(View):
            input1 = TextInput(name="input1")
            # No fill_strategy specified

    parent_view = ParentView(browser)

    # Child gets its own default strategy (not parent's)
    assert isinstance(parent_view.fill_strategy, WaitFillViewStrategy)
    assert isinstance(parent_view.ChildView.fill_strategy, WaitFillViewStrategy)



Key takeaways:

* Views automatically use ``DefaultFillViewStrategy`` if none specified
* Use ``WaitFillViewStrategy`` for dynamic content that may not be immediately available
* Fill strategies handle error cases gracefully (skipping widgets without fill methods)
* Strategies respect widget order and filter None values automatically


This completes the fill strategies tutorial. You now understand how to use Widgetastic's built-in fill strategies effectively in your automation tests.
