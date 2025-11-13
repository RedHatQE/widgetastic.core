"""Nested Views - Inner Classes Approach

This example demonstrates creating nested views using @View.nested decorator.
"""

from widgetastic.widget import View, Text, TextInput, Checkbox


class ViewTesting(View):
    @View.nested
    class normal_view(View):  # noqa
        """Normal View under View testing."""

        ROOT = ".//div[contains(@class, 'normal-view')]"
        title = Text(locator=".//div[@class='widget-title']")
        name = TextInput(id="normal_name")
        email = TextInput(id="normal_email")
        terms = Checkbox(id="normal_terms")
        submit = Text(locator=".//button[@id='normal_submit']")

    @View.nested
    class parametrized_view(View):  # noqa
        """Parametrized View under View testing."""

        ROOT = ".//div[contains(@class, 'parametrized-view')]"
        title = Text(locator=".//div[@class='widget-title']")
        # Some other widgets

    @View.nested
    class conditional_switchable_view(View):  # noqa
        """Conditional Switchable View under View testing."""

        ROOT = ".//div[contains(@class, 'conditional-switchable-view')]"
        title = Text(locator=".//div[@class='widget-title']")
        # Some other widgets


# Access nested elements
view = ViewTesting(browser)  # noqa: F821

print(f"Normal view is displayed: {view.normal_view.is_displayed}")
print(f"Normal view title: {view.normal_view.title.read()}")
print(f"Parametrized view title: {view.parametrized_view.title.read()}")
print(f"Conditional switchable view: {view.conditional_switchable_view.read()}")
