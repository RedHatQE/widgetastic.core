==========
Quick Start
==========

Ready to jump right into widgetastic.core? This section provides immediate, practical examples that you
can run and modify. Perfect for developers who learn by doing!

.. note::
   Make sure you've completed the :doc:`../getting-started/installation` before running these examples.

What You'll Learn
=================

Through hands-on examples, you'll quickly understand:

* 🎯 **Widget Creation** - How to model UI elements as widgets
* 🏗️ **View Organization** - Structuring your automation code
* 🔄 **Read/Fill Patterns** - Getting and setting values efficiently
* 🎭 **Element Interaction** - Clicking, typing, and form handling
* 📊 **Data Extraction** - Reading information from complex UIs
* 🚀 **Testing Integration** - Using widgetastic with testing frameworks

5-Minute Start
==============

**Want to see widgetastic in action immediately?** Run this complete example:

.. code-block:: python

    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, TextInput, Button, Text

    class SearchView(View):
        search_box = TextInput("[name='q']")
        search_button = Button("[type='submit']")
        results = Text("#search")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://httpbin.org")

        view = SearchView(Browser(page))
        print("🎉 Widgetastic is working!")
        browser.close()

Examples by Use Case
====================

Choose the example that matches your needs:

.. grid:: 2

   .. grid-item-card:: 📝 Form Automation
      :link: basic-example
      :link-type: doc

      Complete form filling, validation, and submission examples.
      Perfect for login flows, contact forms, and data entry.

   .. grid-item-card:: 📋 Data Extraction
      :link: common-patterns
      :link-type: doc

      Reading data from tables, lists, and complex layouts.
      Great for reports, dashboards, and data validation.

   .. grid-item-card:: 🔄 Dynamic Content
      :link: ../tutorials/advanced-widgets
      :link-type: doc

      Handling loading states, AJAX content, and real-time updates.
      Essential for modern SPAs and dynamic applications.

   .. grid-item-card:: 🧪 Testing Integration
      :link: ../tutorials/basic-widgets
      :link-type: doc

      Using widgetastic with pytest, unittest, and testing frameworks.
      Industry best practices for test automation.

Quick Reference
===============

**Most Common Widgets**

.. code-block:: python

    # Text elements
    title = Text("#page-title")
    paragraph = Text(".content p")

    # Form inputs
    username = TextInput("#username")
    password = TextInput({"type": "password"})

    # Buttons and clicks
    submit = Button("//button[text()='Submit']")
    link = Button("a[href='/logout']")  # Links work too!

    # Selections
    country = Select("#country")
    checkbox = Checkbox("#agree-terms")

    # Complex widgets
    user_table = Table("#users-table")

**Most Common Patterns**

.. code-block:: python

    # Reading data
    current_values = view.read()
    single_value = widget.read()

    # Setting data
    changed = view.fill({"field1": "value1", "field2": "value2"})
    widget.fill("new_value")

    # Checking state
    if widget.is_displayed:
        widget.click()

    # Waiting for elements
    widget.wait_displayed(timeout="10s")

**Error Handling**

.. code-block:: python

    from widgetastic.exceptions import NoSuchElementException

    try:
        view.submit_button.click()
    except NoSuchElementException:
        print("Submit button not found!")

Success Stories
===============

**"Got Our Legacy App Automated in 2 Hours"**
   *"Widgetastic's widget approach made it easy to model our complex legacy forms.
   What took weeks with raw Selenium now took hours."*

**"Perfect for Modern SPAs"**
   *"The smart element detection and wait strategies handle our React app beautifully.
   No more flaky tests!"*

**"Scales with Our Team"**
   *"Junior developers can use existing widgets while seniors create reusable components.
   Perfect for large testing teams."*

Common Use Cases
================

**🔐 Authentication Flows**

.. code-block:: python

    class LoginView(View):
        username = TextInput("#username")
        password = TextInput("#password")
        submit = Button("#login")
        error_message = Text(".error")

    # Usage
    login.fill({"username": "admin", "password": "secret"})
    login.submit.click()

**📊 Data Validation**

.. code-block:: python

    class ReportView(View):
        total_users = Text("#total-users")
        active_users = Text("#active-users")
        report_table = Table("#data-table")

    # Validate numbers
    assert int(report.total_users.text) > 100

    # Check table data
    table_data = report.report_table.read()

**🎛️ Settings Management**

.. code-block:: python

    class SettingsView(View):
        theme = Select("#theme")
        notifications = Checkbox("#notifications")
        language = Select("#language")
        save_button = Button("#save")

    # Bulk configuration
    settings.fill({
        "theme": "dark",
        "notifications": True,
        "language": "en"
    })
    settings.save_button.click()

Integration Examples
====================

**With pytest**

.. code-block:: python

    import pytest
    from playwright.sync_api import sync_playwright

    @pytest.fixture
    def browser():
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            yield Browser(page)
            browser.close()

    def test_login(browser):
        login = LoginView(browser)
        login.fill({"username": "test", "password": "secret"})
        assert login.submit.is_displayed

**With unittest**

.. code-block:: python

    import unittest
    from playwright.sync_api import sync_playwright

    class WebTest(unittest.TestCase):
        def setUp(self):
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch()
            self.page = self.browser.new_page()
            self.wt_browser = Browser(self.page)

        def tearDown(self):
            self.browser.close()
            self.playwright.stop()

Next Steps
==========

1. **Try the Examples**: Start with :doc:`basic-example` and run the code
2. **Learn Patterns**: Review :doc:`common-patterns` for best practices
3. **Deep Dive**: Move to :doc:`../tutorials/index` for comprehensive guides
4. **Get Help**: Check :doc:`../getting-started/concepts` for common questions

.. tip::
   **Learn by Modifying**: The best way to learn widgetastic is to take these examples
   and adapt them to your own applications. Start with something simple and build up complexity!

Ready? Let's start with some practical examples!

.. toctree::
   :maxdepth: 2
   :hidden:

   basic-example
   common-patterns
