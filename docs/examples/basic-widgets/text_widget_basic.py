"""Basic Text Widget Example

This example demonstrates how to use the Text widget to extract text content.
"""

from widgetastic.widget import Text
from widgetastic.exceptions import NoSuchElementException

# In-line Initialization of Text widget
main_title = Text(parent=browser, locator=".//h1[@id='wt-core-title']")  # noqa: F821

# Widget operations
print(f"Title is displayed: {main_title.is_displayed}")
print(f"Title is enabled: {main_title.is_enabled}")
print(f"Using .text property: '{main_title.text}'")
print(f"Using .read() method: '{main_title.read()}'")

# Handling Non-Existing Elements
non_existing_element = Text(browser, locator='.//div[@id="non-existing-element"]')  # noqa: F821
print(f"Non-existing element is displayed: {non_existing_element.is_displayed}")
try:
    non_existing_element.read()
except NoSuchElementException:
    print("NoSuchElementException raised as expected")
