from cached_property import cached_property

from widgetastic.widget import Table


def test_table_cached_properties():
    for item in Table._CACHED_PROPERTIES:
        attribute = getattr(Table, item)
        attribute_is_cached_property = isinstance(attribute, cached_property)
        attribute_defines_deleter = (
            isinstance(attribute, property) and getattr(Table, item).fdel is None
        )
        assert attribute_is_cached_property or attribute_defines_deleter
