import inspect
from pathlib import Path
from playwright.sync_api import sync_playwright
from widgetastic.browser import Browser


def setup_browser():
    """Setup browser with widgetastic testing page."""
    # If no path provided, get it from widgetastic package location

    # Initialize Playwright
    p = sync_playwright().start()
    browser_instance = p.chromium.launch(headless=False)
    context = browser_instance.new_context()
    page = context.new_page()
    wt_browser = Browser(page)

    # Navigate to testing page
    base_path = Path(inspect.getfile(Browser)).parent.parent.parent
    test_page_path = base_path / "testing" / "html" / "testing_page.html"
    test_page_url = test_page_path.as_uri()
    wt_browser.goto(test_page_url)

    return wt_browser


# Usage
browser = setup_browser()
