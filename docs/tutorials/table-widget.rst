=============
Table Widget
=============

This tutorial demonstrates the Table widget in Widgetastic.core using comprehensive examples from ``testing_page.html``. You'll learn to work with HTML tables, read data from rows and cells, handle embedded widgets, and manage complex table structures with merged cells.

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

.. literalinclude:: ../examples/table-widget/basic_table_reading.py
   :language: python
   :linenos:

**Accessing Cells in Different Ways**

When you have a row, you can access cells in multiple ways:

.. literalinclude:: ../examples/table-widget/accessing_cells.py
   :language: python
   :linenos:

**Finding Rows by Content**

You can search for rows that contain specific values using several methods:

.. literalinclude:: ../examples/table-widget/finding_rows.py
   :language: python
   :linenos:

Table with Embedded Widgets
============================

Some tables have input fields (like text inputs) inside their cells. You need to tell the Table widget which columns contain widgets.

.. literalinclude:: ../examples/table-widget/table_with_widgets.py
   :language: python
   :linenos:


Complex Table with Merged Cells
===============================

Some tables have cells that span multiple rows or columns (rowspan/colspan). Widgetastic handles these automatically.

.. literalinclude:: ../examples/table-widget/complex_table_merged_cells.py
   :language: python
   :linenos:

**What Happens with Merged Cells?**

When a cell spans multiple rows or columns, Widgetastic creates a ``TableReference`` that points to the original cell. This means:
* You can still access all cells normally
* Merged cells are handled transparently
* Widgets in merged cells work just like regular cells

**Associative Column Filling**

When you have a table where one column uniquely identifies each row, you can use ``assoc_column`` to fill rows by their key value:

.. literalinclude:: ../examples/table-widget/associative_column_filling.py
   :language: python
   :linenos:
