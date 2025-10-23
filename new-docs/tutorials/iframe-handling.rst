================
IFrame Handling
================

This tutorial demonstrates how to work with iframes in Widgetastic.core using the framework's test pages.
You'll learn to navigate iframe hierarchies, switch contexts, and handle nested frame structures using ``iframe_page.html`` and ``iframe_page2.html``.

.. note::
   **Prerequisites**: Basic widgets tutorial
   **Test Pages Used**: ``testing/html/testing_page.html``, ``iframe_page.html``, ``iframe_page2.html``

Learning Objectives
===================

* ✅ Understand iframe context switching
* ✅ Navigate nested iframe hierarchies
* ✅ Handle iframe isolation and cross-context access

Understanding IFrames in Web Automation
=======================================

IFrames (inline frames) embed another HTML document within the current page.
They create isolated contexts that require special handling in web automation:

* **Context Isolation**: Elements inside iframes aren't accessible from the main page context
* **Frame Switching**: You must explicitly switch context to interact with iframe content
* **Nested Frames**: IFrames can contain other iframes, creating complex hierarchies
* **Security Boundaries**: Cross-origin iframes may have additional restrictions


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
