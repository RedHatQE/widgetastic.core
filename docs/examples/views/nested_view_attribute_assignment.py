"""Nested Views - Attribute Assignment Approach

This example demonstrates creating nested views using View.nested().
"""

from widgetastic.widget import View, Text, TextInput, Checkbox


class NormalViewTesting(View):
    """Normal View under View testing."""

    ROOT = ".//div[contains(@class, 'normal-view')]"
    title = Text(locator=".//div[@class='widget-title']")
    name = TextInput(id="normal_name")
    email = TextInput(id="normal_email")
    terms = Checkbox(id="normal_terms")
    submit = Text(locator=".//button[@id='normal_submit']")


class ParametrizedViewTesting(View):
    """Parametrized View under View testing."""

    ROOT = ".//div[contains(@class, 'parametrized-view')]"
    title = Text(locator=".//div[@class='widget-title']")
    # Some other widgets


class ConditionalSwitchableViewTesting(View):
    """Conditional Switchable View under View testing."""

    ROOT = ".//div[contains(@class, 'conditional-switchable-view')]"
    title = Text(locator=".//div[@class='widget-title']")
    # Some other widgets


class ViewTesting(View):
    normal_view = View.nested(NormalViewTesting)
    parametrized_view = View.nested(ParametrizedViewTesting)
    conditional_switchable_view = View.nested(ConditionalSwitchableViewTesting)


# Access nested elements
view = ViewTesting(browser)  # noqa: F821

print(f"Normal view is displayed: {view.normal_view.is_displayed}")
print(f"Normal view title: {view.normal_view.title.read()}")
print(f"Parametrized view title: {view.parametrized_view.title.read()}")
print(f"Conditional switchable view: {view.conditional_switchable_view.read()}")
