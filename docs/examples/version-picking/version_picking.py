# Example: Setting Up Version Picking Environment
"""Basic Version Picking

This example demonstrates version-dependent widget definitions.
"""

import inspect
from pathlib import Path
from playwright.sync_api import sync_playwright
from widgetastic.browser import Browser
from widgetastic.utils import VersionPick, Version
from widgetastic.widget import View, Text, TextInput


# Browser setup (from previous example)
class BrowserV1(Browser):
    @property
    def product_version(self):
        return Version("1.0.0")


class BrowserV2(Browser):
    @property
    def product_version(self):
        return Version("2.1.0")


def get_pw_and_browser(version: str = "v1"):
    p = sync_playwright().start()
    browser_instance = p.chromium.launch(headless=False)
    context = browser_instance.new_context()
    page = context.new_page()

    base_path = Path(inspect.getfile(Browser)).parent.parent.parent
    test_page_path = base_path / "testing" / "html" / "testing_page.html"
    test_page_url = test_page_path.as_uri()
    page.goto(test_page_url)

    if version == "v1":
        return p, BrowserV1(page)
    else:
        return p, BrowserV2(page)


# End of Example: Setting Up Version Picking Environment


# Example: Basic Version Picking
# Create versioned view
class VersionedView(View):
    input_field = VersionPick(
        {
            Version.lowest(): TextInput(name="fill_with_1"),  # Default/fallback (v1.x)
            "2.0.0": TextInput(name="fill_with_2"),  # Version 2.0.0+
        }
    )
    click_button = VersionPick(
        {
            Version.lowest(): Text("#fill_with_button_1"),  # Default/fallback (v1.x)
            "2.0.0": Text("#fill_with_button_2"),  # Version 2.0.0+
        }
    )


# Test with version 1.0.0 browser
pw, browser_v1 = get_pw_and_browser("v1")
view = VersionedView(browser_v1)
print(f"Browser version (v1): {browser_v1.product_version}")
print(f"Input locator (v1): {view.input_field.locator}")
print(f"Button locator (v1): {view.click_button.locator}")
pw.stop()

# Test with version 2.1.0 browser
pw, browser_v2 = get_pw_and_browser("v2")
view = VersionedView(browser_v2)
print(f"\nBrowser version (v2): {browser_v2.product_version}")
print(f"Input locator (v2): {view.input_field.locator}")
print(f"Button locator (v2): {view.click_button.locator}")
pw.stop()
# End of Example: Basic Version Picking
