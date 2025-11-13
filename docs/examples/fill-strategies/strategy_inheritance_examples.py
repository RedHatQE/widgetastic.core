"""Strategy Inheritance Examples

This example demonstrates how child views inherit parent's fill strategy.
"""

# Example: Without Inheritance
from widgetastic.utils import WaitFillViewStrategy
from widgetastic.widget import View, TextInput


# Example: Without respect_parent (default behavior)
class ParentViewNoInherit(View):
    fill_strategy = WaitFillViewStrategy(wait_widget="10s")

    @View.nested
    class ChildView(View):
        input1 = TextInput(name="input1")


parent_view = ParentViewNoInherit(browser)  # noqa: F821
print(f"Parent strategy: {type(parent_view.fill_strategy).__name__}")
print(f"Child strategy: {type(parent_view.ChildView.fill_strategy).__name__}")
# End Example: Without Inheritance


# Example: With Inheritance
# Example: With respect_parent=True
class ParentViewWithInherit(View):
    fill_strategy = WaitFillViewStrategy(respect_parent=True, wait_widget="10s")

    @View.nested
    class ChildView(View):
        input1 = TextInput(name="input1")


parent_view2 = ParentViewWithInherit(browser)  # noqa: F821
print(f"Parent strategy: {type(parent_view2.fill_strategy).__name__}")
print(f"Child strategy: {type(parent_view2.ChildView.fill_strategy).__name__}")
# End Example: With Inheritance
