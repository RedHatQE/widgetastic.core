"""Nested IFrame Navigation

This example demonstrates handling nested iframes (iframe within iframe).
"""

from widgetastic.widget import View, Text, Select, TextInput


class NestedIFrameView(View):
    # First level iframe
    FRAME = '//iframe[@name="some_iframe"]'
    iframe_title = Text(".//h3")

    # Nested iframe class (iframe within iframe)
    @View.nested
    class nested_iframe(View):  # noqa
        FRAME = './/iframe[@name="another_iframe"]'
        nested_title = Text(".//h3")
        nested_select = Select(id="iframe_select3")

        # Deeply nested view within the nested iframe
        @View.nested
        class deep_nested(View):  # noqa
            ROOT = './/div[@id="nested_view"]'
            nested_input = TextInput(name="input222")


nested_view = NestedIFrameView(browser)  # noqa: F821

# Access each level of nesting
print(f"Level 1 iframe: {nested_view.iframe_title.read()}")
print(f"Level 2 iframe: {nested_view.nested_iframe.nested_title.read()}")
print(f"Nested select: {nested_view.nested_iframe.nested_select.read()}")

# Access deeply nested input
nested_input_value = nested_view.nested_iframe.deep_nested.nested_input.read()
print(f"Deep nested input: {nested_input_value}")

# Fill deeply nested input
nested_view.nested_iframe.deep_nested.nested_input.fill("Updated Value")
updated_value = nested_view.nested_iframe.deep_nested.nested_input.read()
print(f"Updated nested input: {updated_value}")

# Clean up: Return to main frame
browser.switch_to_main_frame()  # noqa: F821
