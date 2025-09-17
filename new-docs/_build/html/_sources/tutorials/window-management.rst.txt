==========================
Window Management Tutorial
==========================

This tutorial demonstrates window and popup management in Widgetastic.core using the framework's test pages. You'll learn to handle multiple browser windows, tabs, and popups using ``popup_test_page.html`` and ``external_test_page.html``.

.. note::
   **Time Required**: 30 minutes
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

Understanding Window Management in Widgetastic
==============================================

Widgetastic.core provides the ``WindowManager`` class to handle multiple browser windows/pages:

* **Window Creation**: Open new browser windows/tabs programmatically
* **Context Switching**: Switch focus between different browser contexts
* **Lifecycle Management**: Automatically track and cleanup browser instances
* **Popup Detection**: Automatically detect and wrap popup windows
* **Isolation**: Each window maintains independent state and context

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

    # Create new browser with focus (becomes current)
    new_browser = window_manager.new_browser(external_url, focus=True)
    print(f"New browser URL: {new_browser.url}")
    print(f"Current browser changed: {window_manager.current is new_browser}")
    print(f"Total browsers: {len(window_manager.all_browsers)}")

    # Create background browser (doesn't change focus)
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

    # Switch by page instance (more reliable)
    window_manager.switch_to(new_browser.page)
    print(f"Switched using page reference: {window_manager.current.page is new_browser.page}")

Window Management with Views
============================

Use Views to interact with different windows:

**Multi-Window View Setup**

.. code-block:: python

    from widgetastic.widget import View, Text

    class PopupPageView(View):
        """View for popup_test_page.html"""
        title = Text("h1")
        open_popup_button = Text(id="open-popup")
        open_tab_button = Text(id="open-new-tab")
        external_link = Text(id="external-link")

    class ExternalPageView(View):
        """View for external_test_page.html"""
        title = Text("h1")
        external_button = Text(id="external-button")
        external_input = Text(id="external-input")

    # Use views with different browsers
    popup_view = PopupPageView(window_manager.current)
    print(f"Popup page title: {popup_view.title.read()}")

    # Switch to external page browser and create view
    window_manager.switch_to(new_browser)
    external_view = ExternalPageView(window_manager.current)
    print(f"External page title: {external_view.title.read()}")

Handling Popups and New Tabs
============================

Manage popup windows and new tabs created by JavaScript:

**Popup Window Handling**

.. code-block:: python

    class AutomatedPopupHandling(View):
        open_popup_btn = Text(id="open-popup")
        open_tab_btn = Text(id="open-new-tab")

    # Switch to popup page
    window_manager.switch_to(initial_browser)
    popup_handler = AutomatedPopupHandling(window_manager.current)

    print(f"Initial browser count: {len(window_manager.all_browsers)}")

    # Programmatic popup creation (simulates user click)
    initial_count = len(window_manager.all_browsers)

    # Create popup programmatically (testing approach)
    testing_page_url = Path("testing/html/testing_page.html").resolve().as_uri()
    popup_browser = window_manager.new_browser(testing_page_url, focus=False)

    print(f"Popup created. Browser count: {len(window_manager.all_browsers)}")
    print(f"Popup browser URL: {popup_browser.url}")

    # WindowManager automatically tracks all browsers
    all_browsers = window_manager.all_browsers
    print(f"All browser URLs: {[b.url for b in all_browsers]}")

**Automatic Popup Detection**

.. code-block:: python

    # WindowManager automatically detects new pages/popups
    def demonstrate_popup_detection():
        """Demonstrate automatic popup detection."""
        initial_count = len(window_manager.all_browsers)

        # Simulate popup by creating new page in context
        new_page = context.new_page()
        external_url = Path("testing/html/external_test_page.html").resolve().as_uri()
        new_page.goto(external_url)

        # Give WindowManager time to detect new page
        import time
        time.sleep(0.1)

        # Verify automatic detection
        current_count = len(window_manager.all_browsers)
        print(f"Browsers before: {initial_count}, after: {current_count}")

        # Find the new browser
        new_browser = None
        for browser in window_manager.all_browsers:
            if browser.page is new_page:
                new_browser = browser
                break

        if new_browser:
            print(f"✓ New page automatically wrapped as Browser")
            print(f"New browser URL: {new_browser.url}")
            return new_browser
        else:
            print("✗ New page not automatically detected")
            return None

    auto_detected_browser = demonstrate_popup_detection()

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

Window Lifecycle Management
===========================

Properly manage browser lifecycle and cleanup:

**Closing Browsers**

.. code-block:: python

    print(f"Browsers before cleanup: {len(window_manager.all_browsers)}")

    # Close specific browser
    if auto_detected_browser:
        window_manager.close_browser(auto_detected_browser)
        print(f"Closed auto-detected browser")

    # Close current browser (switches to another automatically)
    current_before_close = window_manager.current
    window_manager.close_browser()
    current_after_close = window_manager.current

    print(f"Current browser changed: {current_before_close is not current_after_close}")
    print(f"Browsers after closing current: {len(window_manager.all_browsers)}")

**Bulk Cleanup Operations**

.. code-block:: python

    # Create multiple browsers for cleanup demonstration
    test_browsers = []
    for i in range(3):
        test_url = f"{external_url}#test{i}"
        test_browser = window_manager.new_browser(test_url, focus=False)
        test_browsers.append(test_browser)

    print(f"Created test browsers. Total: {len(window_manager.all_browsers)}")

    # Close extra pages (keeps current)
    window_manager.close_extra_pages()
    print(f"After closing extra pages: {len(window_manager.all_browsers)}")

    # Verify main browser still works
    current_browser = window_manager.current
    print(f"Current browser still functional: {not current_browser.is_browser_closed}")

    # Close all pages including current
    window_manager.close_extra_pages(current=True)
    print(f"After closing all pages: {len(window_manager.all_browsers)}")

Advanced Window Management
==========================

Handle complex scenarios and edge cases:

**Error Handling**

.. code-block:: python

    from widgetastic.exceptions import NoSuchElementException

    def robust_window_switching():
        """Demonstrate robust window switching with error handling."""
        try:
            # Create new browser for testing
            test_browser = window_manager.new_browser(external_url, focus=False)

            # Close it externally (not through WindowManager)
            test_browser.page.close()

            # Try to switch to closed browser - should raise error
            try:
                window_manager.switch_to(test_browser.page)
                print("ERROR: Should have raised exception for closed page")
            except NoSuchElementException as e:
                print(f"✓ Correctly handled closed page: {e}")

            # WindowManager should clean up closed browsers automatically
            browsers_after = window_manager.all_browsers
            closed_browser_present = any(b.page is test_browser.page for b in browsers_after)
            print(f"✓ Closed browser cleaned up: {not closed_browser_present}")

        except Exception as e:
            print(f"Unexpected error in window switching: {e}")

    robust_window_switching()

**Custom Browser Classes**

.. code-block:: python

    # Define custom browser class with additional functionality
    class CustomBrowser(Browser):
        @property
        def product_version(self):
            return "1.0.0"

        def custom_method(self):
            return "Custom functionality"

    # Create WindowManager with custom browser class
    def setup_custom_window_manager():
        """Setup WindowManager with custom browser class."""
        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()

        popup_page_url = Path("testing/html/popup_test_page.html").resolve().as_uri()
        page.goto(popup_page_url)

        # Use custom browser class
        custom_window_manager = WindowManager(context, page, browser_class=CustomBrowser)

        return custom_window_manager, p, browser_instance, context

    custom_wm, custom_p, custom_bi, custom_ctx = setup_custom_window_manager()

    # Verify custom browser class is used
    current_custom = custom_wm.current
    print(f"Custom browser class: {isinstance(current_custom, CustomBrowser)}")
    print(f"Product version: {current_custom.product_version}")
    print(f"Custom method: {current_custom.custom_method()}")

    # New browsers also use custom class
    new_custom_browser = custom_wm.new_browser(external_url, focus=False)
    print(f"New browser is custom: {isinstance(new_custom_browser, CustomBrowser)}")

Real-World Window Management Patterns
=====================================

Practical patterns for common automation scenarios:

**E-commerce Checkout Flow**

.. code-block:: python

    class ECommerceWindowManager:
        """Manage e-commerce multi-window workflows."""

        def __init__(self, window_manager):
            self.wm = window_manager

        def handle_payment_popup(self, payment_url):
            """Handle payment popup window."""
            # Create payment window
            payment_browser = self.wm.new_browser(payment_url, focus=True)

            # Process payment (simplified)
            payment_view = ExternalPageView(payment_browser)
            payment_result = payment_view.title.read()

            # Close payment window and return to main
            self.wm.close_browser(payment_browser)

            return payment_result

        def compare_products(self, product_urls):
            """Open multiple product pages for comparison."""
            product_browsers = []

            for url in product_urls:
                browser = self.wm.new_browser(url, focus=False)
                product_browsers.append(browser)

            # Collect product data
            products = []
            for browser in product_browsers:
                self.wm.switch_to(browser)
                product_view = ExternalPageView(browser)
                products.append(product_view.title.read())

            # Cleanup comparison windows
            for browser in product_browsers:
                self.wm.close_browser(browser)

            return products

    # Demonstrate e-commerce patterns
    ecommerce = ECommerceWindowManager(custom_wm)

    # Simulate product comparison
    product_urls = [f"{external_url}#product{i}" for i in range(2)]
    products = ecommerce.compare_products(product_urls)
    print(f"Product comparison results: {products}")

**Help/Documentation Windows**

.. code-block:: python

    class HelpWindowManager:
        """Manage help and documentation windows."""

        def __init__(self, window_manager):
            self.wm = window_manager
            self.help_windows = []

        def open_help_window(self, help_url, keep_focus_on_main=True):
            """Open help window without losing focus on main workflow."""
            help_browser = self.wm.new_browser(help_url, focus=not keep_focus_on_main)
            self.help_windows.append(help_browser)
            return help_browser

        def close_all_help_windows(self):
            """Close all help windows."""
            for help_browser in self.help_windows:
                if not help_browser.is_browser_closed:
                    self.wm.close_browser(help_browser)
            self.help_windows.clear()

        def get_help_content(self, help_browser):
            """Extract content from help window."""
            self.wm.switch_to(help_browser)
            help_view = ExternalPageView(help_browser)
            return help_view.title.read()

    # Demonstrate help window management
    help_manager = HelpWindowManager(custom_wm)

    # Open help without losing main focus
    help_browser = help_manager.open_help_window(external_url)
    help_content = help_manager.get_help_content(help_browser)
    print(f"Help content: {help_content}")

    # Verify main window still focused
    print(f"Main window still current: {custom_wm.current is not help_browser}")

    # Cleanup help windows
    help_manager.close_all_help_windows()

Best Practices Summary
======================

**Window Management Guidelines**

.. code-block:: python

    # 1. Always use WindowManager for multi-window scenarios
    # ✓ Good
    window_manager = WindowManager(context, initial_page)
    new_browser = window_manager.new_browser(url)

    # ✗ Avoid direct page creation without WindowManager
    # new_page = context.new_page()  # Not tracked by WindowManager

    # 2. Use focus parameter strategically
    # Background operations
    bg_browser = window_manager.new_browser(url, focus=False)

    # User-facing operations
    main_browser = window_manager.new_browser(url, focus=True)

    # 3. Clean up resources properly
    try:
        # Your multi-window automation
        pass
    finally:
        # Cleanup all windows
        window_manager.close_extra_pages(current=True)
        context.close()
        browser_instance.close()
        playwright.stop()

    # 4. Handle errors gracefully
    def safe_window_operation(window_manager, operation):
        """Safely perform window operations."""
        try:
            return operation()
        except NoSuchElementException:
            print("Window/page no longer exists")
            return None
        except Exception as e:
            print(f"Unexpected window error: {e}")
            return None

    # 5. Use descriptive browser references
    main_browser = window_manager.current
    payment_browser = window_manager.new_browser(payment_url)
    help_browser = window_manager.new_browser(help_url, focus=False)

**Performance Optimization**

.. code-block:: python

    # Batch window operations
    def batch_window_operations(window_manager, operations):
        """Perform multiple window operations efficiently."""
        results = {}

        for window_id, operation in operations.items():
            try:
                browser = operation['browser']
                window_manager.switch_to(browser)

                # Perform operation
                result = operation['action']()
                results[window_id] = result

            except Exception as e:
                results[window_id] = f"Error: {e}"

        return results

    # Usage example
    operations = {
        'main': {
            'browser': custom_wm.current,
            'action': lambda: "Main window operation"
        }
    }

    batch_results = batch_window_operations(custom_wm, operations)
    print(f"Batch results: {batch_results}")

Final Cleanup
=============

.. code-block:: python

    # Clean up all resources
    try:
        window_manager.close_extra_pages(current=True)
        custom_wm.close_extra_pages(current=True)
    except:
        pass

    try:
        context.close()
        custom_ctx.close()
    except:
        pass

    try:
        browser_instance.close()
        custom_bi.close()
    except:
        pass

    try:
        playwright.stop()
        custom_p.stop()
    except:
        pass

Summary
=======

Window Management in Widgetastic.core provides:

* **Automatic Tracking**: All browser windows/tabs are automatically tracked
* **Context Switching**: Easy switching between different browser contexts
* **Lifecycle Management**: Automatic cleanup of closed windows
* **Popup Handling**: Automatic detection and wrapping of popup windows
* **Custom Browser Support**: Use custom browser classes with additional functionality

Key takeaways:
* Use WindowManager for all multi-window scenarios
* Handle window lifecycle properly with cleanup
* Use focus parameter strategically for user experience
* Implement error handling for robust automation
* Batch operations for better performance

This completes the window management tutorial. You can now handle complex multi-window automation scenarios in your web applications.
