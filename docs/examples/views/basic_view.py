"""Basic View Example

This example demonstrates creating and using a basic View.
"""

from widgetastic.widget import View, Text


class TestingPageView(View):
    # Read the main page title
    main_title = Text(locator=".//h1[@id='wt-core-title']")
    # Read the sub title
    sub_title = Text(locator='.//p[@class="subtitle"]')
    # Define non existing element
    non_existing_element = Text(locator='.//div[@id="non-existing-element"]')


page = TestingPageView(browser)  # noqa: F821

# Check if element exist on page or not
print(f"Main title is displayed: {page.main_title.is_displayed}")
print(f"Non-existing element is displayed: {page.non_existing_element.is_displayed}")

# Reading text content
print(f"Page title: {page.main_title.read()}")
print(f"Sub title: {page.sub_title.read()}")
