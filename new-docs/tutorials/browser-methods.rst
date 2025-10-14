============================
Browser Methods and Elements
============================

The Browser class is the foundation of widgetastic, providing methods for interacting with web pages and elements. This tutorial covers essential browser operations and element interaction patterns.

.. note::
   **Prerequisites**: Complete :doc:`basic-widgets` and :doc:`views` tutorials first.

Browser Class Overview
======================

The widgetastic Browser wraps Playwright's ``Page`` object with additional intelligence for reliable automation. It provides comprehensive web interaction capabilities while maintaining compatibility with the proven widgetastic API.

**Key Features:**

* **Smart Element Selection**: Intelligently selects visible and interactable elements
* **Robust Text Handling**: Normalized text operations with multiple extraction strategies
* **Enhanced Click Operations**: Handles overlays, animations, and dynamic positioning
* **Frame Context Management**: Seamless iframe handling with automatic context switching
* **Network Activity Monitoring**: Page safety checks for stable interactions

**Browser Initialization**

.. code-block:: python

    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser

    # Setup Playwright and create Browser
    playwright = sync_playwright().start()
    browser_instance = playwright.chromium.launch(headless=False)
    context = browser_instance.new_context()
    page = context.new_page()

    # Create widgetastic Browser
    browser = Browser(page)

    # Navigate to test page
    page.goto("file:///path/to/testing/html/testing_page.html")

Browser Properties and Information
===================================

The Browser class provides several properties for accessing browser and page information:

.. code-block:: python

    # Page URL (can be read or set)
    current_url = browser.url
    browser.url = "https://example.com"  # Navigate by setting URL

    # Page title
    page_title = browser.title
    print(f"Current page: {page_title}")

    # Browser information
    browser_engine = browser.browser_type    # "chromium", "firefox", etc.
    major_version = browser.browser_version  # 119, 120, etc.
    is_closed = browser.is_browser_closed   # True/False

    # Screenshots
    browser.save_screenshot("/path/to/screenshot.png")

    # Page management
    browser.refresh()  # Reload current page
    browser.close()    # Close browser page

Element Finding and Selection
=============================

The Browser provides sophisticated element finding with smart selection strategies and comprehensive element collection methods.

**Basic Element Finding**

.. code-block:: python

    # Find single elements using different strategies
    title_element = browser.element("h1#wt-core-title")
    text_input = browser.element("#input")
    button = browser.element("//button[@id='a_button']")

    # Find multiple elements
    all_buttons = browser.elements("button")  # List of all button elements
    section_headers = browser.elements(".section-header")

    # Element finding with parent scoping
    table = browser.element("#with-thead")
    table_rows = browser.elements("tr", parent=table)

    # Check if elements exist
    exists = browser.is_displayed("h1#wt-core-title")  # True
    missing = browser.is_displayed("#non-existent")    # False

**Smart Element Selection**

When multiple elements match, Browser intelligently selects the most suitable one:

.. code-block:: python

    # Multiple elements with same class - selects visible, interactable one
    sections = browser.elements(".section-header")  # Gets all matching elements
    first_section = browser.element(".section-header")  # Gets best single match

    print(f"Found {len(sections)} sections")
    print(f"Selected section text: {browser.text(first_section)}")

Element Interaction Methods
============================

**Clicking Elements**

.. code-block:: python

    # Basic clicking
    browser.click("#a_button")

    # Click with specific button (left=0, middle=1, right=2)
    browser.click("#multi_button", button=0)  # Left click
    browser.click("#multi_button", button=2)  # Right click

    # Click at specific coordinates (relative to element)
    browser.click("#a_button", x_offset=10, y_offset=5)

    # Force click (bypasses actionability checks)
    browser.click("#disabled_button", force=True)

**Text Input Operations**

.. code-block:: python

    # Clear and type text
    browser.clear("#input")
    browser.send_keys("Hello World", "#input")

    # Fill input (clears then types)
    browser.fill("New Value", "#input")

    # Type without clearing first
    browser.send_keys("Additional text", "#input", clear_first=False)

    # Sensitive data (not logged)
    browser.send_keys("password123", "#password", sensitive=True)

**Reading Element Content**

.. code-block:: python

    # Get text content
    title_text = browser.text("h1#wt-core-title")
    print(f"Page title: {title_text}")

    # Get input values
    input_value = browser.input_value("#input")
    number_value = browser.input_value("#input_number")

    # Get element attributes
    placeholder = browser.get_attribute("#input", "placeholder")
    element_id = browser.get_attribute("#a_button", "id")

    # Get computed styles
    color = browser.get_css_value("#a_button", "background-color")
    display = browser.get_css_value("#invisible", "display")

Element State Checking
=======================

**Visibility and Display States**

.. code-block:: python

    # Check if element is visible on page
    title_visible = browser.is_displayed("h1#wt-core-title")     # True
    hidden_visible = browser.is_displayed("#invisible")          # False (display: none)

    # Check if element is in viewport
    in_viewport = browser.is_visible("#a_button")

    # Wait for element to appear
    browser.wait_for_element("#invisible_appear_p", visible=True, timeout=5000)

**Interaction States**

.. code-block:: python

    # Check if element can be interacted with
    button_enabled = browser.is_enabled("#a_button")           # True
    disabled_enabled = browser.is_enabled("#disabled_button")  # False

    # Check checkbox/radio states
    checkbox_checked = browser.is_checked("#input2")          # False initially
    browser.check("#input2")
    checkbox_checked = browser.is_checked("#input2")          # True after check

    # Check select values
    selected_value = browser.selected_option("#myselect")
    selected_text = browser.selected_text("#myselect")

Wait Strategies
===============

**Smart Waiting**

.. code-block:: python

    # Wait for element to be actionable
    browser.wait_for_element("#dynamic_content", timeout=10000)

    # Wait for element to disappear
    browser.wait_for_element("#loading_spinner", visible=False, timeout=30000)

    # Wait for specific text content
    browser.wait_for_text("#status", "Complete", timeout=15000)

    # Wait for custom condition
    browser.wait_for(lambda: browser.text("#counter") == "100", timeout=10000)

**Network and Page State Waiting**

.. code-block:: python

    # Wait for network to be idle
    browser.wait_for_network_idle(timeout=5000)

    # Wait for page load events
    browser.wait_for_page_ready()

    # Wait for specific URL
    browser.wait_for_url_contains("/dashboard", timeout=10000)

Form and Input Operations
=========================

**Checkbox and Radio Controls**

.. code-block:: python

    # Checkbox operations
    browser.check("#input2")          # Check checkbox
    browser.uncheck("#input2")        # Uncheck checkbox
    browser.set_checked("#input2", True)  # Set to specific state

    # Radio button selection
    browser.check("input[name='radio_input'][value='x']")
    selected = browser.selected_option("input[name='radio_input']:checked")

**Select Dropdown Operations**

.. code-block:: python

    # Select by visible text
    browser.select_by_text("#myselect", "myoption")

    # Select by value
    browser.select_by_value("#myselect", "test")

    # Multiple selection
    browser.select_multiple("#multi_select", ["foo", "baz"])

    # Get all options
    options = browser.select_options("#myselect")
    print(f"Available options: {options}")

File Upload Operations
======================

.. code-block:: python

    # Upload single file
    browser.upload_file("#fileinput", "/path/to/file.txt")

    # Upload multiple files
    browser.upload_files("#fileinput", [
        "/path/to/file1.txt",
        "/path/to/file2.pdf"
    ])

    # Check uploaded file name
    uploaded_files = browser.uploaded_files("#fileinput")

Drag and Drop Operations
========================

**Basic Drag and Drop**

.. code-block:: python

    # Drag from source to target
    browser.drag_and_drop("#drag_source", "#drop_target")

    # Drag by offset (pixels)
    browser.drag_and_drop_by_offset("#drag_source2", x_offset=100, y_offset=50)

    # Drag to specific coordinates
    browser.drag_and_drop_to("#drag_source", to_x=200, to_y=300)

**Advanced Drag Operations**

.. code-block:: python

    # Get drag coordinates for verification
    start_coords = browser.element_coordinates("#drag_source")
    print(f"Start position: {start_coords}")

    # Perform drag with custom steps
    browser.drag_and_drop("#drag_source", "#drop_target", steps=5)

    # Sortable list reordering
    browser.drag_and_drop(".sortable-item[data-sort-id='item-1']",
                         ".sortable-item[data-sort-id='item-3']")

Screenshot and Visual Operations
================================

**Taking Screenshots**

.. code-block:: python

    # Full page screenshot
    screenshot_bytes = browser.screenshot()
    with open("page.png", "wb") as f:
        f.write(screenshot_bytes)

    # Element screenshot
    element_screenshot = browser.screenshot("#a_button")
    with open("button.png", "wb") as f:
        f.write(element_screenshot)

    # Screenshot with options
    full_page_screenshot = browser.screenshot(full_page=True, quality=90)

**Element Measurements**

.. code-block:: python

    # Get element size
    size = browser.size_of("#exact_dimensions")
    print(f"Element size: {size}")  # (100, 50)

    # Get element position
    position = browser.coordinates_of("#a_button")
    print(f"Button position: {position}")

    # Get bounding box
    bbox = browser.bounding_box("#drag_source")
    print(f"Bounding box: {bbox}")

Alert and Dialog Handling
==========================

**JavaScript Alerts**

.. code-block:: python

    # Handle alert dialogs
    browser.click("#alert_button")  # Triggers alert

    # Accept alert
    browser.handle_alert(cancel=False, text="Widget Name")

    # Cancel/dismiss alert
    browser.handle_alert(cancel=True)

    # Get alert text before handling
    alert_text = browser.alert_text()
    print(f"Alert message: {alert_text}")

**Custom Dialog Handling**

.. code-block:: python

    # Setup alert handler
    def handle_confirm(dialog):
        print(f"Dialog type: {dialog.type}")
        print(f"Dialog message: {dialog.message}")
        dialog.accept()  # or dialog.dismiss()

    browser.page.on("dialog", handle_confirm)
    browser.click("#confirm_button")

Mouse and Keyboard Operations
=============================

**Mouse Operations**

.. code-block:: python

    # Hover over elements
    browser.hover("#hover_target")

    # Double click
    browser.double_click("#double_click_area")

    # Right click (context menu)
    browser.right_click("#context_menu_trigger")

    # Mouse down/up for custom interactions
    browser.mouse_down("#drag_handle")
    browser.mouse_move(100, 50)  # Relative movement
    browser.mouse_up()

**Keyboard Operations**

.. code-block:: python

    # Send key combinations
    browser.key_press("Escape")
    browser.key_press("Control+A")
    browser.key_press("Control+C")

    # Type special characters
    browser.key_type("Tab")
    browser.key_type("Enter")
    browser.key_type("ArrowDown")

    # Focus element first
    browser.focus("#input")
    browser.key_type("Control+A")  # Select all in focused input

Scroll and Viewport Operations
==============================

**Scrolling**

.. code-block:: python

    # Scroll element into view
    browser.scroll_into_view("#footer_element")

    # Scroll by pixels
    browser.scroll(x=0, y=500)

    # Scroll to element
    browser.scroll_to_element("#target_section")

    # Scroll within specific element
    browser.scroll_in_element("#scrollable_container", x=0, y=100)

**Viewport Operations**

.. code-block:: python

    # Set viewport size
    browser.set_viewport_size(1920, 1080)

    # Get current viewport
    viewport = browser.viewport_size()
    print(f"Viewport: {viewport}")

    # Check if element is in viewport
    in_view = browser.is_in_viewport("#visible_element")

Advanced Browser Operations
===========================

**Page Navigation**

.. code-block:: python

    # Navigation controls
    browser.back()
    browser.forward()
    browser.reload()

    # Navigate to URL
    browser.goto("https://example.com")

    # Get current URL
    current_url = browser.current_url()

    # Wait for navigation
    browser.wait_for_navigation(lambda: browser.click("#submit"))

**Browser Context Operations**

.. code-block:: python

    # Execute JavaScript
    result = browser.execute_script("return document.title;")
    print(f"Page title from JS: {result}")

    # Execute with arguments
    element_text = browser.execute_script(
        "return arguments[0].textContent;",
        browser.element("#a_button")
    )

    # Set cookies
    browser.set_cookie("session_id", "abc123")

    # Get cookies
    cookies = browser.get_cookies()

Performance and Debugging
==========================

**Performance Timing**

.. code-block:: python

    import time

    # Time operations
    start_time = time.time()
    browser.click("#slow_button")
    browser.wait_for_text("#result", "Complete")
    duration = time.time() - start_time
    print(f"Operation took {duration:.2f} seconds")

**Debug Information**

.. code-block:: python

    # Get element information for debugging
    element_info = browser.debug_element("#problematic_element")
    print(f"Element debug info: {element_info}")

    # Log browser console messages
    def log_console(msg):
        print(f"Console {msg.type}: {msg.text}")

    browser.page.on("console", log_console)

Error Handling Patterns
========================

**Robust Element Interaction**

.. code-block:: python

    def safe_click(browser, locator, timeout=5000):
        """Safely click an element with proper error handling"""
        try:
            browser.wait_for_element(locator, timeout=timeout)
            if browser.is_enabled(locator):
                browser.click(locator)
                return True
            else:
                print(f"Element {locator} is not enabled")
                return False
        except Exception as e:
            print(f"Failed to click {locator}: {e}")
            return False

    # Usage
    success = safe_click(browser, "#submit_button")
    if success:
        print("Click successful")

**Conditional Operations**

.. code-block:: python

    def conditional_fill(browser, locator, value):
        """Fill input only if it exists and is different"""
        if browser.is_displayed(locator):
            current_value = browser.input_value(locator)
            if current_value != value:
                browser.fill(value, locator)
                print(f"Filled {locator} with {value}")
            else:
                print(f"{locator} already has correct value")
        else:
            print(f"{locator} not found on page")

Best Practices
==============

**1. Use Appropriate Wait Strategies**

.. code-block:: python

    # Good: Wait for specific conditions
    browser.wait_for_element("#dynamic_content", visible=True)
    browser.click("#dynamic_content")

    # Avoid: Arbitrary sleep times
    import time
    time.sleep(5)  # Unreliable

**2. Verify Element States**

.. code-block:: python

    # Good: Check before interaction
    if browser.is_displayed("#submit_btn") and browser.is_enabled("#submit_btn"):
        browser.click("#submit_btn")

    # Avoid: Assuming elements are ready
    browser.click("#submit_btn")  # May fail if not ready

**3. Use Specific Locators**

.. code-block:: python

    # Good: Specific, unique locators
    browser.click("#submit-form-button")

    # Avoid: Generic, ambiguous locators
    browser.click("button")  # Which button?

**4. Handle Network Timing**

.. code-block:: python

    # Good: Wait for network stability after actions
    browser.click("#load_data_btn")
    browser.wait_for_network_idle()
    result = browser.text("#data_result")

    # Avoid: Not waiting for async operations
    browser.click("#load_data_btn")
    result = browser.text("#data_result")  # May be empty

Summary
=======

The Browser class provides comprehensive methods for web automation:

* **Element Finding**: Smart selection and multiple strategies
* **Interaction**: Clicking, typing, form operations
* **State Checking**: Visibility, enabled status, values
* **Waiting**: Smart waits for various conditions
* **Advanced Operations**: Drag-drop, screenshots, JavaScript execution
* **Error Handling**: Robust patterns for reliable automation

**Next Step**: Learn :doc:`fill-strategies` to master comprehensive form automation patterns.
