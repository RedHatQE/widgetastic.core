"""Basic IFrame Access

This example demonstrates accessing elements inside an iframe.
"""

from widgetastic.widget import View, Text, Select


class BasicIFrameView(View):
    # The FRAME attribute specifies the iframe locator
    FRAME = '//iframe[@name="some_iframe"]'

    # Widgets inside the iframe
    iframe_title = Text(".//h3")
    select1 = Select(id="iframe_select1")
    select2 = Select(name="iframe_select2")


iframe_view = BasicIFrameView(browser)  # noqa: F821

# Test basic iframe access
print(f"IFrame displayed: {iframe_view.is_displayed}")
print(f"IFrame title: {iframe_view.iframe_title.read()}")

# Interact with iframe widgets
current_selection = iframe_view.select1.read()
print(f"Current selection: {current_selection}")

# Change selection
iframe_view.select1.fill("Bar")
print(f"New selection: {iframe_view.select1.read()}")

# Working with multi-select in iframe
print(f"\nMulti-select options: {iframe_view.select2.all_options}")

# Select multiple options
iframe_view.select2.fill(["Foo", "Baz"])
selected = iframe_view.select2.read()
print(f"Multi-selected: {selected}")
