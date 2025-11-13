===========
First Steps
===========

Ready to write your first widgetastic automation script? This guide walks you through creating a complete,
working example that demonstrates the core concepts in action.

Your First Script
=================

Let's create a script that automates a simple web form. We'll use a public testing website to ensure
the example works reliably.

**Complete Example**

.. literalinclude:: ../examples/getting-started/first_script.py
   :language: python
   :linenos:

.. note::

   Core widgetastic provides minimal widgets (Text, TextInput, Checkbox, etc.). For specialized widgets like Buttons, Modals, Charts, use extensions like `widgetastic-patternfly5 <https://github.com/RedHatQE/widgetastic.patternfly5>`_.

**Running the Script**

Save the code as ``first_script.py`` and run it:

.. code-block:: bash

    python first_script.py

You should see the browser open, the form get filled out automatically, and output showing the progress.

Breaking Down the Example
=========================

Let's examine each part of the script in detail:

**1. Import Statements**

.. code-block:: python

    import json
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput, Checkbox

* ``json`` - For parsing the response data after form submission
* ``sync_playwright`` - Playwright's synchronous API for browser automation
* ``Browser`` - Widgetastic's enhanced browser wrapper
* Widget classes - Individual UI component types (Text, TextInput, Checkbox)

**2. View Definition with Nested Views**

.. code-block:: python

    class DemoFormView(View):
        # Basic form fields
        custname = TextInput(locator='.//input[@name="custname"]')
        telephone = TextInput(locator='.//input[@name="custtel"]')
        email = TextInput(locator='.//input[@name="custemail"]')

        # Nested view for pizza size options
        @View.nested
        class pizza_size(View):
            small = Checkbox(locator=".//input[@value='small']")
            medium = Checkbox(locator=".//input[@value='medium']")
            large = Checkbox(locator=".//input[@value='large']")

        # Nested view for pizza toppings
        @View.nested
        class pizza_toppings(View):
            bacon = Checkbox(locator=".//input[@value='bacon']")
            extra_cheese = Checkbox(locator=".//input[@value='cheese']")
            # ... more toppings

This creates a hierarchical view structure:
* **Basic fields** use XPath locators to find form inputs.
* **Nested views** group related elements (pizza size, toppings) using ``@View.nested``
* **Checkbox widgets** handle radio buttons and checkboxes for selections

**3. Browser Setup and Navigation**

.. code-block:: python

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        wt_browser = Browser(page)
        wt_browser.url = "https://httpbin.org/forms/post"

This creates the browser hierarchy and navigates to the test form:
* Playwright browser → Playwright page → Widgetastic browser
* Uses httpbin.org for reliable testing (no custom setup required)

**4. Form Interaction and Data Handling**

.. code-block:: python

    # Initialize the view
    form_view = DemoFormView(wt_browser)

    # Fill individual fields
    form_view.custname.fill("John Doe")
    form_view.telephone.fill("1234567890")
    form_view.email.fill("john.doe@example.com")

    # Select pizza options using nested views
    form_view.pizza_size.small.fill(True)
    form_view.pizza_toppings.bacon.fill(True)

    form_view.delivery_instructions.fill("Hello from Widgetastic!")

    # Submit and handle response
    form_view.submit_order.click()
    response_data = json.loads(form_view.response.text)


**We can fill the form in a single shot. Widgetastic will fill the form in the order of the widgets.**

.. literalinclude:: ../examples/getting-started/batch_fill_example.py
   :language: python
   :linenos:



Adding Logging
==============

Enable logging to see what widgetastic is doing:

.. code-block:: python

    import logging

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create browser with logger
    logger = logging.getLogger("my_automation")
    wt_browser = MyBrowser(page, logger=logger)

This will show detailed logs of widget operations:

.. code-block:: text

    2025-10-23 16:31:24,598 - my_automation - INFO - Opening URL: 'https://httpbin.org/forms/post' (wait_until=None)
    2025-10-23 16:31:39,549 - my_automation - INFO - [DemoFormView/custname]: fill('John Doe') -> True (elapsed 624 ms)
    2025-10-23 16:31:39,662 - my_automation - INFO - [DemoFormView/telephone]: fill('1234567890') -> True (elapsed 113 ms)
