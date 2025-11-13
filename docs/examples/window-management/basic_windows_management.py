# Setup: Basic Windows Management
"""Basic Windows Management Example
This example demonstrates creating and managing multiple browser windows.
"""

import inspect
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from widgetastic.browser import Browser, WindowManager


def setup_window_manager():
    """Setup WindowManager and base path."""
    # Get headless mode from environment (set by conftest or CI)
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

    base_path = Path(inspect.getfile(Browser)).parent.parent.parent
    p = sync_playwright().start()
    browser_instance = p.chromium.launch(headless=headless)
    context = browser_instance.new_context()
    page = context.new_page()

    return WindowManager(context, page), p, base_path


window_manager, pw, base_path = setup_window_manager()
# End of Setup

# Example: Creating New Windows
# Example: Creating New Windows

# Get external test page URL
external_page_path = base_path / "testing" / "html" / "external_test_page.html"
external_url = external_page_path.as_uri()

# Current browser
initial_browser = window_manager.current
print(f"Initial browser URL: {initial_browser.url}")
print(f"Total browsers: {len(window_manager.all_browsers)}")

# Create new window/browser with focus (becomes current)
new_browser = window_manager.new_browser(external_url, focus=True)
print(f"\nNew browser URL: {new_browser.url}")
print(f"Current browser changed: {window_manager.current is new_browser}")
print(f"Total browsers: {len(window_manager.all_browsers)}")

# Create background window/browser (doesn't change focus)
bg_browser = window_manager.new_browser(external_url, focus=False)
print(f"\nCurrent browser unchanged: {window_manager.current is new_browser}")
print(f"Total browsers: {len(window_manager.all_browsers)}")


# End of Example: Creating New Windows

# Example: Switching Between Windows
# Example: Switching Between Windows
print(f"Initial browsers created: {len(window_manager.all_browsers)}")

# Switch to different browser by instance
window_manager.switch_to(bg_browser)
print(f"Switched to background browser: {window_manager.current is bg_browser}")

# Switch back to original browser
window_manager.switch_to(initial_browser)
print(f"Switched back to initial browser: {window_manager.current is initial_browser}")

# Switch by page instance
window_manager.switch_to(new_browser.page)
print(f"Switched using page reference: {window_manager.current.page is new_browser.page}")

# Close playwright instance
pw.stop()
# End of Example: Switching Between Windows
