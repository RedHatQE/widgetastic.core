def test_playwright(browser):
    assert browser.title() == "Test page"
