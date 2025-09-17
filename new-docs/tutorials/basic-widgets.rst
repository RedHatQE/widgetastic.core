=====================
Basic Widgets Tutorial
=====================

This comprehensive tutorial demonstrates all the fundamental widgets in Widgetastic.core using the framework's real testing pages.
You'll learn to interact with web elements through practical examples using ``testing/html/testing_page.html`` - the same file used to test the framework itself.

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Basic understanding of five core widget types (Text, TextInput, Checkbox, Select, Image)
* ✅ Understand the widget read/fill interface
* ✅ Handle widget state and validation
* ✅ Work with real-world HTML structures
* ✅ Implement effective automation patterns

Setting Up Your Environment
===========================

**Browser Setup Using Testing Page**

.. code-block:: python

    from pathlib import Path
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput, Checkbox, Select, Image

    def setup_browser():
        """Setup browser with widgetastic testing page."""
        # Get the widgetastic testing page path
        test_page_path = Path("testing/html/testing_page.html").resolve()
        test_page_url = test_page_path.as_uri()

        # Initialize Playwright
        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()
        browser = Browser(page)

        # Navigate to testing page
        browser.goto(test_page_url)

        return browser, p, browser_instance, context

    # Usage
    browser, playwright, browser_instance, context = setup_browser()

Understanding the Testing Page Structure
=======================================

The ``testing_page.html`` contains comprehensive examples:

* **Header Section**: Main title and subtitle elements
* **Visibility Testing**: Hidden/visible elements with dynamic content
* **Form Elements**: Text inputs, checkboxes, file inputs, color pickers
* **Selection Widgets**: Single and multi-select dropdowns
* **Interactive Buttons**: Click handlers, state changes
* **Tables**: Standard and complex table structures with embedded widgets
* **Images**: Elements with src, alt, and title attributes
* **Advanced Features**: Drag & drop, OUIA components, alerts, iframes

Text Widget - Reading Content from Pages
========================================

The :py:class:`~widgetastic.widget.Text` widget extracts text content from any web element.

**Basic Text Widget Examples**

.. code-block:: python

    class TestingPageView(View):
        # Read the main page title
        main_title = Text(locator= ".//h1[@id='wt-core-title']")

        # Read the sub title
        sub_title = Text(locator='.//p[@class="subtitle"]')

        # Read section headers; `.section-header` is a CSS selector matches all elements with class `section-header`
        # But it will select first element with class `section-header`
        section_header = Text(locator='.section-header')

        # Define non existing element
        non_existing_element = Text(locator='.//div[@id="non-existing-element"]')


    page = TestingPageView(browser)

    # Check if element exist on page or not
    page.main_title.is_displayed        # True
    page.non_existing_element.is_displayed        # False

    # Reading text content
    print(f"Page title: {page.main_title.read()}")
    # Output: "Widgetastic.Core - Testing Page"

    print(f"Sub title: {page.sub_title.read()}")
    # Output: "Interactive demonstrations for widget automation and testing"

    # In state of read method you can use text property to get the text content
    print(f"First Section header: {page.section_header.text}")
    # Output: "Element Visibility & State Testing"


**Advanced Text Widget Patterns**

.. code-block:: python

    class AdvancedTextExamples(View):
        # Table header content
        table_header = Text(locator="//table[@id='with-thead']//th[2]")

        # Visible content in mixed visibility container
        visible_content = Text(locator="#visible_invisible .visible")

        # Content from OUIA section
        ouia_title = Text(locator="//div[@data-ouia-component-id='ouia']//h3")

    advanced = AdvancedTextExamples(browser)

    # Reading from different contexts
    print(f"Table header: {advanced.table_header.read()}")  # "Column 1"
    print(f"Visible text: {advanced.visible_content.read()}")  # "Visible content"
    print(f"OUIA title: {advanced.ouia_title.read()}")  # "OUIA Widget Examples"

TextInput Widget - Form Field Automation
========================================

The :py:class:`~widgetastic.widget.TextInput` widget handles all text input elements.

**TextInput Initialization Arguments**

The TextInput widget accepts exactly **one** of these three arguments (they are mutually exclusive):

* **id**: Look up input by its id attribute
* **name**: Look up input by its name attribute
* **locator**: Use a custom locator (supports SmartLocator)

.. warning::
   You can only specify **one** argument when initializing TextInput. Using multiple arguments
   (e.g., both ``id`` and ``name``) will raise a ``TypeError``.


.. code-block:: python

    class InputVariations(View):
        # Demonstrating different TextInput initialization methods
        # Note: In real code, you'd typically use id when available for consistency
        text_input = TextInput(id="input")  # Standard text input - by id
        paste_input = TextInput(locator="#input_paste")  # Paste target - by CSS locator
        number_input = TextInput(name="input_number")  # Number input - by name
        textarea_input = TextInput(locator="//textarea[@id='textarea_input']")  # Textarea - by XPath

    view = InputVariations(browser)

    # Reading current values using different initialization methods
    current_value = view.text_input.read()
    paste_value = view.paste_input.read()
    number_value = view.number_input.read()
    textarea_value = view.textarea_input.read()

    # Filling inputs initialized with different arguments
    view.text_input.fill("test_user")
    view.paste_input.fill("pasted_content")
    view.number_input.fill("42")
    view.textarea_input.fill("Multi-line text content")

    # All input types work the same regardless of initialization method
    print(f"Text input: '{view.text_input.read()}'")  # "test_user"
    print(f"Paste input: '{view.paste_input.read()}'")  # "pasted_content"
    print(f"Number input: '{view.number_input.read()}'")  # "42"
    print(f"Textarea: '{view.textarea_input.read()}'")  # "Multi-line text content"



**TextInput State Management**

.. code-block:: python

    class InputStateManagement(View):
        enabled_input = TextInput(id="input1")
        disabled_input = TextInput(name="input1_disabled")
        non_existing_input = TextInput(id="non_existing_input")
        textarea_input = TextInput(id="textarea_input")

    # Using the InputVariations view for state management examples
    view = InputStateManagement(browser)

    # Check if input is displayed or not
    print(f"Enabled input is displayed: {view.enabled_input.is_displayed}") # True
    print(f"Non existing input is displayed: {view.non_existing_input.is_displayed}") # False

    # Check if input is enabled or disabled
    print(f"Enabled input is enabled: {view.enabled_input.is_enabled}") # True
    print(f"Disabled input is enabled: {view.disabled_input.is_enabled}") # False

    # Check if fill was successful (returns True if value changed)
    changed = view.enabled_input.fill("new_value")
    print(f"Value changed: {changed}")  # True if different from previous

    no_change = view.enabled_input.fill("new_value")  # Same value
    print(f"Value changed: {no_change}")   # False, no change needed


    # Multi-line content in textarea
    textarea_content = "Line 1\nLine 2\nNew content"
    view.textarea_input.fill(textarea_content)
    view.textarea_input.read()



Checkbox Widget - Boolean State Management
==========================================

The :py:class:`~widgetastic.widget.Checkbox` widget handles checkbox elements.

**Checkbox Examples from Testing Page**

.. code-block:: python

    class CheckboxView(View):
        # Main form checkboxes
        enabled_checkbox = Checkbox(id="input2")
        disabled_checkbox = Checkbox(id="input2_disabled")

    checkboxes = CheckboxView(browser)

    # Check is_displayed and is_enabled
    print(f"Enabled checkbox is displayed: {checkboxes.enabled_checkbox.is_displayed}") # True
    print(f"Disabled checkbox is displayed: {checkboxes.disabled_checkbox.is_displayed}") # True

    print(f"Enabled checkbox is enabled: {checkboxes.enabled_checkbox.is_enabled}") # True
    print(f"Disabled checkbox is enabled: {checkboxes.disabled_checkbox.is_enabled}") # False

    # Filling  and reading checkboxes
    checkboxes.enabled_checkbox.fill(True)   # Check
    checkboxes.enabled_checkbox.read() # True
    checkboxes.enabled_checkbox.fill(False)        # Uncheck
    checkboxes.enabled_checkbox.read() # False


Select Widget - Dropdown Management
===================================

The :py:class:`~widgetastic.widget.Select` widget handles HTML select elements.

**Select Examples from Testing Page**

.. code-block:: python

    class SelectView(View):
        # Single selection dropdowns
        single_select = Select(name="testselect1")

        # Multiple selection dropdown
        multi_select = Select(name="testselect2")

        # Select with no initial selection
        no_selection = Select(name="testselect3")

    selects = SelectView(browser)

    # Reading selected values
    current = selects.single_select.read()
    print(f"Current selection: {current}")  # "Foo"

    # Get all available options
    options = selects.single_select.all_options
    print(f"Available options: {options}")  # [Option(text='Foo', value='foo'), Option(text='Bar', value='bar')]

    # Select by visible text
    selects.single_select.fill("Bar")

    # Select by value
    selects.single_select.fill(("by_value", "foo"))

    # Multiple selection
    selects.multi_select.fill(["Foo", "Baz"])
    selected_multiple = selects.multi_select.read() # ["Foo", "Baz"]
    print(f"Multi-selected: {selected_multiple}")

Image Widget - Image Attribute Access
=====================================

The :py:class:`~widgetastic.widget.Image` widget provides access to HTML image elements.

**Image Examples from Testing Page**

.. code-block:: python

    class ImageView(View):
        # Images with different attributes
        full_image = Image('.//img[@id="test-image-full"]')      # Has src, alt, title
        src_only_image = Image('.//img[@id="test-image-src-only"]')  # Only src
        alt_image = Image('.//img[@id="test-image-alt"]')        # Has src and alt

    images = ImageView(browser)

    # Accessing image attributes
    print(f"Full image src: {images.full_image.src}")
    print(f"Full image alt: {images.full_image.alt}")    # "Green test image"
    print(f"Full image title: {images.full_image.title}") # "Image title"

    # Check image visibility
    if images.full_image.is_displayed:
        print("Image is visible on page")
