"""TextInput State Management Example

This example demonstrates checking widget state and fill behavior.
"""

from widgetastic.widget import TextInput

# Check if element exists and is accessible
enabled_input = TextInput(parent=browser, id="input1")  # noqa: F821
disabled_input = TextInput(parent=browser, name="input1_disabled")  # noqa: F821

print(f"Enabled input is displayed: {enabled_input.is_displayed}")
print(f"Enabled input is enabled: {enabled_input.is_enabled}")
print(f"Disabled input is enabled: {disabled_input.is_enabled}")

# Fill success checking
result1 = enabled_input.fill("new value")
print(f"First fill('new value') returned: {result1}")

# Try to fill same value - no change detected and returns False
result2 = enabled_input.fill("new value")
print(f"Second fill('new value') returned: {result2}")
