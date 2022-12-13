from cached_property import cached_property

from widgetastic.widget import Table
from widgetastic.widget import View


def test_table_cached_properties():
    """Cached properties are defined as such or as properties with deleters"""
    for item in Table._CACHED_PROPERTIES:
        attribute = getattr(Table, item)
        attribute_is_cached_property = isinstance(attribute, cached_property)
        attribute_defines_deleter = (
            isinstance(attribute, property) and getattr(Table, item).fdel is None
        )
        assert attribute_is_cached_property or attribute_defines_deleter


def test_table_clear_cache(browser):
    class TestForm(View):
        table = table1 = Table(
            "#rowcolspan_table",
        )

    view = TestForm(browser)
    table = view.table

    # invoke properties
    for item in Table._CACHED_PROPERTIES:
        cached_item = getattr(table, item)
        if item == "table_tree":
            assert (
                cached_item is not None
            ), "If the table has not row or col span it won't have a tree"

    table.clear_cache()
    for item in Table._CACHED_PROPERTIES:
        if item == "table_tree":
            assert table._table_tree is None
        else:
            assert item not in table.__dict__
