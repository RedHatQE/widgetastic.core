"""Associative Column Filling

This example demonstrates filling rows using an associative column as a key.
"""

from widgetastic.widget import Table, TextInput

# The edge_case_test_table has a "Status" column with unique values
# Use "Status" column as the associative column
status_table = Table(
    parent=browser,  # noqa: F821
    locator="#edge_case_test_table",
    column_widgets={
        "Input": TextInput(locator="./input"),
    },
    assoc_column="Status",
)

# Read the table - returns a dictionary keyed by Status value
data = status_table.read()
print("Table data (keyed by Status):")
for status, row_data in data.items():
    print(f"  {status}: {row_data}")

# Fill rows by their Status value
print("Filling rows by Status:")
status_table.fill(
    {"Active": {"Input": "new_active_value"}, "Inactive": {"Input": "new_inactive_value"}}
)

# Read back to verify
updated_data = status_table.read()
print(f"After fill - Active row Input: {updated_data['Active']['Input']}")
print(f"After fill - Inactive row Input: {updated_data['Inactive']['Input']}")
