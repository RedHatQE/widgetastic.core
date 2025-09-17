=========================
Advanced Widgets Tutorial
=========================

This tutorial demonstrates advanced widgets in Widgetastic.core using comprehensive examples from ``testing_page.html``. You'll learn to work with tables, handle drag & drop operations, and interact with complex UI components.

.. note::
   **Time Required**: 60 minutes
   **Prerequisites**: Basic widgets tutorial
   **Test Pages Used**: ``testing/html/testing_page.html``

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Master the Table widget for complex data structures
* ✅ Handle table rows, columns, and embedded widgets
* ✅ Implement drag & drop automation
* ✅ Work with dynamic and sortable content
* ✅ Handle complex form scenarios and edge cases

Setting Up Advanced Widget Environment
======================================

.. code-block:: python

    from pathlib import Path
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput, Checkbox, Table

    def setup_advanced_widgets_browser():
        """Setup browser with testing page for advanced widgets."""
        test_page_path = Path("testing/html/testing_page.html").resolve()
        test_page_url = test_page_path.as_uri()

        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()
        browser = Browser(page)

        # Navigate to comprehensive testing page
        browser.goto(test_page_url)

        return browser, p, browser_instance, context

    browser, playwright, browser_instance, context = setup_advanced_widgets_browser()

Table Widget Fundamentals
=========================

The :py:class:`~widgetastic.widget.Table` widget handles HTML tables with advanced features like embedded widgets, filtering, and complex structures.

**Basic Table Structure**

.. code-block:: python

    from widgetastic.widget.table import TableRow, TableColumn

    class StandardTable(Table):
        """Standard table with proper thead/tbody structure."""
        ROOT = "#with-thead"

    standard_table = StandardTable(browser)

    # Basic table information
    print(f"Table headers: {standard_table.headers}")
    # Output: [None, 'Column 1', 'Column 2', 'Column 3', 'Column 4']

    print(f"Number of rows: {len(standard_table.rows)}")
    # Output: 3

    print(f"Table displayed: {standard_table.is_displayed}")
    # Output: True

**Reading Table Data**

.. code-block:: python

    # Iterate through all rows
    for i, row in enumerate(standard_table):
        print(f"Row {i}: {[cell.text for cell in row]}")
        # Output:
        # Row 0: ['asdf', 'qwer', 'yxcv', 'uiop', '']
        # Row 1: ['foo_x', 'bar_x', 'baz_x', 'bat_x', '']
        # Row 2: ['foo_y', 'bar_y', 'baz_y', 'bat_y', '']

    # Access specific rows
    first_row = standard_table[0]
    print(f"First row data: {[cell.text for cell in first_row]}")

    # Access specific cells
    first_cell = standard_table[0][0]  # Row 0, Column 0
    print(f"First cell text: {first_cell.text}")  # "asdf"

**Table Row Selection and Filtering**

.. code-block:: python

    # Find rows by content (returns first matching row)
    row_with_foo = standard_table.row("Column 1"="qwer")  # Find by column content
    if row_with_foo:
        print(f"Found row with 'qwer': {[cell.text for cell in row_with_foo]}")

    # Alternative row selection by data attributes
    # Tables in testing page have data-test attributes
    row_by_data = standard_table.row(("data-test", "abc-123"))
    if row_by_data:
        print(f"Row with data-test='abc-123': {[cell.text for cell in row_by_data]}")

Tables with Embedded Widgets
============================

The testing page includes tables with embedded form elements:

**Table with Widget Columns**

.. code-block:: python

    class TableWithWidgets(Table):
        """Table containing input widgets within cells."""
        ROOT = "#withwidgets"

        # Define column widgets for specific columns
        column_widgets = {
            1: TextInput(),  # Column 2 contains text inputs
            2: TextInput(),  # Column 3 contains text inputs
        }

    widget_table = TableWithWidgets(browser)

    # Access embedded widgets
    print(f"Table headers: {widget_table.headers}")
    # Output: [None, 'Column 2', 'Column 3']

    # Work with embedded widgets in first row
    first_row = widget_table[0]

    # The widget in column 2 (index 1)
    input_widget_col2 = first_row[1].widget
    if hasattr(input_widget_col2, 'fill'):
        input_widget_col2.fill("foo_input_value")
        print(f"Filled column 2 input: {input_widget_col2.read()}")

    # Regular text cell (column 3, index 2)
    text_cell = first_row[2]
    print(f"Column 3 text: {text_cell.text}")

**Advanced Table Widget Patterns**

.. code-block:: python

    class AdvancedTableOperations(View):
        standard_table = StandardTable()
        widget_table = TableWithWidgets()

        def fill_table_row(self, row_index, column_data):
            """Fill a specific table row with data."""
            row = self.widget_table[row_index]
            results = {}

            for col_index, value in column_data.items():
                cell = row[col_index]
                if hasattr(cell, 'widget') and hasattr(cell.widget, 'fill'):
                    changed = cell.widget.fill(value)
                    results[col_index] = {
                        'changed': changed,
                        'value': cell.widget.read()
                    }
                else:
                    results[col_index] = {
                        'text': cell.text,
                        'error': 'Not fillable'
                    }
            return results

        def read_table_data(self, table):
            """Read all data from a table."""
            data = []
            for row in table:
                row_data = []
                for cell in row:
                    if hasattr(cell, 'widget') and hasattr(cell.widget, 'read'):
                        # Widget cell
                        row_data.append(cell.widget.read())
                    else:
                        # Text cell
                        row_data.append(cell.text)
                data.append(row_data)
            return data

    advanced_ops = AdvancedTableOperations(browser)

    # Fill table widgets
    fill_results = advanced_ops.fill_table_row(0, {1: "new_foo_value"})
    print(f"Fill results: {fill_results}")

    # Read all widget table data
    widget_data = advanced_ops.read_table_data(advanced_ops.widget_table)
    print(f"Widget table data: {widget_data}")

Complex Table Structures
========================

The testing page includes tables with rowspan/colspan and multiple tbody elements:

**Tables with Rowspan/Colspan**

.. code-block:: python

    class ComplexTable(Table):
        """Table with rowspan and colspan cells."""
        ROOT = "#rowcolspan_table"

        column_widgets = {
            4: TextInput()  # Widget column (5th column, 0-indexed as 4)
        }

    complex_table = ComplexTable(browser)

    print(f"Complex table headers: {complex_table.headers}")
    # Output: ['#', 'First Name', 'Last Name', 'Username', 'Widget']

    # Handle complex cell structures
    for i, row in enumerate(complex_table):
        print(f"Row {i} cells: {len(row)}")
        for j, cell in enumerate(row):
            colspan = browser.get_attribute(cell, "colspan") if hasattr(cell, 'get_attribute') else None
            rowspan = browser.get_attribute(cell, "rowspan") if hasattr(cell, 'get_attribute') else None
            span_info = f" (colspan={colspan}, rowspan={rowspan})" if colspan or rowspan else ""

            if hasattr(cell, 'widget') and hasattr(cell.widget, 'read'):
                print(f"  Cell [{i}][{j}]: Widget value = {cell.widget.read()}{span_info}")
            else:
                print(f"  Cell [{i}][{j}]: Text = '{cell.text}'{span_info}")

**Multiple Tbody Tables**

.. code-block:: python

    class MultiTBodyTable(Table):
        """Table with multiple tbody elements."""
        ROOT = "#multiple_tbody_table"

    multi_tbody_table = MultiTBodyTable(browser)

    # Access different tbody sections
    if hasattr(multi_tbody_table, 'bodies'):
        print(f"Number of tbody sections: {len(multi_tbody_table.bodies)}")

        for i, tbody in enumerate(multi_tbody_table.bodies):
            print(f"TBody {i}: {tbody}")
            # Each tbody can have data-test attributes
            data_test = browser.get_attribute(tbody, 'data-test')
            print(f"  data-test attribute: {data_test}")

**Dynamic Table Content**

.. code-block:: python

    class DynamicTable(Table):
        """Table with dynamically added rows."""
        ROOT = "#dynamic"

    dynamic_table = DynamicTable(browser)

    # Initial state
    initial_rows = len(dynamic_table.rows)
    print(f"Initial row count: {initial_rows}")

    # Add new row using the button on the page
    add_button = browser.element("#dynamicadd")
    browser.click(add_button)

    # Wait for new row to appear (in real scenarios, you might need explicit waits)
    import time
    time.sleep(0.5)

    # Check updated row count
    updated_rows = len(dynamic_table.rows)
    print(f"Rows after adding: {updated_rows}")

    if updated_rows > initial_rows:
        print("✓ Successfully detected dynamic row addition")

        # Access the new row
        new_row = dynamic_table[updated_rows - 1]
        print(f"New row content: {[cell.text for cell in new_row]}")

Drag and Drop Operations
=======================

The testing page includes comprehensive drag & drop examples:

**Basic Drag and Drop**

.. code-block:: python

    class DragDropView(View):
        # Drag source element
        drag_source = Text(id="drag_source")

        # Drop target element
        drop_target = Text(id="drop_target")

        # Additional draggable for offset testing
        drag_source2 = Text(id="drag_source2")

        # Status display elements
        drop_status = Text(id="drop_status")
        drag_log = Text(id="drag_log")

    drag_drop = DragDropView(browser)

    # Verify drag elements are present
    print(f"Drag source displayed: {drag_drop.drag_source.is_displayed}")
    print(f"Drop target displayed: {drag_drop.drop_target.is_displayed}")

    # Perform drag and drop operation
    browser.drag_and_drop(drag_drop.drag_source, drag_drop.drop_target)

    # Check status after drag and drop
    print(f"Drop status: {drag_drop.drop_status.read()}")

**Drag and Drop by Offset**

.. code-block:: python

    # Get initial position of drag source
    initial_location = browser.location_of(drag_drop.drag_source2)
    print(f"Initial location: {initial_location}")

    # Drag by offset (50 pixels right, 30 pixels down)
    browser.drag_and_drop_by_offset(drag_drop.drag_source2, 50, 30)

    # Note: In real scenarios, you might need to verify the position change
    # The testing page logs drag actions for verification

    # Alternative: drag to specific coordinates
    browser.drag_and_drop_to(drag_drop.drag_source2, to_x=200, to_y=150)

**Sortable List Drag and Drop**

.. code-block:: python

    class SortableListView(View):
        # The sortable list container
        sortable_list = Text(id="sortable_list")

        # Individual sortable items
        item1 = Text(locator="[data-sort-id='item-1']")
        item2 = Text(locator="[data-sort-id='item-2']")
        item3 = Text(locator="[data-sort-id='item-3']")

    sortable = SortableListView(browser)

    # Get initial order
    def get_sortable_order():
        """Get current order of sortable items."""
        items = browser.elements("#sortable_list .sortable-item span:last-child")
        return [browser.text(item) for item in items]

    initial_order = get_sortable_order()
    print(f"Initial order: {initial_order}")

    # Drag first item to second position
    browser.drag_and_drop(sortable.item1, sortable.item2)

    # Get updated order
    updated_order = get_sortable_order()
    print(f"Updated order: {updated_order}")

    if initial_order != updated_order:
        print("✓ Successfully reordered sortable list")

Advanced Interaction Patterns
=============================

Handle complex UI interactions beyond basic widgets:

**Alert and Dialog Handling**

.. code-block:: python

    class AlertHandlingView(View):
        alert_button = Text(id="alert_button")
        alert_output = Text(id="alert_out")

    alert_handler = AlertHandlingView(browser)

    # Handle JavaScript alerts/prompts
    def handle_alert_with_response(response_text="TestWidget"):
        """Handle JavaScript prompt dialog."""

        # Set up dialog handler before triggering
        def handle_dialog(dialog):
            print(f"Dialog message: {dialog.message}")
            dialog.accept(response_text)

        browser.page.on("dialog", handle_dialog)

        # Trigger the alert
        browser.click(alert_handler.alert_button)

        # Wait for result to appear
        time.sleep(0.5)

        # Read the result
        result = alert_handler.alert_output.read()
        print(f"Alert result: {result}")

        # Clean up handler
        browser.page.remove_listener("dialog", handle_dialog)

        return result

    # Test alert handling
    alert_result = handle_alert_with_response("CustomWidget")

**Multi-Button Click Handling**

.. code-block:: python

    class ButtonInteractionView(View):
        # Button that changes state when clicked
        state_button = Text(id="a_button")

        # Button that detects different mouse buttons
        multi_button = Text(id="multi_button")
        click_result = Text(id="click_result")

        # Disabled button for state testing
        disabled_button = Text(id="disabled_button")

    button_tests = ButtonInteractionView(browser)

    # Test button state changes
    initial_classes = browser.get_attribute(button_tests.state_button, "class")
    print(f"Initial button classes: {initial_classes}")

    browser.click(button_tests.state_button)

    updated_classes = browser.get_attribute(button_tests.state_button, "class")
    print(f"Updated button classes: {updated_classes}")

    if "clicked" in updated_classes and "clicked" not in initial_classes:
        print("✓ Button state change detected")

    # Test disabled button handling
    if not button_tests.disabled_button.is_enabled:
        print("✓ Correctly detected disabled button")

        try:
            browser.click(button_tests.disabled_button)
            print("⚠ Disabled button was clickable (unexpected)")
        except Exception as e:
            print(f"✓ Disabled button properly blocked: {type(e).__name__}")

**Visibility and Dynamic Content**

.. code-block:: python

    class VisibilityTestView(View):
        # Hidden element that becomes visible
        invisible_element = Text(id="invisible_appear_p")
        show_element_button = Text(id="invisible_appear_button")

        # Mixed visibility container
        random_visibility = Text(id="random_visibility")

    visibility_test = VisibilityTestView(browser)

    # Test initial visibility
    print(f"Initially visible: {visibility_test.invisible_element.is_displayed}")

    # Trigger element to appear (has 3-second delay in testing page)
    browser.click(visibility_test.show_element_button)
    print("Triggered show element button (3s delay)")

    # Wait for element to become visible
    def wait_for_visibility(element, timeout=5):
        """Wait for element to become visible."""
        import time
        start_time = time.time()
        while time.time() - start_time < timeout:
            if element.is_displayed:
                return True
            time.sleep(0.1)
        return False

    if wait_for_visibility(visibility_test.invisible_element):
        print("✓ Element became visible after delay")
        content = visibility_test.invisible_element.read()
        print(f"Element content: {content}")
    else:
        print("⚠ Element did not become visible within timeout")

Edge Cases and Error Handling
=============================

Handle complex scenarios and error conditions:

**Table Edge Cases**

.. code-block:: python

    class EdgeCaseTable(Table):
        """Table designed to test edge cases."""
        ROOT = "#edge_case_test_table"

        column_widgets = {
            4: TextInput()  # Input column
        }

    edge_table = EdgeCaseTable(browser)

    # Handle duplicate headers
    headers = edge_table.headers
    print(f"Headers (may contain duplicates): {headers}")

    # Find duplicate header indexes
    header_counts = {}
    for i, header in enumerate(headers):
        if header in header_counts:
            print(f"⚠ Duplicate header '{header}' at indexes {header_counts[header]} and {i}")
        else:
            header_counts[header] = i

    # Handle rows with duplicate key values
    def find_rows_with_duplicate_keys(table, key_column_index):
        """Find rows that have duplicate values in a key column."""
        key_values = {}
        duplicate_rows = []

        for i, row in enumerate(table):
            if len(row) > key_column_index:
                key_value = row[key_column_index].text
                if key_value in key_values:
                    duplicate_rows.append((i, key_values[key_value]))
                else:
                    key_values[key_value] = i

        return duplicate_rows

    duplicate_keys = find_rows_with_duplicate_keys(edge_table, 1)  # Column 1 is "Key"
    if duplicate_keys:
        print(f"⚠ Found duplicate keys: {duplicate_keys}")

**Robust Widget Interaction**

.. code-block:: python

    def safe_widget_interaction(widget, operation, *args, **kwargs):
        """Safely interact with widgets with comprehensive error handling."""
        try:
            # Check if widget exists and is displayed
            if not widget.is_displayed:
                return {'success': False, 'error': 'Widget not displayed'}

            # Check if widget is enabled for interactive operations
            if hasattr(widget, 'is_enabled') and not widget.is_enabled:
                return {'success': False, 'error': 'Widget not enabled'}

            # Perform the operation
            if operation == 'fill':
                result = widget.fill(*args, **kwargs)
                return {'success': True, 'changed': result, 'value': widget.read()}
            elif operation == 'click':
                widget.click(*args, **kwargs)
                return {'success': True, 'action': 'clicked'}
            elif operation == 'read':
                value = widget.read(*args, **kwargs)
                return {'success': True, 'value': value}
            else:
                return {'success': False, 'error': f'Unknown operation: {operation}'}

        except Exception as e:
            return {'success': False, 'error': f'{type(e).__name__}: {e}'}

    # Test safe interactions
    from widgetastic.widget import TextInput

    test_input = TextInput(id="input")

    # Safe fill operation
    fill_result = safe_widget_interaction(test_input, 'fill', 'test_value')
    print(f"Safe fill result: {fill_result}")

    # Safe read operation
    read_result = safe_widget_interaction(test_input, 'read')
    print(f"Safe read result: {read_result}")

Complete Advanced Automation Example
====================================

Here's a comprehensive example combining multiple advanced widgets:

.. code-block:: python

    class ComprehensiveAdvancedAutomation(View):
        # Tables
        standard_table = StandardTable()
        widget_table = TableWithWidgets()
        complex_table = ComplexTable()

        # Drag and drop
        drag_source = Text(id="drag_source")
        drop_target = Text(id="drop_target")

        # Interactive elements
        alert_button = Text(id="alert_button")
        alert_output = Text(id="alert_out")

        # Dynamic content
        dynamic_table = DynamicTable()
        add_row_button = Text(id="dynamicadd")

    def comprehensive_automation_workflow():
        """Comprehensive workflow using multiple advanced widgets."""
        automation = ComprehensiveAdvancedAutomation(browser)
        results = {}

        # 1. Table operations
        print("=== Table Operations ===")

        # Read standard table data
        standard_data = []
        for row in automation.standard_table:
            standard_data.append([cell.text for cell in row])
        results['standard_table_data'] = standard_data
        print(f"Standard table rows: {len(standard_data)}")

        # Fill widget table
        if len(automation.widget_table) > 0:
            first_row = automation.widget_table[0]
            if len(first_row) > 1 and hasattr(first_row[1], 'widget'):
                fill_result = safe_widget_interaction(
                    first_row[1].widget, 'fill', 'automated_value'
                )
                results['widget_table_fill'] = fill_result

        # 2. Dynamic content
        print("=== Dynamic Content ===")

        initial_dynamic_rows = len(automation.dynamic_table.rows)
        browser.click(automation.add_row_button)
        time.sleep(0.5)  # Wait for dynamic addition

        updated_dynamic_rows = len(automation.dynamic_table.rows)
        results['dynamic_rows_added'] = updated_dynamic_rows - initial_dynamic_rows

        # 3. Drag and drop
        print("=== Drag and Drop ===")

        try:
            browser.drag_and_drop(automation.drag_source, automation.drop_target)
            results['drag_drop'] = {'success': True}
        except Exception as e:
            results['drag_drop'] = {'success': False, 'error': str(e)}

        # 4. Complex table operations
        print("=== Complex Table Analysis ===")

        complex_widgets = []
        for i, row in enumerate(automation.complex_table):
            for j, cell in enumerate(row):
                if hasattr(cell, 'widget') and hasattr(cell.widget, 'read'):
                    widget_value = safe_widget_interaction(cell.widget, 'read')
                    complex_widgets.append({
                        'row': i,
                        'col': j,
                        'value': widget_value
                    })

        results['complex_table_widgets'] = complex_widgets

        print("=== Results Summary ===")
        for key, value in results.items():
            print(f"{key}: {value}")

        return results

    # Execute comprehensive automation
    comprehensive_results = comprehensive_automation_workflow()

Best Practices for Advanced Widgets
===================================

**Table Widget Guidelines**

.. code-block:: python

    # 1. Always define column_widgets for tables with embedded widgets
    class GoodTableDefinition(Table):
        ROOT = "#table-with-inputs"
        column_widgets = {
            2: TextInput(),  # Column 3 has text inputs
            3: Checkbox(),   # Column 4 has checkboxes
        }

    # 2. Handle dynamic tables with proper waiting
    def wait_for_table_rows(table, expected_count, timeout=10):
        """Wait for table to have expected number of rows."""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            current_count = len(table.rows)
            if current_count >= expected_count:
                return True
            time.sleep(0.1)

        return False

    # 3. Batch table operations for efficiency
    def batch_table_operations(table, operations):
        """Perform multiple table operations efficiently."""
        results = []

        for row_index, column_ops in operations.items():
            if row_index < len(table):
                row = table[row_index]
                row_results = {}

                for col_index, operation in column_ops.items():
                    if col_index < len(row):
                        cell = row[col_index]
                        result = safe_widget_interaction(
                            cell.widget if hasattr(cell, 'widget') else cell,
                            **operation
                        )
                        row_results[col_index] = result

                results.append({row_index: row_results})

        return results

**Drag and Drop Best Practices**

.. code-block:: python

    # 1. Verify elements are ready for drag operations
    def verify_drag_ready(source_element, target_element):
        """Verify elements are ready for drag and drop."""
        checks = {
            'source_displayed': source_element.is_displayed,
            'target_displayed': target_element.is_displayed,
            'source_enabled': getattr(source_element, 'is_enabled', True),
        }

        all_ready = all(checks.values())
        return all_ready, checks

    # 2. Handle different drag and drop scenarios
    def smart_drag_and_drop(browser, source, target, method='auto'):
        """Smart drag and drop with fallback methods."""
        ready, checks = verify_drag_ready(source, target)

        if not ready:
            print(f"Drag not ready: {checks}")
            return False

        try:
            if method == 'auto' or method == 'standard':
                browser.drag_and_drop(source, target)
                return True
        except Exception as e:
            print(f"Standard drag failed: {e}")

            if method == 'auto':
                # Fallback to offset-based approach
                try:
                    source_loc = browser.location_of(source)
                    target_loc = browser.location_of(target)
                    offset_x = target_loc[0] - source_loc[0]
                    offset_y = target_loc[1] - source_loc[1]

                    browser.drag_and_drop_by_offset(source, offset_x, offset_y)
                    return True
                except Exception as e2:
                    print(f"Offset drag failed: {e2}")
                    return False

        return False

    # 3. Monitor drag and drop results
    def monitor_drag_result(status_element, timeout=5):
        """Monitor drag and drop operation results."""
        import time
        start_time = time.time()
        initial_status = status_element.read()

        while time.time() - start_time < timeout:
            current_status = status_element.read()
            if current_status != initial_status:
                return current_status
            time.sleep(0.1)

        return initial_status

Final Cleanup
==============

.. code-block:: python

    # Clean up browser resources
    try:
        context.close()
        browser_instance.close()
        playwright.stop()
    except Exception as e:
        print(f"Cleanup error: {e}")

Summary
=======

Advanced widgets in Widgetastic.core provide:

* **Table Widget**: Comprehensive table handling with embedded widgets, complex structures, and dynamic content
* **Drag and Drop**: Full drag and drop support with multiple interaction methods
* **Complex Interactions**: Alert handling, dynamic content, and advanced UI patterns
* **Error Handling**: Robust error handling for complex scenarios
* **Performance**: Efficient batch operations and smart waiting strategies

Key takeaways:
* Use Table widgets for any tabular data with column_widgets for embedded elements
* Handle dynamic content with appropriate waiting strategies
* Implement comprehensive error handling for robust automation
* Use batch operations for efficiency in complex scenarios
* Test edge cases and error conditions in your automation code

This completes the advanced widgets tutorial. You're now ready to handle the most complex UI automation scenarios with Widgetastic.core.
