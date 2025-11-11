"""IFrame Context Isolation

This example demonstrates that iframe contexts are completely isolated.
"""

from widgetastic.widget import View, Text, Select, Checkbox


class MainPageView(View):
    # Elements in main page context
    main_title = Text("h1#wt-core-title")
    main_checkbox = Checkbox(id="switchabletesting-3")


class IFrameView(View):
    FRAME = '//iframe[@name="some_iframe"]'
    iframe_title = Text(".//h3")
    iframe_select = Select(id="iframe_select1")


main_view = MainPageView(browser)  # noqa: F821
iframe_view = IFrameView(browser)  # noqa: F821

# Both contexts work independently
print(f"Main page title: {main_view.main_title.read()}")
print(f"IFrame title: {iframe_view.iframe_title.read()}")

# Interactions don't affect each other
print("\nTesting context isolation:")
main_view.main_checkbox.fill(True)
iframe_view.iframe_select.fill("Bar")

# Verify isolation - both maintain their states
main_checkbox_state = main_view.main_checkbox.read()
iframe_select_state = iframe_view.iframe_select.read()

print(f"Main checkbox state: {main_checkbox_state}")
print(f"IFrame select state: {iframe_select_state}")

if main_checkbox_state is True and iframe_select_state == "Bar":
    print("✓ Context isolation verified")
