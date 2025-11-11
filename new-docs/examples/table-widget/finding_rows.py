"""Finding Rows by Content

This example demonstrates different methods to search for specific rows.
"""

from widgetastic.widget import Table

table = Table(parent=browser, locator="#with-thead")  # noqa: F821

# Method 1: Keyword-based filtering (Django-style)
print("Finding rows with keyword filters:")
rows = list(table.rows(column_1="qwer"))
print(f"Rows where Column 1 equals 'qwer': {len(rows)}")

rows_containing = list(table.rows(column_2__contains="foo"))
print(f"Rows with 'foo' in Column 2: {len(rows_containing)}")

rows_starting = list(table.rows(column_2__startswith="bar"))
print(f"Rows starting with 'bar' in Column 2: {len(rows_starting)}")

rows_ending = list(table.rows(column_2__endswith="_y"))
print(f"Rows ending with '_y' in Column 2: {len(rows_ending)}")

# Find a single row (returns first match or raises RowNotFound)
row = table.row(column_1="qwer")
print(f"\nSingle row where column_1='qwer': {row.read()}")

# Method 2: Tuple-based filtering
print("\nTuple-based filtering:")
rows = list(table.rows((0, "asdf")))
print(f"Rows where column 0 equals 'asdf': {len(rows)}")

rows = list(table.rows((1, "contains", "bar")))
print(f"Rows where column 1 contains 'bar': {len(rows)}")

# Method 3: Row attribute filtering
print("\nRow attribute filtering:")
rows = list(table.rows(_row__attr=("data-test", "abc-123")))
print(f"Rows with data-test='abc-123': {len(rows)}")
