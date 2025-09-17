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

.. code-block:: python

    # my_first_widgetastic.py
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput, Button, Select

    # Step 1: Define your widgets and views
    class DemoFormView(View):
        # Define the form elements as widgets
        first_name = TextInput(name="first_name")
        last_name = TextInput(name="last_name")
        email = TextInput(name="email")
        country = Select(name="country")
        message = TextInput(name="message")
        submit_button = Button("//button[@type='submit']")

        # Results section
        result_message = Text("#result")

    # Step 2: Create a custom browser class
    class MyBrowser(Browser):
        @property
        def product_version(self):
            return "1.0.0"  # Required for version picking features

    # Step 3: Main automation logic
    def main():
        with sync_playwright() as playwright:
            # Launch browser
            browser = playwright.chromium.launch(headless=False)  # headless=False to see it in action
            page = browser.new_page()

            # Navigate to test page
            page.goto("https://httpbin.org/forms/post")  # Public test form

            # Create widgetastic browser wrapper
            wt_browser = MyBrowser(page)

            # Initialize the view
            form = DemoFormView(wt_browser)

            # Step 4: Interact with the form
            print("📝 Filling out the form...")

            # Fill form using dictionary (bulk fill)
            form_data = {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "message": "Hello from Widgetastic!"
            }

            changed = form.fill(form_data)
            print(f"Form filling changed values: {changed}")

            # Fill individual fields
            if form.country.is_displayed:
                form.country.fill("United States")

            # Step 5: Read form values to verify
            print("\n📖 Reading current form values:")
            current_values = form.read()
            for field, value in current_values.items():
                if value:  # Only show filled fields
                    print(f"  {field}: {value}")

            # Step 6: Submit the form
            print("\n🚀 Submitting form...")
            form.submit_button.click()

            # Step 7: Handle results
            # Wait a moment for response
            page.wait_for_timeout(2000)  # 2 seconds

            print("✅ Script completed successfully!")

            # Clean up
            browser.close()

    if __name__ == "__main__":
        main()

**Running the Script**

Save the code as ``my_first_widgetastic.py`` and run it:

.. code-block:: bash

    python my_first_widgetastic.py

You should see the browser open, the form get filled out automatically, and output showing the progress.

Breaking Down the Example
=========================

Let's examine each part of the script in detail:

**1. Import Statements**

.. code-block:: python

    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput, Button, Select

* ``sync_playwright`` - Playwright's synchronous API
* ``Browser`` - Widgetastic's enhanced browser wrapper
* Widget classes - Individual UI component types

**2. View Definition**

.. code-block:: python

    class DemoFormView(View):
        first_name = TextInput(name="first_name")
        last_name = TextInput(name="last_name")
        # ... more widgets

This creates a view that groups related form elements. Each widget is defined with its locator:
* ``TextInput(name="first_name")`` finds ``<input name="first_name">``
* ``Button("//button[@type='submit']")`` uses XPath to find the submit button

**3. Custom Browser Class**

.. code-block:: python

    class MyBrowser(Browser):
        @property
        def product_version(self):
            return "1.0.0"

The ``product_version`` property is required for advanced features like version picking.
Even if you don't use them immediately, it's good practice to define this.

**4. Browser Setup**

.. code-block:: python

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        wt_browser = MyBrowser(page)

This creates the browser hierarchy:
* Playwright browser → Playwright page → Widgetastic browser

**5. Form Interaction**

.. code-block:: python

    # Bulk fill using dictionary
    form.fill(form_data)

    # Individual field access
    form.country.fill("United States")

    # Read current values
    current_values = form.read()

Demonstrates both bulk operations and individual field access.

Common Patterns
===============

**Pattern 1: Page Object Model**

Organize your views by page or functional area:

.. code-block:: python

    class LoginPage(View):
        username = TextInput("#username")
        password = TextInput("#password")
        login_button = Button("#login")

    class DashboardPage(View):
        welcome_message = Text(".welcome")
        logout_button = Button("#logout")

**Pattern 2: Nested Views**

Group related sections within larger pages:

.. code-block:: python

    class UserProfilePage(View):
        class personal_info(View):
            ROOT = "#personal-section"
            first_name = TextInput("#first_name")
            last_name = TextInput("#last_name")

        class preferences(View):
            ROOT = "#preferences-section"
            theme = Select("#theme")
            language = Select("#language")

**Pattern 3: Reusable Components**

Create widgets for common UI patterns:

.. code-block:: python

    class Modal(View):
        ROOT = ".modal"
        title = Text(".modal-title")
        close_button = Button(".modal-close")
        ok_button = Button(".btn-ok")
        cancel_button = Button(".btn-cancel")

    class MainPage(View):
        delete_modal = Modal()
        settings_modal = Modal()

Adding Error Handling
======================

Make your scripts more robust with proper error handling:

.. code-block:: python

    from widgetastic.exceptions import NoSuchElementException, WidgetOperationFailed

    def safe_fill_form(form, data):
        try:
            changed = form.fill(data)
            print(f"✅ Form filled successfully. Changed: {changed}")
            return True
        except NoSuchElementException as e:
            print(f"❌ Element not found: {e}")
            return False
        except WidgetOperationFailed as e:
            print(f"❌ Operation failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    # Usage
    success = safe_fill_form(form, form_data)
    if success:
        form.submit_button.click()

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

    2024-01-15 10:30:12 - my_automation - INFO - [DemoFormView/first_name]: Filled 'John' with result True
    2024-01-15 10:30:12 - my_automation - INFO - [DemoFormView/submit_button]: Click started

Working with Different Browsers
================================

Test across different browsers easily:

.. code-block:: python

    def run_test(browser_type="chromium"):
        with sync_playwright() as p:
            # Launch different browsers
            if browser_type == "firefox":
                browser = p.firefox.launch(headless=False)
            elif browser_type == "webkit":
                browser = p.webkit.launch(headless=False)
            else:
                browser = p.chromium.launch(headless=False)

            page = browser.new_page()
            # ... rest of your test

    # Run on all browsers
    for browser in ["chromium", "firefox", "webkit"]:
        print(f"\n🌐 Testing with {browser}...")
        run_test(browser)

Next Steps
==========

Congratulations! You've successfully created your first widgetastic automation script. Here's what to explore next:

**Immediate Next Steps**

1. :doc:`../quickstart/index` - More practical examples and common patterns
2. :doc:`../tutorials/basic-widgets` - Deep dive into different widget types
3. :doc:`../tutorials/views-and-navigation` - Advanced view patterns

**As You Progress**

4. :doc:`../tutorials/basic-widgets` - Comprehensive widget examples
5. :doc:`concepts` - Master core concepts and locator strategies
6. :doc:`../tutorials/custom-widgets` - Build your own widgets

**Common Questions**

* **"My elements aren't found"** → Check locator strategies in :doc:`concepts`
* **"How do I handle dynamic content?"** → See :doc:`../tutorials/advanced-widgets`
* **"Can I use this with pytest?"** → Absolutely! See the examples in our tutorials

Troubleshooting Tips
====================

**Script doesn't work?**

1. **Check element locators**: Use browser dev tools to verify element selectors
2. **Add delays**: Some pages need time to load: ``page.wait_for_timeout(1000)``
3. **Enable headful mode**: Set ``headless=False`` to see what's happening
4. **Check logs**: Add logging to see detailed operation information

**Elements not found?**

1. **Verify locators**: Test selectors in browser console: ``document.querySelector("#my-id")``
2. **Wait for elements**: Use ``form.submit_button.wait_displayed()``
3. **Check frames**: Some elements might be in iframes

**Form filling not working?**

1. **Check element types**: Ensure you're using the right widget type
2. **Verify values**: Some fields have value restrictions
3. **Check visibility**: Elements must be visible and enabled

Remember: Start simple, test often, and build complexity gradually!
