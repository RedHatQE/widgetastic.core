# Example: Handling Popups and New Tabs
"""Handling Popups and New Tabs

This example demonstrates handling JavaScript popups using expect_new_page().
"""

import inspect
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from widgetastic.browser import Browser, WindowManager
from widgetastic.widget import View, Text


def setup_window_manager():
    """Setup WindowManager with popup test page."""
    # Get headless mode from environment (set by conftest or CI)
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

    base_path = Path(inspect.getfile(Browser)).parent.parent.parent

    p = sync_playwright().start()
    browser_instance = p.chromium.launch(headless=headless)
    context = browser_instance.new_context()
    page = context.new_page()
    return WindowManager(context, page), p, base_path


window_manager, pw, base_path = setup_window_manager()


class PopupPageView(View):
    """View for popup_test_page.html"""

    open_popup_button = Text("#open-popup")
    open_tab_button = Text("#open-new-tab")
    external_link = Text("#external-link")


# Navigate to popup test page
popup_page_path = base_path / "testing" / "html" / "popup_test_page.html"
initial_browser = window_manager.current
initial_browser.url = popup_page_path.as_uri()
popup_view = PopupPageView(initial_browser)

print(f"Initial browser count: {len(window_manager.all_browsers)}")

# Handle JavaScript popup window
with window_manager.expect_new_page(timeout=5.0) as popup_browser:
    popup_view.open_popup_button.click()

print(f"Popup browser URL: {popup_browser.url}")
print(f"Popup browser title: {popup_browser.title}")
print(f"Total browsers: {len(window_manager.all_browsers)}")

# Handle new tab opened by JavaScript
with window_manager.expect_new_page(timeout=5.0) as new_tab_browser:
    popup_view.open_tab_button.click()

print(f"New tab URL: {new_tab_browser.url}")

# Handle link with target="_blank"
with window_manager.expect_new_page(timeout=5.0) as external_browser:
    popup_view.external_link.click()

print(f"External browser URL: {external_browser.url}")

# Clean up opened browsers
window_manager.close_browser(popup_browser)
window_manager.close_browser(new_tab_browser)
window_manager.close_browser(external_browser)

print(f"After cleanup: {len(window_manager.all_browsers)} browsers")

# End of Example: Handling Popups and New Tabs

# Example: Working with all_browsers Property
# Example: Working with all_browsers Property.

# Get all active browsers with automatic cleanup
all_browsers = window_manager.all_browsers
print(f"Currently managing {len(all_browsers)} windows")

# open one more page external test page
external_page_path = base_path / "testing" / "html" / "external_test_page.html"
test_browser = window_manager.new_browser(external_page_path.as_uri(), focus=False)
print(f"Before close: {len(window_manager.all_browsers)} browsers")

# Iterate through all browsers
for i, browser in enumerate(window_manager.all_browsers):
    print(f"Window {i}: {browser.title} - {browser.url}")

window_manager.close_browser(test_browser)
print(f"After close: {len(window_manager.all_browsers)} browsers")

# Close playwright instance
pw.stop()
# End of Example: Working with all_browsers Property
