"""ConditionalSwitchableView Example

This example demonstrates using ConditionalSwitchableView to handle dynamic UI sections.
"""

from widgetastic.widget import ConditionalSwitchableView, View, TextInput, Select, Checkbox


class ConditionalSwitchableViewTesting(View):
    ROOT = "#conditional_form_container"

    foo = TextInput(name="foo_value")  # For multi-widget reference
    action_type = Select(name="action_type")

    action_form = ConditionalSwitchableView(reference="action_type")

    # Simple value matching. If Action type 1 is selected in the select, use this view.
    # And if the action_type value does not get matched, use this view as default
    @action_form.register("Action type 1", default=True)
    class ActionType1Form(View):
        ROOT = "#action_form_1"
        widget = TextInput(name="action1_widget")
        options = Select(name="action1_options")
        enabled = Checkbox(name="action1_enabled")

    # You can use a callable to declare the widget values to compare
    @action_form.register(lambda action_type: action_type == "Action type 2")
    class ActionType2Form(View):
        ROOT = "#action_form_2"
        widget = TextInput(name="action2_widget")
        priority = Select(name="action2_priority")
        notes = TextInput(name="action2_notes")

    # With callable, you can use values from multiple widgets
    @action_form.register(
        lambda action_type, foo: action_type == "Action type 3" and foo == "special"
    )
    class ActionType3Form(View):
        ROOT = "#action_form_3"
        widget = TextInput(name="action3_widget")
        config = TextInput(name="action3_config")
        mode = Select(name="action3_mode")


view = ConditionalSwitchableViewTesting(browser)  # noqa: F821

# Switch content by changing selector
print("Filling Action type 1 form:")
view.action_type.fill("Action type 1")
view.action_form.widget.fill("Test input for type 1")
view.action_form.options.fill("Option 1")
view.action_form.enabled.fill(True)
print(f"Action form values: {view.action_form.read()}")

# Switch to action type 2 content
print("\nFilling Action type 2 form:")
view.action_type.fill("Action type 2")
view.action_form.widget.fill("Test input for type 2")
view.action_form.priority.fill("High")
view.action_form.notes.fill("Important notes")
print(f"Action form values: {view.action_form.read()}")

# Switch to action type 3 with multi-widget condition
print("\nFilling Action type 3 form (requires foo='special'):")
view.foo.fill("special")  # Required for condition
view.action_type.fill("Action type 3")
view.action_form.widget.fill("Test input for type 3")
view.action_form.config.fill("advanced config")
print(f"Action form values: {view.action_form.read()}")
