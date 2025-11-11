"""Table with Embedded Widgets

This example demonstrates working with tables that have input fields in cells.
"""

from widgetastic.widget import Table, TextInput

# Create the table with column_widgets
# Tell the table which columns have widgets
widget_table = Table(
    parent=browser,  # noqa: F821
    locator="#withwidgets",
    column_widgets={
        "Column 2": TextInput(locator="./input"),
        "Column 3": TextInput(locator="./input"),
    },
)

# Read the table (widgets are automatically read when present)
data = widget_table.read()
print(f"Table data: {data[0]}")

# Access and fill a widget in a specific cell
first_row = widget_table[0]
column2_cell = first_row["Column 2"]

# Fill the input
column2_cell.widget.fill("new value")
print(f"Value after filling: {column2_cell.widget.read()}")

# The read() method handles this automatically
print(f"Cell value using read(): {column2_cell.read()}")

# Fill multiple rows at once
print("\nFilling multiple rows:")
widget_table.fill([{"Column 2": "value1"}, {"Column 3": "value3"}])
print(f"After batch fill: {widget_table.read()}")
