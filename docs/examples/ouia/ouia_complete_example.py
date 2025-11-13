"""Complete OUIA Example

This example demonstrates a comprehensive OUIA setup with multiple widgets.
"""

from widgetastic.ouia import OUIAGenericView, OUIAGenericWidget
from widgetastic.ouia.checkbox import Checkbox
from widgetastic.ouia.input import TextInput
from widgetastic.ouia.text import Text


# Define custom OUIA widget
class Button(OUIAGenericWidget):
    OUIA_COMPONENT_TYPE = "PF/Button"


# Create comprehensive OUIA view
class TestView(OUIAGenericView):
    OUIA_COMPONENT_TYPE = "TestView"
    OUIA_ID = "ouia"

    button = Button(component_id="This is a button")
    text = Text(component_id="unique_id", component_type="Text")
    text_input = TextInput(component_id="unique_id", component_type="TextInput")
    checkbox = Checkbox(component_id="unique_id", component_type="CheckBox")


# Use the view
view = TestView(browser)  # noqa: F821

print("Testing OUIA widgets:")
view.button.click()
print("✓ Button clicked successfully")

view.text_input.fill("Test")
print(f"✓ Text input value: {view.text_input.read()}")

view.checkbox.fill(True)
print(f"✓ Checkbox checked: {view.checkbox.read()}")

print(f"✓ Text widget value: {view.text.read()}")
