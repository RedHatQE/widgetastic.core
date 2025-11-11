"""Basic TextInput Widget Example

This example demonstrates basic TextInput operations.
"""

from widgetastic.widget import TextInput

# Inline initialization for learning
text_input = TextInput(parent=browser, id="input")  # noqa: F821

# Widget operations
print(f"Text input is displayed: {text_input.is_displayed}")
print(f"Text input is enabled: {text_input.is_enabled}")

text_input.fill("Hello World")
print(f"After fill, .value returns: '{text_input.value}'")
print(f"After fill, .read() returns: '{text_input.read()}'")
