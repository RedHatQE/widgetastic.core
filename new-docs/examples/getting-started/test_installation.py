# test_installation.py

from playwright.sync_api import sync_playwright
from widgetastic.browser import Browser
from widgetastic.widget import View, Text


class TestView(View):
    title = Text("title")


def test_widgetastic():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://example.com")

        wt_browser = Browser(page)
        view = TestView(wt_browser)

        print(f"Page title: {view.title.text}")
        print("✅ Widgetastic is working correctly!")

        browser.close()


if __name__ == "__main__":
    test_widgetastic()
