"""Complex Table with Merged Cells

This example demonstrates handling tables with rowspan/colspan cells.
"""

from widgetastic.widget import Table, TextInput

# Create the table with column_widgets
complex_table = Table(
    parent=browser,  # noqa: F821
    locator="#rowcolspan_table",
    column_widgets={
        "Widget": TextInput(locator="./input"),
    },
)

# Get headers
print(f"Headers: {complex_table.headers}")

# Read the table - merged cells are handled automatically
data = complex_table.read()
print(f"\nTable has {len(data)} rows")
print(f"First row: {data[0]}")

# Access and fill a widget in a merged cell
row = complex_table[7]  # Access row 8
widget_cell = row["Widget"]
widget_cell.widget.fill("test value")
print(f"\nWidget value after fill: {widget_cell.widget.read()}")
