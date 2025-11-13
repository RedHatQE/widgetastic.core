"""View State Checking Examples

This example demonstrates how ROOT locators affect is_displayed behavior.
"""

from widgetastic.widget import View, TextInput


# Example 1: Without ROOT locator
class NormalView(View):
    # Without root locator, it will be considered as displayed every time.
    name = TextInput(id="normal_name")


view = NormalView(browser)  # noqa: F821
print(f"View without ROOT - name is displayed: {view.name.is_displayed}")


# Example 2: With ROOT locator
class NormalViewWithRoot(View):
    ROOT = "#normal_view_container"
    name = TextInput(id="normal_name")


view_with_root = NormalViewWithRoot(browser)  # noqa: F821
print(f"View with ROOT - name is displayed: {view_with_root.name.is_displayed}")


# Example 3: Custom is_displayed property
class NormalViewCustom(View):
    name = TextInput(id="normal_name")

    @property
    def is_displayed(self):
        # We can take support of other widgets to check if the view is displayed
        return self.name.is_displayed


view_custom = NormalViewCustom(browser)  # noqa: F821
print(f"View with custom is_displayed: {view_custom.is_displayed}")
