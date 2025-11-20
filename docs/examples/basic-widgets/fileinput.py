"""FileInput Widget Example

This example demonstrates file upload operations.
"""

from widgetastic.widget import FileInput

file_input = FileInput(browser, id="fileinput")  # noqa: F821

print(f"File input is displayed: {file_input.is_displayed}")
print(f"File input is enabled: {file_input.is_enabled}")

# File upload operations
result = file_input.fill("/etc/resolv.conf")
print(f"File upload result: {result}")
