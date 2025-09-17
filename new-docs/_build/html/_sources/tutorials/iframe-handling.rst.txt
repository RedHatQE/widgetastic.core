========================
IFrame Handling Tutorial
========================

This tutorial demonstrates how to work with iframes in Widgetastic.core using the framework's test pages. You'll learn to navigate iframe hierarchies, switch contexts, and handle nested frame structures using ``iframe_page.html`` and ``iframe_page2.html``.

.. note::
   **Time Required**: 30 minutes
   **Prerequisites**: Basic widgets tutorial
   **Test Pages Used**: ``testing/html/testing_page.html``, ``iframe_page.html``, ``iframe_page2.html``

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Understand iframe context switching
* ✅ Navigate nested iframe hierarchies
* ✅ Handle iframe isolation and cross-context access
* ✅ Implement robust iframe automation patterns
* ✅ Debug iframe-related issues

Understanding IFrames in Web Automation
=======================================

IFrames (inline frames) embed another HTML document within the current page. They create isolated contexts that require special handling in web automation:

* **Context Isolation**: Elements inside iframes aren't accessible from the main page context
* **Frame Switching**: You must explicitly switch context to interact with iframe content
* **Nested Frames**: IFrames can contain other iframes, creating complex hierarchies
* **Security Boundaries**: Cross-origin iframes may have additional restrictions

Setting Up Iframe Testing Environment
====================================

.. code-block:: python

    from pathlib import Path
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, Select, TextInput

    def setup_iframe_browser():
        """Setup browser with iframe testing pages."""
        # Main testing page with embedded iframe
        main_page_path = Path("testing/html/testing_page.html").resolve()
        main_page_url = main_page_path.as_uri()

        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()
        browser = Browser(page)

        # Navigate to main testing page (contains iframe)
        browser.goto(main_page_url)

        return browser, p, browser_instance, context

    browser, playwright, browser_instance, context = setup_iframe_browser()

Basic IFrame Access
===================

The testing page contains an iframe that loads ``iframe_page.html``. Here's how to access it:

**Simple IFrame View**

.. code-block:: python

    class BasicIFrameView(View):
        # The FRAME attribute specifies the iframe locator
        FRAME = '//iframe[@name="some_iframe"]'

        # Widgets inside the iframe
        iframe_title = Text(".//h3")
        select1 = Select(id="iframe_select1")
        select2 = Select(name="iframe_select2")

    iframe_view = BasicIFrameView(browser)

    # Test basic iframe access
    print(f"IFrame displayed: {iframe_view.is_displayed}")
    print(f"IFrame title: {iframe_view.iframe_title.read()}")
    # Output: "IFrame Widget Testing"

    # Interact with iframe widgets
    current_selection = iframe_view.select1.read()
    print(f"Current selection: {current_selection}")  # "Foo"

    # Change selection
    iframe_view.select1.fill("Bar")
    print(f"New selection: {iframe_view.select1.read()}")  # "Bar"

**Multiple Select in IFrame**

.. code-block:: python

    # Working with multi-select in iframe
    print(f"Multi-select options: {iframe_view.select2.all_options}")
    # Output: [('Foo', 'foo'), (' Bar', 'bar'), ('Baz', 'baz')]

    # Select multiple options
    iframe_view.select2.fill(["Foo", "Baz"])
    selected = iframe_view.select2.read()
    print(f"Multi-selected: {selected}")

Nested IFrame Navigation
========================

The iframe testing setup includes nested iframes. Here's how to handle complex hierarchies:

**Nested IFrame Structure**

.. code-block:: python

    class NestedIFrameView(View):
        # First level iframe
        FRAME = '//iframe[@name="some_iframe"]'
        iframe_title = Text(".//h3")

        # Nested iframe class (iframe within iframe)
        class nested_iframe(View):
            FRAME = './/iframe[@name="another_iframe"]'
            nested_title = Text(".//h3")
            nested_select = Select(id="iframe_select3")

            # Deeply nested view within the nested iframe
            class deep_nested(View):
                ROOT = './/div[@id="nested_view"]'
                nested_input = TextInput(name="input222")

    nested_view = NestedIFrameView(browser)

    # Access each level of nesting
    print(f"Level 1 iframe: {nested_view.iframe_title.read()}")
    # Output: "IFrame Widget Testing"

    print(f"Level 2 iframe: {nested_view.nested_iframe.nested_title.read()}")
    # Output: "Nested IFrame Content"

    print(f"Nested select: {nested_view.nested_iframe.nested_select.read()}")
    # Output: "Foo"

    # Access deeply nested input
    nested_input_value = nested_view.nested_iframe.deep_nested.nested_input.read()
    print(f"Deep nested input: {nested_input_value}")
    # Output: "Default Value"

    # Fill deeply nested input
    nested_view.nested_iframe.deep_nested.nested_input.fill("Updated Value")
    updated_value = nested_view.nested_iframe.deep_nested.nested_input.read()
    print(f"Updated nested input: {updated_value}")

IFrame Context Isolation
========================

IFrame contexts are completely isolated. Elements in different frames cannot directly interact:

**Demonstrating Context Isolation**

.. code-block:: python

    class MainPageView(View):
        # Elements in main page context
        main_title = Text('h1#wt-core-title')
        main_checkbox = Checkbox(id="switchabletesting-3")

    class IFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        iframe_title = Text(".//h3")
        iframe_select = Select(id="iframe_select1")

    main_view = MainPageView(browser)
    iframe_view = IFrameView(browser)

    # Both contexts work independently
    print(f"Main page title: {main_view.main_title.read()}")
    # Output: "Widgetastic.Core - Testing Page"

    print(f"IFrame title: {iframe_view.iframe_title.read()}")
    # Output: "IFrame Widget Testing"

    # Interactions don't affect each other
    main_view.main_checkbox.fill(True)
    iframe_view.iframe_select.fill("Bar")

    # Verify isolation - both maintain their states
    assert main_view.main_checkbox.read() is True
    assert iframe_view.iframe_select.read() == "Bar"
    print("✓ Context isolation verified")

Multiple IFrame Switching
=========================

Efficiently switch between multiple iframe contexts:

**Cross-Context Operations**

.. code-block:: python

    class MultiContextView(View):
        # Main frame elements
        main_checkbox1 = Checkbox(id="switchabletesting-3")
        main_checkbox2 = Checkbox(id="switchabletesting-4")

    class IFrameContextView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        select1 = Select(id="iframe_select1")
        select2 = Select(name="iframe_select2")

    main_view = MultiContextView(browser)
    iframe_view = IFrameContextView(browser)

    # Perform multiple cross-context operations
    for i in range(3):
        # Access iframe context
        iframe_value = "Bar" if i % 2 == 0 else "Foo"
        iframe_view.select1.fill(iframe_value)

        # Access main frame context
        main_view.main_checkbox1.fill(i % 2 == 0)

        # Verify states maintained correctly
        assert iframe_view.select1.read() == iframe_value
        assert main_view.main_checkbox1.read() == (i % 2 == 0)

    print("✓ Multiple context switching successful")

IFrame Error Handling
=====================

Handle common iframe-related errors gracefully:

**Error Handling Patterns**

.. code-block:: python

    from widgetastic.exceptions import FrameNotFoundError, NoSuchElementException

    class ErrorHandlingIFrameView(View):
        # Invalid iframe reference
        FRAME = '//iframe[@name="nonexistent_iframe"]'
        some_element = Text(".//h3")

    class ValidIFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        nonexistent_element = Text(".//nonexistent")
        valid_element = Text(".//h3")

    # Test 1: Invalid iframe reference
    invalid_view = ErrorHandlingIFrameView(browser)
    try:
        _ = invalid_view.some_element.is_displayed
        print("ERROR: Should have raised FrameNotFoundError")
    except FrameNotFoundError as e:
        print(f"✓ Correctly caught frame error: {e}")

    # Test 2: Valid iframe, nonexistent element
    valid_view = ValidIFrameView(browser)
    print(f"Valid element exists: {valid_view.valid_element.is_displayed}")  # True
    print(f"Invalid element exists: {valid_view.nonexistent_element.is_displayed}")  # False

    # Test 3: Robust error handling
    def safe_iframe_interaction(view, widget_name, fill_value=None):
        """Safely interact with iframe widgets."""
        try:
            widget = getattr(view, widget_name)
            if not widget.is_displayed:
                print(f"Widget {widget_name} not displayed")
                return False

            if fill_value is not None:
                widget.fill(fill_value)
                print(f"✓ Successfully filled {widget_name}")
            else:
                value = widget.read()
                print(f"✓ Successfully read {widget_name}: {value}")
            return True

        except (FrameNotFoundError, NoSuchElementException) as e:
            print(f"Error accessing {widget_name}: {e}")
            return False

    # Use safe interaction
    iframe_view = ValidIFrameView(browser)
    safe_iframe_interaction(iframe_view, 'valid_element')
    safe_iframe_interaction(iframe_view, 'nonexistent_element')

Complex IFrame Scenarios
========================

Handle real-world complex iframe scenarios:

**Dynamic IFrame Loading**

.. code-block:: python

    class DynamicIFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'

        # Wait for iframe content to load
        def wait_for_iframe_ready(self, timeout=10):
            """Wait for iframe content to be ready."""
            return self.browser.wait_for_element(
                ".//h3", parent=self, timeout=timeout
            ).is_displayed

    dynamic_view = DynamicIFrameView(browser)

    # Wait for iframe to be ready before interaction
    if hasattr(dynamic_view, 'wait_for_iframe_ready'):
        if dynamic_view.wait_for_iframe_ready():
            print("✓ IFrame content loaded successfully")
        else:
            print("⚠ IFrame content failed to load")

**IFrame with Form Automation**

.. code-block:: python

    class IFrameFormView(View):
        FRAME = '//iframe[@name="some_iframe"]'

        # Form elements in iframe
        select1 = Select(id="iframe_select1")
        select2 = Select(name="iframe_select2")

        def fill_iframe_form(self, select1_value, select2_values):
            """Fill entire iframe form."""
            results = {}

            # Fill first select
            if self.select1.fill(select1_value):
                results['select1'] = self.select1.read()

            # Fill multi-select
            if self.select2.fill(select2_values):
                results['select2'] = self.select2.read()

            return results

        def read_iframe_form(self):
            """Read all iframe form data."""
            return {
                'select1': self.select1.read(),
                'select2': self.select2.read()
            }

    form_view = IFrameFormView(browser)

    # Fill iframe form
    results = form_view.fill_iframe_form("Bar", ["Foo", "Baz"])
    print(f"Fill results: {results}")

    # Read back form data
    form_data = form_view.read_iframe_form()
    print(f"Form data: {form_data}")

Best Practices for IFrame Handling
==================================

**IFrame Development Patterns**

.. code-block:: python

    # 1. Always specify FRAME at the View level
    class GoodIFrameView(View):
        FRAME = '//iframe[@name="target_iframe"]'  # ✓ Correct
        content = Text(".//div[@class='content']")

    # 2. Use descriptive iframe locators
    class DescriptiveIFrameView(View):
        FRAME = '//iframe[@title="User Management"]'  # ✓ Clear intent
        user_list = Text(".//ul[@class='users']")

    # 3. Handle nested iframes with clear structure
    class WellStructuredNestedView(View):
        FRAME = '//iframe[@name="outer_frame"]'

        class inner_content(View):
            FRAME = './/iframe[@name="inner_frame"]'  # ✓ Relative to parent
            data = Text(".//div[@class='data']")

    # 4. Implement iframe readiness checks
    def ensure_iframe_ready(iframe_view, timeout=5):
        """Ensure iframe is ready for interaction."""
        try:
            return iframe_view.browser.wait_for_element(
                iframe_view.FRAME, timeout=timeout
            ).is_displayed
        except:
            return False

**Performance Optimization**

.. code-block:: python

    # Group iframe operations to minimize context switching
    class OptimizedIFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        select1 = Select(id="iframe_select1")
        select2 = Select(name="iframe_select2")

        def batch_fill_operations(self, data_dict):
            """Perform multiple operations in single iframe context."""
            results = {}
            for widget_name, value in data_dict.items():
                widget = getattr(self, widget_name)
                if widget.fill(value):
                    results[widget_name] = widget.read()
            return results

    # Use batch operations
    iframe_view = OptimizedIFrameView(browser)
    batch_results = iframe_view.batch_fill_operations({
        'select1': 'Bar',
        'select2': ['Foo', 'Baz']
    })
    print(f"Batch results: {batch_results}")

Troubleshooting IFrame Issues
=============================

**Common Issues and Solutions**

.. code-block:: python

    # Issue 1: Frame not found
    def debug_iframe_locator(browser, frame_locator):
        """Debug iframe locator issues."""
        frames = browser.elements(frame_locator)
        print(f"Found {len(frames)} frames matching '{frame_locator}'")

        for i, frame in enumerate(frames):
            name = browser.get_attribute(frame, 'name')
            src = browser.get_attribute(frame, 'src')
            print(f"Frame {i}: name='{name}', src='{src}'")

    # Issue 2: Timing problems
    def wait_for_iframe_content(iframe_view, content_locator, timeout=10):
        """Wait for specific content in iframe."""
        try:
            return iframe_view.browser.wait_for_element(
                content_locator, parent=iframe_view, timeout=timeout
            )
        except:
            print(f"Timeout waiting for iframe content: {content_locator}")
            return None

    # Issue 3: Context verification
    def verify_iframe_context(view):
        """Verify you're in the correct iframe context."""
        try:
            # Try to access iframe-specific content
            test_element = view.browser.element(".//h3")
            content = view.browser.text(test_element)
            print(f"Current iframe context contains: {content}")
            return True
        except:
            print("Not in expected iframe context")
            return False

    # Usage examples
    debug_iframe_locator(browser, '//iframe[@name="some_iframe"]')

    iframe_view = BasicIFrameView(browser)
    verify_iframe_context(iframe_view)

Summary
=======

IFrame handling in Widgetastic.core provides:

* **Automatic Context Switching**: Views with FRAME automatically switch contexts
* **Nested Frame Support**: Handle complex iframe hierarchies easily
* **Context Isolation**: Each frame maintains independent state
* **Error Handling**: Robust error handling for missing frames/elements
* **Performance**: Efficient frame switching and batched operations

Key takeaways:
* Always use ``FRAME`` attribute in Views for iframe widgets
* Handle frame-specific errors with appropriate exception handling
* Batch iframe operations for better performance
* Test iframe readiness before interaction
* Use descriptive locators for maintainable code

This completes the iframe handling tutorial. You're now ready to handle any iframe scenario in your web automation projects.
