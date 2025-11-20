"""Select Widget Example

This example demonstrates select dropdown operations.
"""

from widgetastic.widget import Select

single_select = Select(browser, name="testselect1")  # noqa: F821
multi_select = Select(browser, name="testselect2")  # noqa: F821

# Reading selected values
print(f"Single select current value: {single_select.read()}")

# Get all available options
print(f"All available options: {single_select.all_options}")

# Select by visible text
single_select.fill("Bar")
print(f"After fill('Bar'): {single_select.read()}")

# Select by value
single_select.fill(("by_value", "foo"))
print(f"After fill by value 'foo': {single_select.read()}")

# Multiple selection
multi_select.fill(["Foo", "Baz"])
print(f"Multiple select values: {multi_select.read()}")
