"""Tests for WindowManager functionality."""

import pytest
import time
from pathlib import Path
from widgetastic.browser import Browser, WindowManager
from widgetastic.exceptions import NoSuchElementException


@pytest.fixture(scope="function")
def popup_test_page_url() -> str:
    """URL for the popup test page."""
    html_file = Path(__file__).parent / "html" / "popup_test_page.html"
    return html_file.resolve().as_uri()


def test_initialization_and_properties(isolated_window_manager, testing_page_url):
    """Test WindowManager initialization and basic properties."""
    # Basic initialization
    assert isolated_window_manager.current is not None
    assert isinstance(isolated_window_manager.current, Browser)
    assert isolated_window_manager.current.url.endswith("testing_page.html")

    # Properties work correctly
    browsers = isolated_window_manager.all_browsers
    pages = isolated_window_manager.all_pages
    assert len(browsers) >= 1
    assert len(pages) >= 1
    assert isolated_window_manager.current in browsers
    assert isolated_window_manager.current.page in pages


def test_custom_browser_class(isolated_browser_context, testing_page_url):
    """Test WindowManager with custom browser class."""
    from conftest import CustomBrowser

    # Create page for this test
    page = isolated_browser_context.new_page()
    page.goto(testing_page_url)

    # Create WindowManager with custom browser class
    manager = WindowManager(isolated_browser_context, page, browser_class=CustomBrowser)

    # Current browser should be of custom class
    assert isinstance(manager.current, CustomBrowser)
    assert hasattr(manager.current, "product_version")
    assert manager.current.product_version == "1.0.0"

    # New browsers should also use custom class
    new_browser = manager.new_browser(testing_page_url, focus=False)
    assert isinstance(new_browser, CustomBrowser)
    assert new_browser.product_version == "1.0.0"


def test_new_browser_with_focus(isolated_window_manager, external_test_url, testing_page_url):
    """Test creating new browser with focus (default behavior)."""
    initial_browser = isolated_window_manager.current
    initial_count = len(isolated_window_manager.all_browsers)

    # Create new browser (focus=True by default)
    new_browser = isolated_window_manager.new_browser(external_test_url)

    # New browser becomes current
    assert isolated_window_manager.current is new_browser
    assert isolated_window_manager.current is not initial_browser
    assert len(isolated_window_manager.all_browsers) == initial_count + 1
    assert new_browser.url.rstrip("/") == external_test_url.rstrip("/")


def test_new_browser_without_focus(isolated_window_manager, external_test_url, testing_page_url):
    """Test creating new browser without focus."""
    initial_browser = isolated_window_manager.current
    initial_count = len(isolated_window_manager.all_browsers)

    # Create new browser without focus
    new_browser = isolated_window_manager.new_browser(external_test_url, focus=False)

    # Original browser remains current
    assert isolated_window_manager.current is initial_browser
    assert isolated_window_manager.current is not new_browser
    assert len(isolated_window_manager.all_browsers) == initial_count + 1


def test_switch_focus_between_browsers(
    isolated_window_manager, external_test_url, testing_page_url
):
    """Test switching focus between browsers."""
    initial_browser = isolated_window_manager.current
    initial_page = initial_browser.page

    # Create second browser
    new_browser = isolated_window_manager.new_browser(external_test_url, focus=False)
    assert isolated_window_manager.current is initial_browser

    # Switch to new browser
    isolated_window_manager.switch_to(new_browser)
    assert isolated_window_manager.current is new_browser

    # Switch back using page instance (more reliable than browser object)
    isolated_window_manager.switch_to(initial_page)
    assert isolated_window_manager.current.page is initial_page


def test_close_current_browser(isolated_window_manager, external_test_url, testing_page_url):
    """Test closing current browser."""

    initial_count = len(isolated_window_manager.all_browsers)
    initial_url = isolated_window_manager.current.url

    # Create and switch to new browser
    new_browser = isolated_window_manager.new_browser(external_test_url)
    assert isolated_window_manager.current is new_browser
    assert len(isolated_window_manager.all_browsers) == initial_count + 1

    # Close current browser
    isolated_window_manager.close_browser()

    # Should switch to a remaining browser and count should decrease
    assert len(isolated_window_manager.all_browsers) == initial_count
    assert isolated_window_manager.current in isolated_window_manager.all_browsers
    # Should switch back to a browser with testing page (though not necessarily same object)
    assert isolated_window_manager.current.url == initial_url


def test_close_specific_browser(isolated_window_manager, external_test_url, testing_page_url):
    """Test closing specific browser without affecting current."""

    current_browser = isolated_window_manager.current
    initial_count = len(isolated_window_manager.all_browsers)

    # Create new browser without focus
    target_browser = isolated_window_manager.new_browser(external_test_url, focus=False)
    assert isolated_window_manager.current is current_browser

    # Close the specific browser
    isolated_window_manager.close_browser(target_browser)

    # Current should remain unchanged
    assert isolated_window_manager.current is current_browser
    assert len(isolated_window_manager.all_browsers) == initial_count
    assert target_browser not in isolated_window_manager.all_browsers


def test_close_extra_pages_except_current(
    isolated_window_manager, external_test_url, testing_page_url
):
    """Test close_extra_pages default behavior - keeps current page."""

    current_browser = isolated_window_manager.current

    # Create multiple additional browsers
    browser2 = isolated_window_manager.new_browser(external_test_url, focus=False)
    browser3 = isolated_window_manager.new_browser(testing_page_url, focus=False)

    assert len(isolated_window_manager.all_pages) >= 3

    # Close all except current
    isolated_window_manager.close_extra_pages()

    # Current should remain, others should be closed
    assert not current_browser.is_browser_closed
    assert browser2.is_browser_closed
    assert browser3.is_browser_closed
    assert len(isolated_window_manager.all_pages) == 1


def test_close_extra_pages_including_current(
    isolated_window_manager, external_test_url, testing_page_url
):
    """Test close_extra_pages with current=True - closes everything."""

    current_browser = isolated_window_manager.current

    # Create additional browsers
    browser2 = isolated_window_manager.new_browser(external_test_url, focus=False)
    browser3 = isolated_window_manager.new_browser(testing_page_url, focus=False)
    assert len(isolated_window_manager.all_pages) >= 3

    # Close all including current
    isolated_window_manager.close_extra_pages(current=True)

    # All should be closed
    assert current_browser.is_browser_closed
    assert browser2.is_browser_closed
    assert browser3.is_browser_closed
    assert len(isolated_window_manager.all_pages) == 0


def test_close_extra_pages_with_exceptions(
    isolated_window_manager, external_test_url, testing_page_url
):
    """Test that close_extra_pages handles exceptions gracefully."""


    test_browser = isolated_window_manager.new_browser(
        f"{external_test_url}#exception_test", focus=False
    )

    # Mock the page.close method to raise an exception
    original_close = test_browser.page.close
    close_called = False

    def mock_failing_close():
        nonlocal close_called
        close_called = True
        raise Exception("Simulated page close failure")

    test_browser.page.close = mock_failing_close

    try:
        # This should not raise an exception even if individual page.close() fails
        isolated_window_manager.close_extra_pages()

        # Verify that close was attempted on the mocked page
        assert close_called, "close() should have been called on the test page"

    except Exception as e:
        pytest.fail(f"close_extra_pages should handle page close exceptions gracefully, got: {e}")

    finally:
        # Restore original close method for cleanup
        test_browser.page.close = original_close

        # Clean up the test browser
        try:
            if not test_browser.is_browser_closed:
                test_browser.page.close()
        except Exception:
            pass


def test_automatic_cleanup_externally_closed_pages(
    isolated_window_manager, external_test_url, testing_page_url
):
    """Test that externally closed pages are automatically cleaned up."""

    initial_count = len(isolated_window_manager.all_browsers)

    # Create new browser
    new_browser = isolated_window_manager.new_browser(external_test_url, focus=False)
    new_page = new_browser.page
    assert len(isolated_window_manager.all_browsers) == initial_count + 1

    # Close page externally (not through WindowManager)
    new_page.close()

    # Accessing all_browsers should trigger cleanup
    browsers_after = isolated_window_manager.all_browsers
    assert len(browsers_after) == initial_count
    assert new_browser not in browsers_after


def test_automatic_popup_detection(
    isolated_window_manager, isolated_browser_context, external_test_url, testing_page_url
):
    """Test that popups/new pages are automatically detected and wrapped."""

    initial_count = len(isolated_window_manager.all_browsers)

    # Simulate popup by directly creating a new page in the context
    # This mimics what happens when a popup is opened programmatically
    new_page = isolated_browser_context.new_page()
    new_page.goto(external_test_url)

    # WindowManager should automatically detect and wrap the new page
    # Give it a moment to register the new page
    time.sleep(0.1)

    browsers_after = isolated_window_manager.all_browsers
    assert len(browsers_after) == initial_count + 1, "New page should be automatically wrapped"

    # Find the new browser
    new_browser = None
    for browser in browsers_after:
        if browser.page is new_page:
            new_browser = browser
            break

    assert new_browser is not None, "New page should be wrapped as a Browser instance"
    assert isinstance(new_browser, Browser), "Wrapped page should be a Browser instance"

    # Should be able to switch to it
    isolated_window_manager.switch_to(new_browser)
    assert isolated_window_manager.current is new_browser


def test_error_handling_nonexistent_page(
    isolated_window_manager, isolated_browser_context, testing_page_url
):
    """Test error handling for invalid operations."""


    # Create and immediately close external page
    external_page = isolated_browser_context.new_page()
    external_page.close()

    # Should raise error when trying to switch to closed page
    with pytest.raises(NoSuchElementException, match="The specified Page handle does not exist"):
        isolated_window_manager.switch_to(external_page)


def test_empty_state_handling(isolated_browser_context, testing_page_url):
    """Test handling of empty state (no pages remaining)."""
    # Close all existing pages
    for page in list(isolated_browser_context.pages):
        try:
            if not page.is_closed():
                page.close()
        except Exception:
            pass

    # Create WindowManager and immediately close the page
    page = isolated_browser_context.new_page()
    page.goto(testing_page_url)
    manager = WindowManager(isolated_browser_context, page)
    page.close()

    # Should handle empty state gracefully
    assert len(manager.all_browsers) == 0
    assert len(manager.all_pages) == 0

    # Methods should not crash on empty state
    manager.close_extra_pages()
    manager.close_extra_pages(current=True)


def test_browser_workflow_integration(isolated_window_manager, external_test_url, testing_page_url):
    """Test complete workflow: create, switch, and close browsers."""


    # Verify starting state
    initial_browser = isolated_window_manager.current
    assert initial_browser.url.endswith("testing_page.html")
    initial_count = len(isolated_window_manager.all_browsers)

    # Create background browser (no focus change)
    bg_browser = isolated_window_manager.new_browser(f"{external_test_url}#bg", focus=False)
    assert isolated_window_manager.current is initial_browser  # Should not change
    assert len(isolated_window_manager.all_browsers) > initial_count  # Should increase

    # Create focused browser (focus should change)
    focus_browser = isolated_window_manager.new_browser(f"{testing_page_url}#focus", focus=True)
    assert isolated_window_manager.current is focus_browser  # Should change to new browser

    # Test switching between browsers
    isolated_window_manager.switch_to(bg_browser)
    assert isolated_window_manager.current is bg_browser
    assert bg_browser.url.endswith("external_test_page.html#bg")

    isolated_window_manager.switch_to(focus_browser)
    assert isolated_window_manager.current is focus_browser
    assert focus_browser.url.endswith("testing_page.html#focus")

    # Close a browser and verify cleanup
    browser_count_before_close = len(isolated_window_manager.all_browsers)
    isolated_window_manager.close_browser(bg_browser)
    browser_count_after_close = len(isolated_window_manager.all_browsers)

    # Verify browser was removed from collection
    assert browser_count_after_close < browser_count_before_close
    assert bg_browser not in isolated_window_manager.all_browsers

    # Verify current browser is still valid
    assert isolated_window_manager.current in isolated_window_manager.all_browsers
    assert not isolated_window_manager.current.is_browser_closed
