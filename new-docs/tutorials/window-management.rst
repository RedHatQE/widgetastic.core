==================
Window Management
==================

This tutorial demonstrates window and popup management in Widgetastic.core using the framework's test pages. You'll learn to handle multiple browser windows, tabs, and popups using ``popup_test_page.html`` and ``external_test_page.html``.

.. note::
   **Prerequisites**: Basic widgets tutorial
   **Test Pages Used**: ``popup_test_page.html``, ``external_test_page.html``, ``testing_page.html``

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Understand the WindowManager system
* ✅ Handle popup windows and new tabs
* ✅ Switch between multiple browser contexts
* ✅ Manage browser lifecycle and cleanup
* ✅ Handle cross-page automation workflows

Setting Up Window Management
============================

.. code-block:: python

    from pathlib import Path
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser, WindowManager

    def setup_window_manager():
        """Setup WindowManager with popup test page."""
        # Get test page paths
        popup_page_path = Path("testing/html/popup_test_page.html").resolve()
        popup_page_url = popup_page_path.as_uri()

        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()

        # Create initial page
        page = context.new_page()
        page.goto(popup_page_url)

        # Initialize WindowManager
        window_manager = WindowManager(context, page)

        return window_manager, p, browser_instance, context

    window_manager, playwright, browser_instance, context = setup_window_manager()

Basic Window Operations
=======================

The WindowManager provides methods for creating and managing multiple browser windows:

**Creating New Windows**

.. code-block:: python

    # Get external test page URL
    external_page_path = Path("testing/html/external_test_page.html").resolve()
    external_url = external_page_path.as_uri()

    # Current browser
    initial_browser = window_manager.current
    print(f"Initial browser URL: {initial_browser.url}")
    print(f"Total browsers: {len(window_manager.all_browsers)}")

    # Create new window/browser with focus (becomes current)
    new_browser = window_manager.new_browser(external_url, focus=True)
    print(f"New browser URL: {new_browser.url}")
    print(f"Current browser changed: {window_manager.current is new_browser}")
    print(f"Total browsers: {len(window_manager.all_browsers)}")

    # Create background window/browser (doesn't change focus)
    bg_browser = window_manager.new_browser(external_url, focus=False)
    print(f"Current browser unchanged: {window_manager.current is new_browser}")
    print(f"Total browsers: {len(window_manager.all_browsers)}")

**Switching Between Windows**

.. code-block:: python

    # Switch to different browser by instance
    window_manager.switch_to(bg_browser)
    print(f"Switched to background browser: {window_manager.current is bg_browser}")

    # Switch back to original browser
    window_manager.switch_to(initial_browser)
    print(f"Switched back to initial browser: {window_manager.current is initial_browser}")

    # Switch by page instance
    window_manager.switch_to(new_browser.page)
    print(f"Switched using page reference: {window_manager.current.page is new_browser.page}")


Handling Popups and New Tabs
============================

Manage popup windows and new tabs created by JavaScript. Widgetastic provides two approaches:
reliable detection using ``expect_new_page()`` context manager, and automatic detection via
``all_browsers`` property.

**Reliable Popup Detection with `expect_new_page()`**

The recommended approach for handling popups and new tabs is using the ``expect_new_page()``
context manager. This method uses Playwright's native ``expect_page()`` to reliably wait for
and capture new pages opened by JavaScript or links.

.. code-block:: python

    from widgetastic.widget import View, Text

    class PopupPageView(View):
        """View for popup_test_page.html"""
        open_popup_button = Text("#open-popup")
        open_tab_button = Text("#open-new-tab")
        external_link = Text("#external-link")

    # Navigate to popup test page
    window_manager.switch_to(initial_browser)
    popup_view = PopupPageView(window_manager.current)

    print(f"Initial browser count: {len(window_manager.all_browsers)}")

    # Method 1: Handle JavaScript popup window
    with window_manager.expect_new_page(timeout=5.0) as popup_browser:
        popup_view.open_popup_button.click()

    print(f"✓ Popup opened and captured")
    print(f"Popup browser URL: {popup_browser.url}")
    print(f"Popup browser title: {popup_browser.title}")
    print(f"Total browsers: {len(window_manager.all_browsers)}")

    # Verify popup is in all_browsers
    assert popup_browser in window_manager.all_browsers
    print(f"✓ Popup browser is tracked in all_browsers")

    # Handle new tab opened by JavaScript
    with window_manager.expect_new_page(timeout=5.0) as new_tab_browser:
        popup_view.open_tab_button.click()

    print(f"✓ New tab opened and captured")
    print(f"New tab URL: {new_tab_browser.url}")

    # Handle link with target="_blank"
    with window_manager.expect_new_page(timeout=5.0) as external_browser:
        popup_view.external_link.click()

    print(f"✓ External link opened in new tab")
    print(f"External browser URL: {external_browser.url}")

    # Clean up opened browsers
    window_manager.close_browser(popup_browser)
    window_manager.close_browser(new_tab_browser)
    window_manager.close_browser(external_browser)


**Working with `all_browsers` Property**

The ``all_browsers`` property provides automatic cleanup and best-effort detection of new pages.
It's useful for listing all active browsers, but for reliable popup detection, use ``expect_new_page()``.

.. code-block:: python

    # Get all active browsers with automatic cleanup
    all_browsers = window_manager.all_browsers
    print(f"Currently managing {len(all_browsers)} windows")

    # Iterate through all browsers
    for i, browser in enumerate(all_browsers):
        print(f"Window {i}: {browser.title} - {browser.url}")

    # all_browsers automatically cleans up closed pages
    test_browser = window_manager.new_browser(external_url, focus=False)
    print(f"Before close: {len(window_manager.all_browsers)} browsers")

    window_manager.close_browser(test_browser)
    print(f"After close: {len(window_manager.all_browsers)} browsers")


Cross-Window Automation Workflows
=================================

Coordinate actions across multiple browser windows:

**Multi-Window Form Workflow**

.. code-block:: python

    class MainPageForm(View):
        """Form on main popup test page"""
        title = Text("h1")

    class ExternalPageForm(View):
        """Form on external test page"""
        title = Text("h1")
        button = Text(id="external-button")
        input_field = TextInput(id="external-input")

    def multi_window_workflow():
        """Demonstrate cross-window automation."""
        results = {}

        # Step 1: Work with main window
        window_manager.switch_to(initial_browser)
        main_form = MainPageForm(window_manager.current)
        results['main_title'] = main_form.title.read()

        # Step 2: Switch to external window
        if auto_detected_browser:
            window_manager.switch_to(auto_detected_browser)
            external_form = ExternalPageForm(window_manager.current)

            # Fill external form
            results['external_title'] = external_form.title.read()
            external_form.input_field.fill("Cross-window data")
            results['input_value'] = external_form.input_field.read()

        # Step 3: Return to main window
        window_manager.switch_to(initial_browser)
        results['back_to_main'] = main_form.title.read()

        return results

    # Execute multi-window workflow
    workflow_results = multi_window_workflow()
    print(f"Workflow results: {workflow_results}")
