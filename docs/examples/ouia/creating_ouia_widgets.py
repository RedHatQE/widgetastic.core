"""Creating OUIA Widgets

This example demonstrates creating and using OUIA-compatible widgets.
"""

from widgetastic.ouia import OUIAGenericWidget
from widgetastic.widget import View


class Button(OUIAGenericWidget):
    """OUIA Button widget following PF (PatternFly) namespace."""

    OUIA_COMPONENT_TYPE = "PF/Button"


class Details(View):
    button = Button(component_id="This is a button")


view = Details(browser)  # noqa: F821

print(f"Button is displayed: {view.button.is_displayed}")
print("Clicking button...")
view.button.click()
print("Button clicked successfully")
