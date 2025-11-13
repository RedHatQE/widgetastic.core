"""ROOT Locator Scoping Example

This example demonstrates how ROOT locators scope widget searches.
"""

from widgetastic.widget import View, Text, TextInput


class NormalViewTesting(View):
    ROOT = ".//div[contains(@class, 'normal-view')]"  # All widgets scoped to this section

    # These widgets are found within `ROOT`.
    title = Text(locator=".//div[@class='widget-title']")
    name = TextInput(id="normal_name")


# Without ROOT, widgets would search the entire page
# With ROOT, widgets only search within .//div[contains(@class, 'normal-view')].

view = NormalViewTesting(browser)  # noqa: F821
print(f"View title: {view.title.read()}")
print(f"Name input is displayed: {view.name.is_displayed}")
