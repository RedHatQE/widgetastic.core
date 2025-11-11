# Example: Basic Usage
"""DefaultFillViewStrategy Examples

This comprehensive example demonstrates all aspects of DefaultFillViewStrategy.
"""

from widgetastic.utils import DefaultFillViewStrategy
from widgetastic.widget import View, TextInput, Checkbox, Widget


class BasicForm(View):
    input1 = TextInput(name="input1")
    input2 = TextInput(name="fill_with_2")
    checkbox1 = Checkbox(id="input2")

    # Explicitly set the default strategy (optional - it's the default)
    fill_strategy = DefaultFillViewStrategy()


# Create view instance
view = BasicForm(browser)  # noqa: F821

# Fill multiple widgets at once
changed = view.fill({"input1": "test_value", "checkbox1": True})

print(f"Fill changed values: {changed}")
print(f"Current values: {view.read()}")
# End Example: Basic Usage

# Example: Filtering None Values
values_with_none = {
    "input1": "value1",
    "input2": None,  # This will be filtered out
    "checkbox1": True,
}

view.fill(values_with_none)
print(f"After filling with None values: {view.read()}")
# End Example: Filtering None Values

# Example: Handling Extra Keys
import logging  # noqa: E402

logging.basicConfig(level=logging.WARNING)

values_with_extras = {
    "input1": "value1",
    "nonexistent_widget": "value2",  # This doesn't exist
    "another_extra": "value3",  # This doesn't exist either
}

# When filling, you'll get a warning in logs:
# "Extra values that have no corresponding fill fields passed: another_extra, nonexistent_widget"
view.fill(values_with_extras)
# End Example: Handling Extra Keys


# Example: Handling Widgets Without Fill
class NoFillWidget(Widget):
    """Widget without fill method."""

    pass


class TestForm(View):
    input1 = TextInput(name="input1")
    no_fill_widget = NoFillWidget()
    input2 = TextInput(name="fill_with_2")

    fill_strategy = DefaultFillViewStrategy()


test_view = TestForm(browser)  # noqa: F821

# Fill operation will skip no_fill_widget and log a warning
values = {
    "input1": "value1",
    "no_fill_widget": "will_skip",  # This will be skipped
    "input2": "value2",
}

result = test_view.fill(values)
print(f"Fill result: {result}")
print(f"Current values: {test_view.read()}")
# End Example: Handling Widgets Without Fill

# Example: Change Detection
# First fill - values are new, so returns True
result1 = view.fill({"input1": "test_value", "checkbox1": True})
print(f"First fill result: {result1}")

# Second fill with same values - no change, returns False
result2 = view.fill({"input1": "test_value", "checkbox1": True})
print(f"Second fill result: {result2}")
# End Example: Change Detection
