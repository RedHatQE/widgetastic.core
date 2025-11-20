# test_installation.py

import os
from playwright.sync_api import sync_playwright
from widgetastic.browser import Browser
from widgetastic.widget import View, Text


class TestView(View):
    title = Text("title")


def test_widgetastic():
    # Get headless mode from environment (set by conftest or CI)
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto("https://example.com")

        wt_browser = Browser(page)
        view = TestView(wt_browser)

        print(f"Page title: {view.title.text}")
        print("✅ Widgetastic is working correctly!")

        browser.close()


if __name__ == "__main__":
    test_widgetastic()
