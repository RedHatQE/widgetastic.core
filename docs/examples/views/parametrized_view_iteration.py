"""Parametrized View Iteration Example

This example demonstrates iterating through all occurrences of a parametrized view.
"""

from widgetastic.utils import ParametrizedLocator, ParametrizedString
from widgetastic.widget import ParametrizedView, TextInput, Checkbox, View, Text


class ParametrizedViewTesting(View):
    """Parametrized View under View testing."""

    ROOT = ".//div[contains(@class, 'parametrized-view')]"
    title = Text(locator=".//div[@class='widget-title']")

    class thing_container_view(ParametrizedView):  # noqa
        # Defining one parameter
        PARAMETERS = ("thing_id",)
        # ParametrizedLocator coerces to a string upon access
        ROOT = ParametrizedLocator(".//div[@id={thing_id|quote}]")

        # Widget definition processed with parameters
        the_widget = TextInput(name=ParametrizedString("asdf_{thing_id}"))
        description = TextInput(name=ParametrizedString("desc_{thing_id}"))
        active = Checkbox(name=ParametrizedString("active_{thing_id}"))

        @classmethod
        def all(cls, browser):
            # Get all the thing_id values from the page
            elements = browser.elements(".//div[@class='thing']")
            # Return a list of tuples, each containing the thing_id value
            return [(browser.get_attribute("id", el),) for el in elements]


# We create the root view
view = ParametrizedViewTesting(browser)  # noqa: F821

print("Iterating through all thing containers:")
for container_view in view.thing_container_view:
    container_view.the_widget.fill("do something with the widget")
    print(f"Container values: {container_view.read()}")
