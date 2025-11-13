"""Checkbox Widget Example

This example demonstrates checkbox operations.
"""

from widgetastic.widget import Checkbox

enabled_checkbox = Checkbox(browser, id="input2")  # noqa: F821
disabled_checkbox = Checkbox(browser, id="input2_disabled")  # noqa: F821

# Check is_displayed and is_enabled
print(f"Enabled checkbox is displayed: {enabled_checkbox.is_displayed}")
print(f"Disabled checkbox is displayed: {disabled_checkbox.is_displayed}")

print(f"Enabled checkbox is enabled: {enabled_checkbox.is_enabled}")
print(f"Disabled checkbox is enabled: {disabled_checkbox.is_enabled}")

# Filling and reading checkboxes
enabled_checkbox.fill(True)
print(f"After fill(True), read returns: {enabled_checkbox.read()}")

enabled_checkbox.fill(False)
print(f"After fill(False), read returns: {enabled_checkbox.read()}")
