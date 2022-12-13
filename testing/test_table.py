from cached_property import cached_property

from widgetastic.widget import Table


def test_table_cached_properties():
    for item in Table._CACHED_PROPERTIES:
        attribute = getattr(Table, item)
        assert isinstance(attribute, cached_property)
