"""ParametrizedView Example

This example demonstrates using ParametrizedView to handle repeated UI patterns.
"""

from widgetastic.utils import ParametrizedLocator, ParametrizedString
from widgetastic.widget import ParametrizedView, TextInput, Checkbox


class ThingContainerView(ParametrizedView):
    # Defining one parameter
    PARAMETERS = ("thing_id",)
    # ParametrizedLocator coerces to a string upon access
    # It follows similar formatting syntax as .format
    # You can use the xpath quote filter as shown
    ROOT = ParametrizedLocator(".//div[@id={thing_id|quote}]")

    # Widget definition *args and values of **kwargs (only the first level) are processed as well
    the_widget = TextInput(name=ParametrizedString("asdf_{thing_id}"))
    description = TextInput(name=ParametrizedString("desc_{thing_id}"))
    active = Checkbox(name=ParametrizedString("active_{thing_id}"))


# Then for invoking this. create a view for foo.
view = ThingContainerView(browser, additional_context={"thing_id": "foo"})  # noqa: F821

# Fill the foo container
print("Filling container 'foo':")
view.the_widget.fill("Test input for foo")
view.description.fill("Description for foo")
view.active.fill(True)
print(f"Foo container values: {view.read()}")

# Create parametrized view for bar
bar_view = ThingContainerView(browser, additional_context={"thing_id": "bar"})  # noqa: F821
bar_view.the_widget.fill("Test input for bar")
print(f"Bar container widget value: {bar_view.the_widget.read()}")
