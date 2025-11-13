# Example: Basic Usage
"""WaitFillViewStrategy Examples

This comprehensive example demonstrates WaitFillViewStrategy usage.
"""

from widgetastic.utils import WaitFillViewStrategy
from widgetastic.widget import View, TextInput, Checkbox


class DynamicForm(View):
    input1 = TextInput(name="input1")
    checkbox1 = Checkbox(id="input2")

    # Use wait strategy with default 5-second timeout
    fill_strategy = WaitFillViewStrategy()


view = DynamicForm(browser)  # noqa: F821

# Fill operation will wait for each widget to be displayed
changed = view.fill({"input1": "wait_test_value", "checkbox1": True})

print(f"Fill changed values: {changed}")
print(f"Current values: {view.read()}")
# End Example: Basic Usage


# Example: Custom Wait Timeout
class DynamicFormCustomTimeout(View):
    input1 = TextInput(name="input1")
    input2 = TextInput(name="fill_with_2")
    checkbox1 = Checkbox(id="input2")

    # Custom 10-second timeout per widget
    fill_strategy = WaitFillViewStrategy(wait_widget="10s")


view_custom = DynamicFormCustomTimeout(browser)  # noqa: F821

# Each widget will wait up to 10 seconds to be displayed
view_custom.fill({"input1": "custom_wait_test", "input2": "another_value"})
print(f"Current values: {view_custom.read()}")
# End Example: Custom Wait Timeout
