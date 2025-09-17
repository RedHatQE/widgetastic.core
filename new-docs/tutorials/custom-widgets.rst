===================================
Custom Widget Development Tutorial
===================================

This tutorial demonstrates how to create custom widgets in Widgetastic.core. You'll learn to extend the framework with your own widget types, implement the read/fill interface, and build reusable automation components for complex UI patterns.

.. note::
   **Time Required**: 60 minutes
   **Prerequisites**: Advanced widgets and fill strategies tutorials
   **Test Pages Used**: ``testing/html/testing_page.html``

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Understand widget architecture and design principles
* ✅ Create custom widgets with proper read/fill interfaces
* ✅ Implement complex locator strategies and element handling
* ✅ Handle widget state management and validation
* ✅ Build reusable widget components for your applications

Understanding Widget Architecture
================================

Widgetastic widgets follow a specific architecture pattern:

**Core Widget Components**
* **Base Widget Class**: Inherits from ``Widget`` base class
* **Locator Strategy**: Defines how to find the widget on the page
* **Read Interface**: Extracts current state/value from the widget
* **Fill Interface**: Sets new state/value in the widget
* **State Management**: Handles widget lifecycle and caching

**Widget Design Principles**
* **Single Responsibility**: Each widget handles one UI component type
* **Consistent Interface**: Follow read/fill pattern for predictability
* **Error Handling**: Gracefully handle missing or invalid elements
* **Performance**: Cache expensive operations and minimize DOM access
* **Reusability**: Design for use across different applications

Setting Up Custom Widget Environment
====================================

.. code-block:: python

    from pathlib import Path
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import Widget, View, Text, TextInput, ClickableMixin
    from widgetastic.exceptions import NoSuchElementException
    from widgetastic.utils import ParametrizedLocator, cached_property
    from widgetastic.log import logged

    def setup_custom_widget_browser():
        """Setup browser for custom widget development."""
        test_page_path = Path("testing/html/testing_page.html").resolve()
        test_page_url = test_page_path.as_uri()

        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()
        browser = Browser(page)

        browser.goto(test_page_url)

        return browser, p, browser_instance, context

    browser, playwright, browser_instance, context = setup_custom_widget_browser()

Simple Custom Widget Development
================================

Start with basic custom widget patterns:

**Basic Custom Widget Example**

.. code-block:: python

    class StatusIndicator(Widget):
        """Custom widget for status indicator elements."""

        def __init__(self, parent, locator=None, logger=None):
            """Initialize status indicator widget."""
            super().__init__(parent, logger)
            if locator:
                self.locator = locator

        def __locator__(self):
            """Define how to locate this widget on the page."""
            # This should be overridden by subclasses or provided in constructor
            if hasattr(self, 'locator'):
                return self.locator
            raise NotImplementedError("StatusIndicator requires a locator")

        @property
        def status_class(self):
            """Get the CSS class that indicates status."""
            classes = self.browser.get_attribute(self, "class")
            return classes.split() if classes else []

        @property
        def status_text(self):
            """Get the status text content."""
            return self.browser.text(self)

        def read(self):
            """Read the current status."""
            classes = self.status_class
            text = self.status_text

            # Determine status based on classes and text
            if 'success' in classes or 'active' in classes:
                return {'status': 'active', 'text': text}
            elif 'error' in classes or 'failed' in classes:
                return {'status': 'error', 'text': text}
            elif 'warning' in classes:
                return {'status': 'warning', 'text': text}
            else:
                return {'status': 'unknown', 'text': text}

        def is_active(self):
            """Check if status indicates active state."""
            status = self.read()
            return status['status'] == 'active'

        def is_error(self):
            """Check if status indicates error state."""
            status = self.read()
            return status['status'] == 'error'

    # Test the custom status indicator
    class TestStatusView(View):
        # Use existing elements from testing page as status indicators
        status_message = StatusIndicator(locator="#click_result")  # Button click result
        page_title = StatusIndicator(locator="h1#wt-core-title")  # Page title

    test_view = TestStatusView(browser)

    print("=== Custom Status Widget Test ===")
    message_status = test_view.status_message.read()
    print(f"Status message: {message_status}")

    title_status = test_view.page_title.read()
    print(f"Page title status: {title_status}")

    print(f"Message is active: {test_view.status_message.is_active()}")

**Enhanced Custom Widget with Fill Interface**

.. code-block:: python

    class ProgressBar(Widget):
        """Custom widget for progress bar elements."""

        def __locator__(self):
            """Locate progress bar element."""
            # In a real application, this would be a progress bar
            # For demo, we'll use an existing element
            return "#exact_dimensions"

        @property
        def progress_value(self):
            """Get progress value from aria-valuenow or data attributes."""
            # Check for standard progress attributes
            value = self.browser.get_attribute(self, "aria-valuenow")
            if value:
                return int(value)

            # Check for data attributes
            value = self.browser.get_attribute(self, "data-progress")
            if value:
                return int(value)

            # Fallback: calculate from width if it's a visual progress bar
            style = self.browser.get_attribute(self, "style") or ""
            if "width:" in style:
                # Extract width percentage (simplified)
                import re
                match = re.search(r'width:\s*(\d+)%', style)
                if match:
                    return int(match.group(1))

            return 0

        @property
        def max_value(self):
            """Get maximum progress value."""
            max_val = self.browser.get_attribute(self, "aria-valuemax")
            return int(max_val) if max_val else 100

        def read(self):
            """Read current progress state."""
            current = self.progress_value
            maximum = self.max_value
            percentage = (current / maximum) * 100 if maximum > 0 else 0

            return {
                'current': current,
                'max': maximum,
                'percentage': percentage,
                'completed': percentage >= 100
            }

        def wait_for_completion(self, timeout=30):
            """Wait for progress to complete."""
            import time
            start_time = time.time()

            while time.time() - start_time < timeout:
                progress = self.read()
                if progress['completed']:
                    return True
                time.sleep(0.5)

            return False

        def wait_for_progress(self, target_percentage, timeout=30):
            """Wait for specific progress percentage."""
            import time
            start_time = time.time()

            while time.time() - start_time < timeout:
                progress = self.read()
                if progress['percentage'] >= target_percentage:
                    return True
                time.sleep(0.5)

            return False

    # Test progress bar widget
    progress_bar = ProgressBar(browser)

    print("\n=== Custom Progress Bar Widget Test ===")
    if progress_bar.is_displayed:
        progress_data = progress_bar.read()
        print(f"Progress bar state: {progress_data}")
    else:
        print("Progress bar not displayed")

Complex Custom Widget with Multiple Elements
============================================

Build sophisticated widgets that manage multiple sub-elements:

**Multi-Element Custom Widget**

.. code-block:: python

    class FormSection(Widget):
        """Custom widget representing a form section with multiple inputs."""

        def __init__(self, parent, section_locator=None, logger=None):
            """Initialize form section widget."""
            super().__init__(parent, logger)
            if section_locator:
                self.section_locator = section_locator

        def __locator__(self):
            """Locate the form section container."""
            if hasattr(self, 'section_locator'):
                return self.section_locator
            return "#testform"  # Default to test form on page

        def get_input_elements(self):
            """Get all input elements within this section."""
            inputs = self.browser.elements("input", parent=self)
            return inputs

        def get_input_by_name(self, name):
            """Get specific input by name attribute."""
            try:
                return self.browser.element(f"input[name='{name}']", parent=self)
            except NoSuchElementException:
                return None

        def get_input_by_id(self, input_id):
            """Get specific input by ID attribute."""
            try:
                return self.browser.element(f"input[id='{input_id}']", parent=self)
            except NoSuchElementException:
                return None

        def get_all_labels(self):
            """Get all label elements in this section."""
            labels = self.browser.elements("label", parent=self)
            return labels

        def read(self):
            """Read all form data from this section."""
            data = {}
            inputs = self.get_input_elements()

            for input_element in inputs:
                # Get input properties
                input_name = self.browser.get_attribute(input_element, "name")
                input_id = self.browser.get_attribute(input_element, "id")
                input_type = self.browser.get_attribute(input_element, "type") or "text"

                # Use name or id as key
                key = input_name or input_id
                if not key:
                    continue

                # Read value based on input type
                if input_type == "checkbox":
                    data[key] = self.browser.is_checked(input_element)
                elif input_type == "radio":
                    if self.browser.is_checked(input_element):
                        data[key] = self.browser.get_attribute(input_element, "value")
                else:
                    # Text, email, password, etc.
                    data[key] = self.browser.input_value(input_element)

            return data

        def fill(self, data):
            """Fill form section with provided data."""
            changed = {}

            for field_name, value in data.items():
                # Try to find input by name first, then by ID
                input_element = self.get_input_by_name(field_name)
                if not input_element:
                    input_element = self.get_input_by_id(field_name)

                if not input_element:
                    continue

                # Get current value to check if change is needed
                input_type = self.browser.get_attribute(input_element, "type") or "text"

                if input_type == "checkbox":
                    current_checked = self.browser.is_checked(input_element)
                    target_checked = bool(value)

                    if current_checked != target_checked:
                        if target_checked:
                            self.browser.check(input_element)
                        else:
                            self.browser.uncheck(input_element)
                        changed[field_name] = True
                    else:
                        changed[field_name] = False

                else:
                    # Text inputs
                    current_value = self.browser.input_value(input_element)
                    if current_value != str(value):
                        self.browser.fill(input_element, str(value))
                        changed[field_name] = True
                    else:
                        changed[field_name] = False

            return changed

        def validate_required_fields(self, required_fields):
            """Validate that required fields have values."""
            data = self.read()
            errors = []

            for field in required_fields:
                if field not in data or not data[field]:
                    errors.append(f"Required field '{field}' is empty")

            return errors

        def clear_all(self):
            """Clear all inputs in this form section."""
            inputs = self.get_input_elements()

            for input_element in inputs:
                input_type = self.browser.get_attribute(input_element, "type") or "text"

                if input_type == "checkbox":
                    if self.browser.is_checked(input_element):
                        self.browser.uncheck(input_element)
                elif input_type != "radio":  # Don't clear radio buttons
                    self.browser.clear(input_element)

    # Test complex form section widget
    form_section = FormSection(browser)

    print("\n=== Complex Form Section Widget Test ===")

    # Read current form data
    current_data = form_section.read()
    print(f"Current form data: {current_data}")

    # Fill form with test data
    test_data = {
        'input1': 'custom_widget_test',
        'input2': True  # checkbox
    }

    fill_results = form_section.fill(test_data)
    print(f"Fill results: {fill_results}")

    # Read updated data
    updated_data = form_section.read()
    print(f"Updated form data: {updated_data}")

    # Test validation
    required_fields = ['input1']
    validation_errors = form_section.validate_required_fields(required_fields)
    print(f"Validation errors: {validation_errors}")

Advanced Custom Widget Patterns
===============================

Implement sophisticated widget patterns with caching and performance optimization:

**Cached Property Custom Widget**

.. code-block:: python

    from widgetastic.utils import cached_property

    class DataTable(Widget):
        """Advanced custom widget for data tables with caching."""

        def __locator__(self):
            """Locate the data table."""
            return "#with-thead"  # Use existing table on test page

        @cached_property
        def headers(self):
            """Get table headers (cached for performance)."""
            header_elements = self.browser.elements("thead th", parent=self)
            return [self.browser.text(h) for h in header_elements]

        @cached_property
        def row_count(self):
            """Get number of rows (cached)."""
            rows = self.browser.elements("tbody tr", parent=self)
            return len(rows)

        def get_row(self, index):
            """Get specific row data."""
            try:
                row_element = self.browser.element(f"tbody tr:nth-child({index + 1})", parent=self)
                cells = self.browser.elements("td", parent=row_element)
                return [self.browser.text(cell) for cell in cells]
            except NoSuchElementException:
                return None

        def get_column_data(self, column_index):
            """Get all data from specific column."""
            column_data = []
            for row_index in range(self.row_count):
                row_data = self.get_row(row_index)
                if row_data and len(row_data) > column_index:
                    column_data.append(row_data[column_index])
            return column_data

        def search_rows(self, search_term):
            """Search for rows containing specific text."""
            matching_rows = []

            for row_index in range(self.row_count):
                row_data = self.get_row(row_index)
                if row_data and any(search_term.lower() in cell.lower() for cell in row_data):
                    matching_rows.append({'index': row_index, 'data': row_data})

            return matching_rows

        def read(self):
            """Read complete table data."""
            return {
                'headers': self.headers,
                'row_count': self.row_count,
                'rows': [self.get_row(i) for i in range(self.row_count)]
            }

        def click_cell(self, row_index, column_index):
            """Click specific table cell."""
            try:
                cell = self.browser.element(
                    f"tbody tr:nth-child({row_index + 1}) td:nth-child({column_index + 1})",
                    parent=self
                )
                self.browser.click(cell)
                return True
            except NoSuchElementException:
                return False

        def get_cell_widget(self, row_index, column_index, widget_class):
            """Get widget from specific table cell."""
            try:
                cell = self.browser.element(
                    f"tbody tr:nth-child({row_index + 1}) td:nth-child({column_index + 1})",
                    parent=self
                )
                # Create widget instance with cell as parent
                widget = widget_class(cell)
                return widget if widget.is_displayed else None
            except NoSuchElementException:
                return None

    # Test advanced data table widget
    data_table = DataTable(browser)

    print("\n=== Advanced Data Table Widget Test ===")

    if data_table.is_displayed:
        # Read table structure
        table_data = data_table.read()
        print(f"Table headers: {table_data['headers']}")
        print(f"Row count: {table_data['row_count']}")

        # Get specific row
        first_row = data_table.get_row(0)
        print(f"First row: {first_row}")

        # Get column data
        first_column = data_table.get_column_data(0)
        print(f"First column data: {first_column}")

        # Search functionality
        search_results = data_table.search_rows("foo")
        print(f"Search results for 'foo': {len(search_results)} matches")

**Parameterized Custom Widget**

.. code-block:: python

    from widgetastic.utils import ParametrizedLocator

    class ParameterizedButton(Widget, ClickableMixin):
        """Custom button widget that accepts parameters."""

        def __init__(self, parent, button_type=None, button_id=None, logger=None):
            """Initialize parameterized button."""
            super().__init__(parent, logger)
            self.button_type = button_type
            self.button_id = button_id

        def __locator__(self):
            """Generate locator based on parameters."""
            if self.button_id:
                return f"button[id='{self.button_id}']"
            elif self.button_type:
                return f"button[type='{self.button_type}']"
            else:
                return "button"

        @property
        def button_text(self):
            """Get button text."""
            return self.browser.text(self)

        @property
        def is_enabled(self):
            """Check if button is enabled."""
            return self.browser.is_enabled(self)

        @property
        def css_classes(self):
            """Get button CSS classes."""
            classes = self.browser.get_attribute(self, "class") or ""
            return classes.split()

        def read(self):
            """Read button state."""
            return {
                'text': self.button_text,
                'enabled': self.is_enabled,
                'classes': self.css_classes,
                'displayed': self.is_displayed
            }

        def has_class(self, class_name):
            """Check if button has specific CSS class."""
            return class_name in self.css_classes

        def wait_for_enabled(self, timeout=10):
            """Wait for button to become enabled."""
            return self.browser.wait_for_element(
                self,
                condition=lambda el: self.browser.is_enabled(el),
                timeout=timeout
            )

    # Test parameterized button widgets
    class ButtonTestView(View):
        # Different button instances with parameters
        click_button = ParameterizedButton(button_id="a_button")
        disabled_button = ParameterizedButton(button_id="disabled_button")
        multi_button = ParameterizedButton(button_id="multi_button")

    button_view = ButtonTestView(browser)

    print("\n=== Parameterized Button Widget Test ===")

    # Test each button
    buttons = [
        ('click_button', button_view.click_button),
        ('disabled_button', button_view.disabled_button),
        ('multi_button', button_view.multi_button)
    ]

    for name, button in buttons:
        if button.is_displayed:
            button_state = button.read()
            print(f"{name}: {button_state}")

            # Test specific features
            print(f"  Has 'clicked' class: {button.has_class('clicked')}")
        else:
            print(f"{name}: Not displayed")

Custom Widget with Logging and Debugging
========================================

Implement proper logging and debugging features:

**Logged Custom Widget**

.. code-block:: python

    from widgetastic.log import logged

    class SmartForm(Widget):
        """Custom form widget with comprehensive logging."""

        def __init__(self, parent, form_locator=None, logger=None):
            super().__init__(parent, logger)
            self.form_locator = form_locator or "#testform"

        def __locator__(self):
            return self.form_locator

        @logged
        def find_all_inputs(self):
            """Find all inputs with detailed logging."""
            inputs = self.browser.elements("input", parent=self)
            self.logger.info(f"Found {len(inputs)} input elements")

            input_details = []
            for i, input_el in enumerate(inputs):
                details = {
                    'index': i,
                    'type': self.browser.get_attribute(input_el, 'type'),
                    'name': self.browser.get_attribute(input_el, 'name'),
                    'id': self.browser.get_attribute(input_el, 'id'),
                    'enabled': self.browser.is_enabled(input_el),
                    'displayed': self.browser.is_displayed(input_el)
                }
                input_details.append(details)
                self.logger.debug(f"Input {i}: {details}")

            return input_details

        @logged
        def smart_fill(self, data, strategy='adaptive'):
            """Smart fill with different strategies and logging."""
            self.logger.info(f"Starting smart fill with strategy '{strategy}' and data: {data}")

            input_details = self.find_all_inputs()
            results = {}

            for field_name, value in data.items():
                self.logger.debug(f"Processing field '{field_name}' with value '{value}'")

                # Find matching input
                target_input = None
                for input_info in input_details:
                    if (input_info['name'] == field_name or
                        input_info['id'] == field_name):
                        target_input = input_info
                        break

                if not target_input:
                    self.logger.warning(f"No input found for field '{field_name}'")
                    results[field_name] = {'error': 'Input not found'}
                    continue

                if not target_input['enabled']:
                    self.logger.warning(f"Input '{field_name}' is disabled")
                    results[field_name] = {'error': 'Input disabled'}
                    continue

                # Get actual element and fill
                input_element = self.browser.elements("input", parent=self)[target_input['index']]

                try:
                    if target_input['type'] == 'checkbox':
                        current = self.browser.is_checked(input_element)
                        target = bool(value)

                        if current != target:
                            if target:
                                self.browser.check(input_element)
                            else:
                                self.browser.uncheck(input_element)
                            results[field_name] = {'changed': True, 'from': current, 'to': target}
                            self.logger.info(f"Checkbox '{field_name}' changed from {current} to {target}")
                        else:
                            results[field_name] = {'changed': False, 'value': current}

                    else:
                        current = self.browser.input_value(input_element)
                        if current != str(value):
                            self.browser.fill(input_element, str(value))
                            results[field_name] = {'changed': True, 'from': current, 'to': str(value)}
                            self.logger.info(f"Input '{field_name}' changed from '{current}' to '{value}'")
                        else:
                            results[field_name] = {'changed': False, 'value': current}

                except Exception as e:
                    self.logger.error(f"Error filling field '{field_name}': {e}")
                    results[field_name] = {'error': str(e)}

            self.logger.info(f"Smart fill completed. Results: {results}")
            return results

        @logged
        def validate_form(self, validation_rules):
            """Validate form with comprehensive logging."""
            self.logger.info(f"Starting form validation with rules: {validation_rules}")

            current_data = {}
            input_details = self.find_all_inputs()

            # Read current values
            for input_info in input_details:
                field_name = input_info['name'] or input_info['id']
                if field_name:
                    input_element = self.browser.elements("input", parent=self)[input_info['index']]
                    if input_info['type'] == 'checkbox':
                        current_data[field_name] = self.browser.is_checked(input_element)
                    else:
                        current_data[field_name] = self.browser.input_value(input_element)

            # Validate against rules
            errors = []
            for field, rules in validation_rules.items():
                if field not in current_data:
                    errors.append(f"Field '{field}' not found")
                    continue

                value = current_data[field]

                # Required validation
                if rules.get('required') and not value:
                    errors.append(f"Field '{field}' is required")

                # Length validation
                if 'min_length' in rules and len(str(value)) < rules['min_length']:
                    errors.append(f"Field '{field}' must be at least {rules['min_length']} characters")

                # Pattern validation
                if 'pattern' in rules and value:
                    import re
                    if not re.match(rules['pattern'], str(value)):
                        errors.append(f"Field '{field}' does not match required pattern")

            self.logger.info(f"Validation completed. Errors: {errors}")
            return {'valid': len(errors) == 0, 'errors': errors, 'data': current_data}

    # Test smart form widget
    smart_form = SmartForm(browser)

    print("\n=== Smart Form Widget with Logging Test ===")

    # Test smart fill
    test_data = {
        'input1': 'smart_form_test',
        'input2': True
    }

    fill_results = smart_form.smart_fill(test_data)
    print(f"Smart fill results: {fill_results}")

    # Test validation
    validation_rules = {
        'input1': {'required': True, 'min_length': 3},
        'input2': {'required': False}
    }

    validation_results = smart_form.validate_form(validation_rules)
    print(f"Validation results: {validation_results}")

Widget Testing and Quality Assurance
====================================

Implement comprehensive testing for custom widgets:

**Widget Test Framework**

.. code-block:: python

    class WidgetTester:
        """Framework for testing custom widgets."""

        def __init__(self, browser):
            self.browser = browser
            self.test_results = []

        def test_widget_basic_functionality(self, widget, widget_name):
            """Test basic widget functionality."""
            tests = []

            # Test 1: Widget existence and display
            try:
                displayed = widget.is_displayed
                tests.append({
                    'test': 'is_displayed',
                    'passed': displayed,
                    'message': f"Widget is {'displayed' if displayed else 'not displayed'}"
                })
            except Exception as e:
                tests.append({
                    'test': 'is_displayed',
                    'passed': False,
                    'message': f"Error checking display: {e}"
                })

            # Test 2: Read functionality
            try:
                read_result = widget.read()
                tests.append({
                    'test': 'read',
                    'passed': read_result is not None,
                    'message': f"Read returned: {type(read_result).__name__}",
                    'data': read_result
                })
            except Exception as e:
                tests.append({
                    'test': 'read',
                    'passed': False,
                    'message': f"Error reading widget: {e}"
                })

            # Test 3: Fill functionality (if available)
            if hasattr(widget, 'fill'):
                try:
                    # Test with simple data
                    test_value = "test_value"
                    fill_result = widget.fill(test_value)
                    tests.append({
                        'test': 'fill',
                        'passed': fill_result is not None,
                        'message': f"Fill returned: {fill_result}",
                        'data': fill_result
                    })
                except Exception as e:
                    tests.append({
                        'test': 'fill',
                        'passed': False,
                        'message': f"Error filling widget: {e}"
                    })

            return {'widget': widget_name, 'tests': tests}

        def run_comprehensive_test_suite(self, widgets_dict):
            """Run comprehensive tests on multiple widgets."""
            all_results = {}

            for widget_name, widget in widgets_dict.items():
                print(f"\nTesting {widget_name}...")
                result = self.test_widget_basic_functionality(widget, widget_name)
                all_results[widget_name] = result

                # Print test results
                for test in result['tests']:
                    status = "PASS" if test['passed'] else "FAIL"
                    print(f"  {test['test']}: {status} - {test['message']}")

            return all_results

        def generate_test_report(self, test_results):
            """Generate comprehensive test report."""
            total_widgets = len(test_results)
            total_tests = sum(len(result['tests']) for result in test_results.values())
            passed_tests = sum(
                len([t for t in result['tests'] if t['passed']])
                for result in test_results.values()
            )

            report = {
                'summary': {
                    'total_widgets': total_widgets,
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': total_tests - passed_tests,
                    'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
                },
                'details': test_results
            }

            return report

    # Test all custom widgets
    widgets_to_test = {
        'StatusIndicator': StatusIndicator(browser, locator="#click_result"),
        'ProgressBar': ProgressBar(browser),
        'FormSection': FormSection(browser),
        'DataTable': DataTable(browser),
        'SmartForm': SmartForm(browser)
    }

    tester = WidgetTester(browser)
    test_results = tester.run_comprehensive_test_suite(widgets_to_test)
    test_report = tester.generate_test_report(test_results)

    print("\n=== Custom Widget Test Report ===")
    print(f"Total widgets tested: {test_report['summary']['total_widgets']}")
    print(f"Total tests run: {test_report['summary']['total_tests']}")
    print(f"Tests passed: {test_report['summary']['passed_tests']}")
    print(f"Tests failed: {test_report['summary']['failed_tests']}")
    print(f"Success rate: {test_report['summary']['success_rate']:.1f}%")

Best Practices for Custom Widgets
=================================

Guidelines for creating maintainable and robust custom widgets:

**Custom Widget Best Practices**

.. code-block:: python

    # 1. Follow naming conventions and inheritance hierarchy
    class GoodCustomWidget(Widget):
        """✓ Good - Clear name, inherits from Widget base class."""

        def __locator__(self):
            """✓ Good - Implements required locator method."""
            return self.locator

        def read(self):
            """✓ Good - Implements read interface."""
            return self.browser.text(self)

        def __repr__(self):
            """✓ Good - Provides useful string representation."""
            return f"{self.__class__.__name__}(locator={self.__locator__()})"

    # 2. Handle errors gracefully
    class RobustWidget(Widget):
        """Widget with comprehensive error handling."""

        def read(self):
            """Read with error handling."""
            try:
                if not self.is_displayed:
                    return None

                return self.browser.text(self)

            except NoSuchElementException:
                self.logger.warning(f"Element not found for {self}")
                return None
            except Exception as e:
                self.logger.error(f"Unexpected error reading {self}: {e}")
                return None

        def safe_fill(self, value):
            """Fill with comprehensive error checking."""
            try:
                if not self.is_displayed:
                    return {'success': False, 'error': 'Widget not displayed'}

                if hasattr(self, 'is_enabled') and not self.is_enabled:
                    return {'success': False, 'error': 'Widget not enabled'}

                result = self.fill(value)
                return {'success': True, 'result': result}

            except Exception as e:
                return {'success': False, 'error': str(e)}

    # 3. Use caching for expensive operations
    class PerformantWidget(Widget):
        """Widget with performance optimizations."""

        @cached_property
        def expensive_computation(self):
            """Cache expensive DOM operations."""
            # This would be cached after first access
            return len(self.browser.elements("*", parent=self))

        def invalidate_cache(self):
            """Clear cached properties when DOM changes."""
            if hasattr(self, '_expensive_computation'):
                delattr(self, '_expensive_computation')

    # 4. Document widget behavior and parameters
    class DocumentedWidget(Widget):
        """
        Custom widget for complex UI component.

        This widget handles XYZ functionality and provides:
        - Read interface for current state
        - Fill interface for setting values
        - Validation for input data
        - Error handling for edge cases

        Parameters:
            locator: CSS selector or XPath for the widget
            validation_mode: 'strict' or 'lenient' validation
            timeout: Maximum wait time for operations

        Example:
            widget = DocumentedWidget(browser, locator="#my-widget")
            current_state = widget.read()
            widget.fill({"field1": "value1"})
        """

        def __init__(self, parent, locator=None, validation_mode='strict', timeout=5, logger=None):
            super().__init__(parent, logger)
            self.locator = locator
            self.validation_mode = validation_mode
            self.timeout = timeout

Final Cleanup
==============

.. code-block:: python

    try:
        context.close()
        browser_instance.close()
        playwright.stop()
    except Exception as e:
        print(f"Cleanup error: {e}")

Summary
=======

Custom widget development in Widgetastic.core provides:

* **Extensibility**: Create widgets for any UI component type
* **Reusability**: Build widgets once, use across multiple projects
* **Consistency**: Follow framework patterns for predictable behavior
* **Performance**: Implement caching and optimization strategies
* **Maintainability**: Proper error handling, logging, and documentation

Key takeaways:
* Always inherit from Widget base class and implement __locator__()
* Follow read/fill interface pattern for consistency
* Handle errors gracefully with try/catch and logging
* Use caching for expensive DOM operations
* Test widgets thoroughly with comprehensive test suites
* Document widget behavior, parameters, and usage examples
* Consider performance implications in widget design

This completes the custom widget development tutorial. You can now create sophisticated, reusable widgets that extend Widgetastic.core for your specific automation needs.
