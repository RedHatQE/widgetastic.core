====================
Views and Navigation
====================

Views are the cornerstone of widgetastic's architecture. They organize widgets into logical groups that represent pages, sections, or components of your application. This tutorial covers different types of views and navigation patterns.

.. note::
   **Prerequisites**: Complete :doc:`basic-widgets` tutorial first.

Understanding Views
===================

A **View** is a container that groups related widgets together. Think of it as representing a page, dialog, or section of your web application.

**Basic View Example**

.. code-block:: python

    class TestingPageView(View):
        # Page title
        main_title = Text(locator='h1#wt-core-title')

        # Form elements
        text_input = TextInput(id="input")
        checkbox = Checkbox(id="input2")
        submit_button = Button(id="a_button")

        # Check element visibility
        non_existing_element = Text(locator='.//div[@id="non-existing-element"]')

    page = TestingPageView(browser)

    # Check if elements exist on page
    page.main_title.is_displayed        # True
    page.non_existing_element.is_displayed        # False

    # Read page content
    title = page.main_title.read()
    print(f"Page title: {title}")  # "Widgetastic.Core - Testing Page"

View Hierarchy and Nesting
===========================

Views can contain other views, creating hierarchical structures that mirror your application's layout.

**Nested Views**

.. code-block:: python

    class HeaderView(View):
        ROOT = ".header"
        title = Text("h1")
        subtitle = Text(".subtitle")

    class FormView(View):
        ROOT = "#testform"
        username = TextInput(name="input1")
        checkbox = Checkbox(id="input2")

    class MainPageView(View):
        header = HeaderView()
        form = FormView()

        # Page-level elements
        alert_button = Button(id="alert_button")

    page = MainPageView(browser)

    # Access nested elements
    page.header.title.read()
    page.form.username.fill("test_user")
    page.form.checkbox.fill(True)

**ROOT Locator**

The ``ROOT`` attribute defines the container for a view. All widgets in that view are searched within this container.

.. code-block:: python

    class SectionView(View):
        ROOT = ".section-content"  # All widgets scoped to this section

        # These widgets are found within .section-content
        input_field = TextInput(id="input")
        button = Button(id="a_button")

Parametrized Views
==================

Use parametrized views for repeated UI patterns that differ only in parameters.

**ParametrizedView Example**

.. code-block:: python

    from widgetastic.utils import ParametrizedLocator

    class TableRowView(ParametrizedView):
        PARAMETERS = ("row_id",)
        ROOT = ParametrizedLocator("//tr[@data-test='{row_id}']")

        # Widgets within each row
        first_column = Text(".//td[1]")
        second_column = Text(".//td[2]")
        checkbox = Checkbox(locator=".//input[@type='checkbox']")

    class TablePageView(View):
        # Individual rows
        row_abc123 = TableRowView("abc-123")
        row_abc345 = TableRowView("abc-345")
        row_def345 = TableRowView("def-345")

    page = TablePageView(browser)

    # Access specific rows
    page.row_abc123.first_column.read()  # "asdf"
    page.row_abc345.checkbox.fill(True)

    # Or create dynamically
    def get_row(row_id):
        return TableRowView(browser, row_id=row_id)

    dynamic_row = get_row("abc-123")
    dynamic_row.first_column.read()

Conditional Views
=================

Handle dynamic UI sections that change based on application state using conditional views.

**ConditionalSwitchableView Example**

.. code-block:: python

    from widgetastic.widget import ConditionalSwitchableView

    class SwitchableContentView(View):
        selector = Select(id="switchabletesting-select")

        content = ConditionalSwitchableView(reference="selector")

        @content.register("foo")
        class FooContent(View):
            foo_heading = Text(id="switchabletesting-1")
            foo_checkbox = Checkbox(id="switchabletesting-3")

        @content.register("bar")
        class BarContent(View):
            bar_heading = Text(id="switchabletesting-2")
            bar_checkbox = Checkbox(id="switchabletesting-4")

    page = SwitchableContentView(browser)

    # Switch content by changing selector
    page.selector.fill("foo")
    page.content.foo_heading.read()  # "footest"
    page.content.foo_checkbox.fill(True)

    # Switch to bar content
    page.selector.fill("bar")
    page.content.bar_heading.read()  # "bartest"
    page.content.bar_checkbox.fill(True)

View-Level Operations
=====================

Views support batch operations on all their widgets.

**Reading Entire Views**

.. code-block:: python

    class FormView(View):
        username = TextInput(name="input1")
        enabled_checkbox = Checkbox(id="input2")

        # Form submission
        submit_button = Button(id="a_button")

    form = FormView(browser)

    # Read all fillable widgets in the view
    current_values = form.read()
    print(current_values)
    # {'username': 'current_value', 'enabled_checkbox': True}

**Filling Entire Views**

.. code-block:: python

    # Fill multiple widgets at once
    form_data = {
        'username': 'john_doe',
        'enabled_checkbox': True
    }

    form.fill(form_data)

    # Verify the fill
    assert form.read() == form_data

View State and Validation
==========================

Views can validate their state and provide information about their widgets.

**View State Checking**

.. code-block:: python

    class PageView(View):
        visible_element = Text(id="visible_invisible")
        hidden_element = Text(id="invisible")
        form_input = TextInput(name="input1")
        disabled_input = TextInput(name="input1_disabled")

    page = PageView(browser)

    # Check widget display status
    print(f"Visible element displayed: {page.visible_element.is_displayed}")  # True
    print(f"Hidden element displayed: {page.hidden_element.is_displayed}")    # False

    # Check widget enabled status
    print(f"Form input enabled: {page.form_input.is_enabled}")        # True
    print(f"Disabled input enabled: {page.disabled_input.is_enabled}")  # False

Navigation Patterns
===================

Use views to create navigation patterns and page transitions.

**Page Navigation Example**

.. code-block:: python

    class NavigationView(View):
        def navigate_to_section(self, section_name):
            """Navigate to different sections of the page"""
            if section_name == "forms":
                return FormSectionView(self.browser)
            elif section_name == "tables":
                return TableSectionView(self.browser)
            elif section_name == "images":
                return ImageSectionView(self.browser)
            else:
                raise ValueError(f"Unknown section: {section_name}")

    class FormSectionView(View):
        ROOT = ".section:has(.section-header:contains('Input Widgets'))"
        username = TextInput(id="input")
        checkbox = Checkbox(id="input2")

    class TableSectionView(View):
        ROOT = ".section:has(.section-header:contains('Table Widget'))"
        main_table = Table(id="with-thead")

    # Navigation workflow
    nav = NavigationView(browser)

    # Navigate to forms section
    forms_page = nav.navigate_to_section("forms")
    forms_page.username.fill("test_user")

    # Navigate to tables section
    tables_page = nav.navigate_to_section("tables")
    row_count = len(tables_page.main_table.rows)

Best Practices for Views
=========================

**1. Use Descriptive Names**

.. code-block:: python

    # Good: Clear purpose
    class LoginFormView(View):
        pass

    class UserProfileSettingsView(View):
        pass

    # Avoid: Generic names
    class View1(View):
        pass

**2. Logical Widget Grouping**

.. code-block:: python

    # Group related functionality
    class SearchView(View):
        search_input = TextInput(id="search")
        search_button = Button(id="search-btn")
        results_table = Table(id="results")

    # Don't mix unrelated widgets
    class BadView(View):
        login_field = TextInput(id="login")      # Login functionality
        checkout_btn = Button(id="checkout")     # Shopping functionality
        settings_link = Text("a#settings")      # Settings functionality

**3. Use ROOT for Scoping**

.. code-block:: python

    # Scope widgets to specific sections
    class SidebarView(View):
        ROOT = "#sidebar"

        menu_item1 = Text("a[href='/dashboard']")
        menu_item2 = Text("a[href='/profile']")

    # This prevents finding elements in other page sections

**4. Handle Dynamic Content**

.. code-block:: python

    class DynamicContentView(View):
        @property
        def is_loading(self):
            """Check if content is still loading"""
            loading_indicator = Text(locator=".loading-spinner")
            return loading_indicator.is_displayed

        def wait_for_load(self, timeout=30):
            """Wait for dynamic content to load"""
            self.browser.wait_for(lambda: not self.is_loading, timeout=timeout)

Common View Patterns
====================

**Modal Dialog View**

.. code-block:: python

    class ModalDialogView(View):
        ROOT = ".modal-dialog"

        title = Text("h4.modal-title")
        content = Text(".modal-body")
        ok_button = Button(".btn-primary")
        cancel_button = Button(".btn-secondary")

        def close(self):
            """Close modal using OK button"""
            self.ok_button.click()

        def cancel(self):
            """Close modal using Cancel button"""
            self.cancel_button.click()

**Pagination View**

.. code-block:: python

    class PaginatedTableView(View):
        table = Table(id="data-table")

        # Pagination controls
        previous_btn = Button(".pagination .prev")
        next_btn = Button(".pagination .next")
        page_info = Text(".pagination .info")

        def go_to_next_page(self):
            """Navigate to next page if available"""
            if self.next_btn.is_enabled:
                self.next_btn.click()
                self.browser.wait_for(lambda: not self.is_loading)

        def go_to_previous_page(self):
            """Navigate to previous page if available"""
            if self.previous_btn.is_enabled:
                self.previous_btn.click()
                self.browser.wait_for(lambda: not self.is_loading)

Summary
=======

Views are essential for organizing and structuring your automation code:

* **Basic Views**: Container for related widgets
* **Nested Views**: Hierarchical page structures
* **Parametrized Views**: Handle repeated UI patterns
* **Conditional Views**: Adapt to dynamic content
* **View Operations**: Batch read/fill operations
* **Navigation**: Structured page transitions

**Next Step**: Learn :doc:`browser-methods` to master browser interactions and element operations.
