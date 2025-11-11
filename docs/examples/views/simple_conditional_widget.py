"""Simple Conditional Widget Registration Example

This example demonstrates registering a simple widget directly with ConditionalSwitchableView.
"""

from widgetastic.widget import ConditionalSwitchableView, View, TextInput, Select


class SimpleConditionalWidgetView(View):
    bar = Select(
        name="bar"
    )  # Reference widget; depends on the value of this widget we will decide widget to use.

    conditional_widget = ConditionalSwitchableView(reference="bar")

    # Register simple widget directly without creating a class
    conditional_widget.register(
        "Action type 1", default=True, widget=TextInput(name="simple_widget")
    )


view = SimpleConditionalWidgetView(browser)  # noqa: F821

# When bar is set to 'Action type 1', conditional_widget becomes available.
view.bar.fill("Action type 1")
print(f"Conditional widget is displayed (Action type 1): {view.conditional_widget.is_displayed}")
view.conditional_widget.fill("Direct widget input")
print("Filled conditional widget with: 'Direct widget input'")

# When bar is set to 'Other', conditional_widget becomes unavailable.
view.bar.fill("Other")
print(f"Conditional widget is displayed (Other): {view.conditional_widget.is_displayed}")
