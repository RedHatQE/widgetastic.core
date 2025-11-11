"""Nested Parametrized View Example

This example demonstrates nesting a parametrized view inside another view.
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


# We create the root view
view = ParametrizedViewTesting(browser)  # noqa: F821

# Now if it was an ordinary nested view, view.thing_container_view.the_widget would give us the
# nested view instance directly and then the the_widget widget. But this is a parametrized view
# and it will give us an intermediate object whose task is to collect the parameters upon
# calling and then pass them through into the real view object.

# This example will be invoking the parametrized view with the exactly same param like the
# previous example:
print("Accessing parametrized container 'foo'")
foo_container = view.thing_container_view("foo")

# So, when we have that view, you can use it as you are used to
view.thing_container_view("foo").the_widget.fill("Test for foo")
print(f"Filled foo container: {view.thing_container_view('foo').the_widget.read()}")

view.thing_container_view("bar").the_widget.fill("Test for bar")
print(f"Filled bar container: {view.thing_container_view('bar').the_widget.read()}")

view.thing_container_view("baz").the_widget.fill("Test for baz")
print(f"Filled baz container: {view.thing_container_view('baz').the_widget.read()}")

# Or with keyword params
view.thing_container_view(thing_id="foo").the_widget.fill("Test for foo with keyword")
print(f"Using keyword param: {view.thing_container_view(thing_id='foo').the_widget.read()}")
