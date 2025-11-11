"""Basic Table - Reading Data

This example demonstrates reading data from a standard table with headers.
"""

from widgetastic.widget import Table

# Initialize the table widget
table = Table(parent=browser, locator="#with-thead")  # noqa: F821

# Get table information
print(f"Headers: {table.headers}")
print(f"Number of rows: {len(list(table))}")

# Read all rows
print("\nAll rows:")
for row in table:
    print([cell.text for header, cell in row])

# Access a specific row (first row is index 0)
first_row = table[0]
print(f"\nFirst row data: {first_row.read()}")

# Access a specific cell (row 0, column 0)
cell = table[0][0]
print(f"First cell text: {cell.text}")

# Read the entire table as a list of dictionaries
all_data = table.read()
print(f"\nTable has {len(all_data)} rows")
print(f"First row from read(): {all_data[0]}")
