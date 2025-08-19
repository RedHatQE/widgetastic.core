import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser as PlaywrightBrowser, BrowserContext
from widgetastic.browser import Browser, WindowManager
from typing import Iterator


# custom browser class
class CustomBrowser(Browser):
    @property
    def product_version(self):
        return "1.0.0"


def pytest_addoption(parser):
    """Add custom command line options for browser selection and mode."""
    parser.addoption(
        "--browser",
        action="store",
        default="chromium",
        choices=["chromium", "firefox"],
        help="Browser to run tests with: chromium, firefox (default: chromium)",
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run tests in headless mode (no browser window) default its run in headed mode.",
    )


@pytest.fixture(scope="session")
def browser_name(request):
    """Get browser name from command line argument."""
    return request.config.getoption("--browser")


@pytest.fixture(scope="session")
def headless_mode(request):
    """Determine if tests should run in headless mode."""
    if request.config.getoption("--headless"):
        return True
    return False


@pytest.fixture(scope="session")
def testing_page_url() -> str:
    """Provides the local file path to the testing page."""
    html_file = Path(__file__).parent / "html" / "testing_page.html"
    return html_file.resolve().as_uri()


@pytest.fixture(scope="session")
def external_test_url() -> str:
    """Provides a reliable local URL simulating external domain for testing.
    We are going to use this for window/browser management testing.
    """
    html_file = Path(__file__).parent / "html" / "external_test_page.html"
    return html_file.resolve().as_uri()


@pytest.fixture(scope="session")
def playwright_browser_instance(browser_name: str, headless_mode: bool) -> PlaywrightBrowser:
    """Launches a Playwright browser instance."""
    with sync_playwright() as p:
        # Select browser based on command line argument (default to chromium)
        if browser_name == "firefox":
            browser = p.firefox.launch(headless=headless_mode)
        else:
            browser = p.chromium.launch(headless=headless_mode)

        print(
            f"\nLaunching {browser_name} browser ({'headless' if headless_mode else 'headed'} mode)"
        )
        yield browser
        print(f"\nClosing {browser_name} browser")
        browser.close()


@pytest.fixture(scope="session")
def browser_context(playwright_browser_instance: PlaywrightBrowser) -> BrowserContext:
    """Creates a browser context for the entire test session."""
    context = playwright_browser_instance.new_context(
        viewport={"width": 1280, "height": 720},
    )
    yield context
    context.close()


@pytest.fixture(scope="session")
def page(browser_context: BrowserContext, testing_page_url: str) -> Iterator[Page]:
    """Creates the initial page within the session context."""
    page = browser_context.new_page()
    page.goto(testing_page_url)
    yield page
    page.close()


@pytest.fixture(scope="session")
def window_manager(browser_context: BrowserContext, page: Page) -> Iterator[WindowManager]:
    """Provides a WindowManager instance for multi-window testing."""
    manager = WindowManager(browser_context, page, browser_class=CustomBrowser)
    try:
        yield manager
    finally:
        manager.close_extra_pages()


@pytest.fixture(scope="function")
def browser(window_manager: WindowManager, testing_page_url: str) -> Iterator[Browser]:
    """Provides the active widgetastic Browser from the manager.
    This will provide isolated tests for each browser.
    """
    br = window_manager.current
    br.url = testing_page_url
    yield br
