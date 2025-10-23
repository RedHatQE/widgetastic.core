=============
Table Widget
=============

This tutorial demonstrates advanced widgets in Widgetastic.core using comprehensive examples from ``testing_page.html``. You'll learn to work with tables, handle drag & drop operations, and interact with complex UI components.

.. note::
   **Prerequisites**: Basic widgets tutorial
   **Test Pages Used**: ``testing/html/testing_page.html``


Table Widget Fundamentals
=========================

The :py:class:`~widgetastic.widget.Table` widget lets you work with HTML tables easily. Think of it as a way to read and interact with table data on web pages.

**What is a Table Widget?**

A table widget represents an HTML ``<table>`` element. It helps you:
* Read data from table rows and cells
* Fill in form inputs that are inside table cells
* Find specific rows based on their content
* Handle complex tables with merged cells

Let's learn with three simple examples from the testing page.

Basic Table - Reading Data
==========================

The simplest use case: reading data from a standard table with headers.

.. code-block:: python

    from widgetastic.widget import Table


    # Initialize the table widget.    
    table = Table(parent=browser, locator="#with-thead")

    # Get table information
    print(f"Headers: {table.headers}")
    # Output: (None, 'Column 1', 'Column 2', 'Column 3', 'Column 4')

    print(f"Number of rows: {len(list(table))}")
    # Output: 3

    # Read all rows
    # Note: When iterating over a row, you get (header, cell) tuples
    for row in table:
        print([cell.text for header, cell in row])
    # Output:
    # ['asdf', 'qwer', 'yxcv', 'uiop', '']
    # ['foo_x', 'bar_x', 'baz_x', 'bat_x', '']
    # ['foo_y', 'bar_y', 'baz_y', 'bat_y', '']
    
    # Access a specific row (first row is index 0)
    first_row = table[0]
    print(f"First row: {first_row.read()}")
    # Output: {0: 'asdf', 'Column 1': 'qwer', 'Column 2': 'yxcv', 'Column 3': 'uiop', 'Column 4': ''}

    # Access a specific cell (row 0, column 0)
    cell = table[0][0]
    print(f"First cell: {cell.text}")
    # Output: asdf

    # Read the entire table as a list of dictionaries
    all_data = table.read()
    from pprint import pprint
    pprint(all_data)
    # Output: [{0: 'asdf', 'Column 1': 'qwer', ...}, {...}, {...}]

**Accessing Cells in Different Ways**

When you have a row, you can access cells in multiple ways:

.. code-block:: python

    row = table[0]  # Get first row

    # Method 1: By index (0-based)
    cell = row[0]
    print(cell.text)  # Output: asdf

    # Method 2: By column name (exact match)
    cell = row["Column 1"]
    print(cell.text)  # Output: qwer

    # Method 3: By attributized name (Django-style)
    # Column names are automatically converted: "Column 1" -> "column_1"
    cell = row.column_1
    print(cell.text)  # Output: qwer

    # You can also click on cells
    row.column_1.click()

**Finding Rows by Content**

You can search for rows that contain specific values using several methods:

**1. Keyword-based filtering (Django-style)**

Column names are automatically "attributized" - spaces become underscores, special chars removed:

.. code-block:: python

    # Find all rows where "Column 1" contains "qwer"
    rows = list(table.rows(column_1="qwer"))
    print(f"Found {len(rows)} row(s)")

    # Django-style filtering methods
    rows_containing_bar = list(table.rows(column_2__contains="foo"))
    print(f"Rows with 'bar' in Column 2: {len(rows_containing_bar)}")

    rows_starting_with_bar = list(table.rows(column_2__startswith="bar"))
    print(f"Rows starting with 'bar' in Column 2: {len(rows_starting_with_bar)}")

    rows_ending_with_y = list(table.rows(column_2__endswith="_y"))
    print(f"Rows ending with 'y' in Column 2: {len(rows_ending_with_y)}")

    # Find a single row (returns first match or raises RowNotFound)
    row = table.row(column_1="qwer")
    print(row.read())

    # Combine multiple filters
    filtered = list(table.rows(column_1__contains="foo", column_2__contains="bar"))

**2. Tuple-based filtering**

You can filter by column index and value:

.. code-block:: python

    # Find rows where first column (index 0) equals "asdf"
    rows = list(table.rows((0, "asdf")))
    print(f"Found {len(rows)} row(s)")

    # Find rows where second column (index 1) contains "bar"
    rows = list(table.rows((1, "contains", "bar")))
    print(f"Found {len(rows)} row(s)")

    # Combine tuple filters with keyword filters
    rows = list(table.rows((0, "foo_x"), column_2__contains="baz"))
    print(f"Found {len(rows)} row(s)")

**3. Row attribute filtering**

Filter rows based on HTML attributes on the ``<tr>`` element:

.. code-block:: python

    # The #with-thead table has data-test attributes on rows
    # Find rows with data-test="abc-123"
    rows = list(table.rows(_row__attr=("data-test", "abc-123")))
    print(f"Found {len(rows)} row(s)")

    # Other attribute filters
    rows_startswith = list(table.rows(_row__attr_startswith=("data-test", "abc")))
    rows_endswith = list(table.rows(_row__attr_endswith=("data-test", "123")))
    rows_contains = list(table.rows(_row__attr_contains=("data-test", "abc")))

    # Example with edge_case_test_table that has data-category
    edge_table = Table(parent=browser, locator="#edge_case_test_table")
    active_rows = list(edge_table.rows(_row__attr=("data-category", "active")))
    print(f"Active rows: {len(active_rows)}")

Table with Embedded Widgets
============================

Some tables have input fields (like text inputs) inside their cells. You need to tell the Table widget which columns contain widgets.

.. code-block:: python

    from widgetastic.widget import Table
    from widgetastic.widget.input import TextInput

    # Create the table with column_widgets
    # Tell the table which columns have widgets
    # You can use column index or column name
    widget_table = Table(
        parent=browser,
        locator="#withwidgets",
        column_widgets={
            "Column 2": TextInput(locator="./input"),  # By column name
            "Column 3": TextInput(locator="./input"),  # By column name
            # Or by index:
            # 1: TextInput(locator="./input"),
            # 2: TextInput(locator="./input"),
        }
    )

    # Read the table (widgets are automatically read when present)
    data = widget_table.read()
    print(data)
    # Output: [{0: 'foo', 'Column 2': '', 'Column 3': 'foo col 3'}, ...]

    # Access and fill a widget in a specific cell
    first_row = widget_table[0]
    column2_cell = first_row["Column 2"]  # Access by column name


    # Fill the input
    column2_cell.widget.fill("new value")
    print(f"Value after filling: {column2_cell.widget.read()}")
    # Output: new value
    

    # The read() method handles this automatically - it reads widget if present, text otherwise
    print(f"Cell value: {column2_cell.read()}")
    # Output: new value

    # Fill multiple rows at once
    widget_table.fill([{"Column 2": "value1"}, {"Column 3": "value3"}])

    # You can also fill a single row
    first_row = widget_table[0]
    first_row.fill({"Column 2": "new_value"})


Complex Table with Merged Cells
===============================

Some tables have cells that span multiple rows or columns (rowspan/colspan). Widgetastic handles these automatically.

.. code-block:: python

    from widgetastic.widget import Table
    from widgetastic.widget.input import TextInput
    from pprint import pprint

    # Create the table with column_widgets
    # The "Widget" column contains text inputs
    complex_table = Table(
        parent=browser,
        locator="#rowcolspan_table",
        column_widgets={
            "Widget": TextInput(locator="./input"),
        }
    )

    # Get headers
    print(f"Headers: {complex_table.headers}")
    # Output: ('#', 'First Name', 'Last Name', 'Username', 'Widget')

    # Read the table - merged cells are handled automatically
    data = complex_table.read()
    pprint(data)

    # Access and fill a widget in a merged cell
    row = complex_table[7]  # Access row 8
    widget_cell = row["Widget"]  # Access by column name
    widget_cell.widget.fill("test value")
    print(f"Widget value: {widget_cell.widget.read()}")
    # Output: test value

**What Happens with Merged Cells?**

When a cell spans multiple rows or columns, Widgetastic creates a ``TableReference`` that points to the original cell. This means:
* You can still access all cells normally
* Merged cells are handled transparently
* Widgets in merged cells work just like regular cells

**Associative Column Filling**

When you have a table where one column uniquely identifies each row, you can use ``assoc_column`` to fill rows by their key value:

.. code-block:: python

    from widgetastic.widget import Table
    from widgetastic.widget.input import TextInput
    from pprint import pprint

    # The edge_case_test_table has a "Status" column with unique values
    # Use "Status" column as the associative column
    status_table = Table(
        parent=browser,
        locator="#edge_case_test_table",
        column_widgets={
            "Input": TextInput(locator="./input"),
        },
        assoc_column="Status"
    )

    # Read the table - returns a dictionary keyed by Status value
    data = status_table.read()
    pprint(data)
    # Output: {'Active': {0: 1, 'Key': 'duplicate', ...}, 'Inactive': {...}, ...}

    # Fill rows by their Status value
    # This finds the row with Status="Active" and fills its Input column
    status_table.fill({
        "Active": {"Input": "new_active_value"},
        "Inactive": {"Input": "new_inactive_value"}
    })

