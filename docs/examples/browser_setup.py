import inspect
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from widgetastic.browser import Browser


def setup_browser():
    """Setup browser with widgetastic testing page."""

    # Initialize Playwright
    p = sync_playwright().start()
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"
    browser_instance = p.chromium.launch(headless=headless)
    context = browser_instance.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    wt_browser = Browser(page)

    # Navigate to testing page
    base_path = Path(inspect.getfile(Browser)).parent.parent.parent
    test_page_path = base_path / "testing" / "html" / "testing_page.html"
    test_page_url = test_page_path.as_uri()
    wt_browser.goto(test_page_url, wait_until="load")

    return wt_browser


# Usage
browser = setup_browser()
