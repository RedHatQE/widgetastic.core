"""Creating OUIA Views

This example demonstrates creating OUIA views as containers for OUIA widgets.
"""

from widgetastic.ouia import OUIAGenericView, OUIAGenericWidget


class Button(OUIAGenericWidget):
    OUIA_COMPONENT_TYPE = "PF/Button"


class TestView(OUIAGenericView):
    """OUIA view containing multiple OUIA widgets."""

    OUIA_COMPONENT_TYPE = "TestView"
    OUIA_ID = "ouia"  # Optional: default component_id for the view

    button = Button(component_id="This is a button")


view = TestView(browser)  # noqa: F821

# OUIA_COMPONENT_TYPE is used to generate ROOT for this view
print(f"ROOT locator for this view: {view.ROOT}")

print(f"View is displayed: {view.is_displayed}")

print("Clicking button inside OUIA view...")
view.button.click()
print("Button clicked successfully")
