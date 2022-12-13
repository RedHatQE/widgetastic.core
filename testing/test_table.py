from cached_property import cached_property

from widgetastic.widget import Table
from widgetastic.widget import View


def test_table_cached_properties():
    """Cached properties are defined as such"""
    for item in Table._CACHED_PROPERTIES:
        attribute = getattr(Table, item)
        assert isinstance(attribute, cached_property)


def test_table_clear_cache(browser):
    class TestForm(View):
        table = Table("#rowcolspan_table")

    view = TestForm(browser)
    table = view.table

    # invoke properties
    for item in Table._CACHED_PROPERTIES:
        getattr(table, item)
    tree = table.table_tree
    assert tree is not None, "If the table has not row or col span it won't have a tree"

    table.clear_cache()

    for item in Table._CACHED_PROPERTIES:
        assert item not in table.__dict__
    assert table._table_tree is None
