"""Accessing Cells in Different Ways

This example demonstrates multiple methods to access table cells.
"""

from widgetastic.widget import Table

table = Table(parent=browser, locator="#with-thead")  # noqa: F821
row = table[0]  # Get first row

# Method 1: By index (0-based)
cell = row[0]
print(f"Cell by index [0]: {cell.text}")

# Method 2: By column name (exact match)
cell = row["Column 1"]
print(f"Cell by column name 'Column 1': {cell.text}")

# Method 3: By attributized name (Django-style)
# Column names are automatically converted: "Column 1" -> "column_1"
cell = row.column_1
print(f"Cell by attributized name 'column_1': {cell.text}")

# You can also click on cells
print("Clicking on column_1 cell...")
row.column_1.click()
print("Cell clicked successfully")
