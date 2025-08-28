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


def reset_to_clean_state(window_manager, testing_page_url):
    """Reset WindowManager to a clean state with single testing page."""
    window_manager.close_extra_pages()
    # If current page isn't the testing page, navigate to it
    if not window_manager.current.url.endswith("testing_page.html"):
        window_manager.current.url = testing_page_url


def test_initialization_and_properties(window_manager, testing_page_url):
    """Test WindowManager initialization and basic properties."""
    reset_to_clean_state(window_manager, testing_page_url)

    # Basic initialization
    assert window_manager.current is not None
    assert isinstance(window_manager.current, Browser)
    assert window_manager.current.url.endswith("testing_page.html")

    # Properties work correctly
    browsers = window_manager.all_browsers
    pages = window_manager.all_pages
    assert len(browsers) >= 1
    assert len(pages) >= 1
    assert window_manager.current in browsers
    assert window_manager.current.page in pages


def test_custom_browser_class(browser_context, page, testing_page_url):
    """Test WindowManager with custom browser class."""
    from conftest import CustomBrowser

    # Clean up any existing extra pages
    if len(browser_context.pages) > 1:
        for extra_page in browser_context.pages[1:]:
            try:
                if not extra_page.is_closed():
                    extra_page.close()
            except Exception:
                pass

    # Create WindowManager with custom browser class
    manager = WindowManager(browser_context, page, browser_class=CustomBrowser)

    # Current browser should be of custom class
    assert isinstance(manager.current, CustomBrowser)
    assert hasattr(manager.current, "product_version")
    assert manager.current.product_version == "1.0.0"

    # New browsers should also use custom class
    new_browser = manager.new_browser(testing_page_url, focus=False)
    assert isinstance(new_browser, CustomBrowser)
    assert new_browser.product_version == "1.0.0"


def test_new_browser_with_focus(window_manager, external_test_url, testing_page_url):
    """Test creating new browser with focus (default behavior)."""
    reset_to_clean_state(window_manager, testing_page_url)
    initial_browser = window_manager.current
    initial_count = len(window_manager.all_browsers)

    # Create new browser (focus=True by default)
    new_browser = window_manager.new_browser(external_test_url)

    # New browser becomes current
    assert window_manager.current is new_browser
    assert window_manager.current is not initial_browser
    assert len(window_manager.all_browsers) == initial_count + 1
    assert new_browser.url.rstrip("/") == external_test_url.rstrip("/")


def test_new_browser_without_focus(window_manager, external_test_url, testing_page_url):
    """Test creating new browser without focus."""
    reset_to_clean_state(window_manager, testing_page_url)
    initial_browser = window_manager.current
    initial_count = len(window_manager.all_browsers)

    # Create new browser without focus
    new_browser = window_manager.new_browser(external_test_url, focus=False)

    # Original browser remains current
    assert window_manager.current is initial_browser
    assert window_manager.current is not new_browser
    assert len(window_manager.all_browsers) == initial_count + 1


def test_switch_focus_between_browsers(window_manager, external_test_url, testing_page_url):
    """Test switching focus between browsers."""
    reset_to_clean_state(window_manager, testing_page_url)
    initial_browser = window_manager.current
    initial_page = initial_browser.page

    # Create second browser
    new_browser = window_manager.new_browser(external_test_url, focus=False)
    assert window_manager.current is initial_browser

    # Switch to new browser
    window_manager.switch_to(new_browser)
    assert window_manager.current is new_browser

    # Switch back using page instance (more reliable than browser object)
    window_manager.switch_to(initial_page)
    assert window_manager.current.page is initial_page


def test_close_current_browser(window_manager, external_test_url, testing_page_url):
    """Test closing current browser."""
    reset_to_clean_state(window_manager, testing_page_url)
    initial_count = len(window_manager.all_browsers)
    initial_url = window_manager.current.url

    # Create and switch to new browser
    new_browser = window_manager.new_browser(external_test_url)
    assert window_manager.current is new_browser
    assert len(window_manager.all_browsers) == initial_count + 1

    # Close current browser
    window_manager.close_browser()

    # Should switch to a remaining browser and count should decrease
    assert len(window_manager.all_browsers) == initial_count
    assert window_manager.current in window_manager.all_browsers
    # Should switch back to a browser with testing page (though not necessarily same object)
    assert window_manager.current.url == initial_url


def test_close_specific_browser(window_manager, external_test_url, testing_page_url):
    """Test closing specific browser without affecting current."""
    reset_to_clean_state(window_manager, testing_page_url)
    current_browser = window_manager.current
    initial_count = len(window_manager.all_browsers)

    # Create new browser without focus
    target_browser = window_manager.new_browser(external_test_url, focus=False)
    assert window_manager.current is current_browser

    # Close the specific browser
    window_manager.close_browser(target_browser)

    # Current should remain unchanged
    assert window_manager.current is current_browser
    assert len(window_manager.all_browsers) == initial_count
    assert target_browser not in window_manager.all_browsers


def test_close_extra_pages_except_current(window_manager, external_test_url, testing_page_url):
    """Test close_extra_pages default behavior - keeps current page."""
    reset_to_clean_state(window_manager, testing_page_url)
    current_browser = window_manager.current

    # Create multiple additional browsers
    browser2 = window_manager.new_browser(external_test_url, focus=False)
    browser3 = window_manager.new_browser(testing_page_url, focus=False)

    assert len(window_manager.all_pages) >= 3

    # Close all except current
    window_manager.close_extra_pages()

    # Current should remain, others should be closed
    assert not current_browser.is_browser_closed
    assert browser2.is_browser_closed
    assert browser3.is_browser_closed
    assert len(window_manager.all_pages) == 1


def test_close_extra_pages_including_current(window_manager, external_test_url, testing_page_url):
    """Test close_extra_pages with current=True - closes everything."""
    reset_to_clean_state(window_manager, testing_page_url)
    current_browser = window_manager.current

    # Create additional browsers
    browser2 = window_manager.new_browser(external_test_url, focus=False)
    browser3 = window_manager.new_browser(testing_page_url, focus=False)

    assert len(window_manager.all_pages) >= 3

    # Close all including current
    window_manager.close_extra_pages(current=True)

    # All should be closed
    assert current_browser.is_browser_closed
    assert browser2.is_browser_closed
    assert browser3.is_browser_closed
    assert len(window_manager.all_pages) == 0


def test_close_extra_pages_with_exceptions(
    isolated_window_manager, external_test_url, testing_page_url
):
    """Test that close_extra_pages handles exceptions gracefully."""
    reset_to_clean_state(isolated_window_manager, testing_page_url)

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
    window_manager, external_test_url, testing_page_url
):
    """Test that externally closed pages are automatically cleaned up."""
    reset_to_clean_state(window_manager, testing_page_url)
    initial_count = len(window_manager.all_browsers)

    # Create new browser
    new_browser = window_manager.new_browser(external_test_url, focus=False)
    new_page = new_browser.page
    assert len(window_manager.all_browsers) == initial_count + 1

    # Close page externally (not through WindowManager)
    new_page.close()

    # Accessing all_browsers should trigger cleanup
    browsers_after = window_manager.all_browsers
    assert len(browsers_after) == initial_count
    assert new_browser not in browsers_after


def test_automatic_popup_detection(
    window_manager, browser_context, external_test_url, testing_page_url
):
    """Test that popups/new pages are automatically detected and wrapped."""
    reset_to_clean_state(window_manager, testing_page_url)
    initial_count = len(window_manager.all_browsers)

    # Simulate popup by directly creating a new page in the context
    # This mimics what happens when a popup is opened programmatically
    new_page = browser_context.new_page()
    new_page.goto(external_test_url)

    # WindowManager should automatically detect and wrap the new page
    # Give it a moment to register the new page
    time.sleep(0.1)

    browsers_after = window_manager.all_browsers
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
    window_manager.switch_to(new_browser)
    assert window_manager.current is new_browser


def test_error_handling_nonexistent_page(window_manager, browser_context, testing_page_url):
    """Test error handling for invalid operations."""
    reset_to_clean_state(window_manager, testing_page_url)

    # Create and immediately close external page
    external_page = browser_context.new_page()
    external_page.close()

    # Should raise error when trying to switch to closed page
    with pytest.raises(NoSuchElementException, match="The specified Page handle does not exist"):
        window_manager.switch_to(external_page)


def test_empty_state_handling(browser_context, testing_page_url):
    """Test handling of empty state (no pages remaining)."""
    # Close all existing pages
    for page in list(browser_context.pages):
        try:
            if not page.is_closed():
                page.close()
        except Exception:
            pass

    # Create WindowManager and immediately close the page
    page = browser_context.new_page()
    page.goto(testing_page_url)
    manager = WindowManager(browser_context, page)
    page.close()

    # Should handle empty state gracefully
    assert len(manager.all_browsers) == 0
    assert len(manager.all_pages) == 0

    # Methods should not crash on empty state
    manager.close_extra_pages()
    manager.close_extra_pages(current=True)


def test_browser_workflow_integration(window_manager, external_test_url, testing_page_url):
    """Test complete workflow: create, switch, and close browsers."""
    reset_to_clean_state(window_manager, testing_page_url)

    # Verify starting state
    initial_browser = window_manager.current
    assert initial_browser.url.endswith("testing_page.html")
    initial_count = len(window_manager.all_browsers)

    # Create background browser (no focus change)
    bg_browser = window_manager.new_browser(f"{external_test_url}#bg", focus=False)
    assert window_manager.current is initial_browser  # Should not change
    assert len(window_manager.all_browsers) > initial_count  # Should increase

    # Create focused browser (focus should change)
    focus_browser = window_manager.new_browser(f"{testing_page_url}#focus", focus=True)
    assert window_manager.current is focus_browser  # Should change to new browser

    # Test switching between browsers
    window_manager.switch_to(bg_browser)
    assert window_manager.current is bg_browser
    assert bg_browser.url.endswith("external_test_page.html#bg")

    window_manager.switch_to(focus_browser)
    assert window_manager.current is focus_browser
    assert focus_browser.url.endswith("testing_page.html#focus")

    # Close a browser and verify cleanup
    browser_count_before_close = len(window_manager.all_browsers)
    window_manager.close_browser(bg_browser)
    browser_count_after_close = len(window_manager.all_browsers)

    # Verify browser was removed from collection
    assert browser_count_after_close < browser_count_before_close
    assert bg_browser not in window_manager.all_browsers

    # Verify current browser is still valid
    assert window_manager.current in window_manager.all_browsers
    assert not window_manager.current.is_browser_closed
