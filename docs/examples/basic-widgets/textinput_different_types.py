"""TextInput with Different Element Types

This example shows how TextInput works with different HTML input types.
"""

from widgetastic.widget import TextInput

# Number input
number_input = TextInput(parent=browser, locator='.//input[@id="input_number"]')  # noqa: F821
number_input.fill("42")
print(f"Number input read value: {number_input.read()}")

# Textarea (multi-line)
textarea = TextInput(parent=browser, id="textarea_input")  # noqa: F821
multiline_text = "Line 1\nLine 2\nLine 3"
textarea.fill(multiline_text)
print(f"Textarea read value: {textarea.read()}")
