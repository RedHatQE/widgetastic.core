"""OUIA Safety Attribute

This example demonstrates using the data-ouia-safe attribute.
"""

from widgetastic.ouia import OUIAGenericWidget

# Create OUIA widgets
button = OUIAGenericWidget(
    parent=browser,  # noqa: F821
    component_id="This is a button",
    component_type="PF/Button",
)

select = OUIAGenericWidget(parent=browser, component_id="some_id", component_type="PF/Select")  # noqa: F821

# Check if components are in a static state (no animations)
print(f"Button is safe: {button.is_safe}")
print(f"Select is safe: {select.is_safe}")

# You can wait for a component to be safe before interacting
print("Waiting for button to be safe before clicking...")
if button.is_safe:
    button.click()
    print("Button clicked after verifying it's safe")
