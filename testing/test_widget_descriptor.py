# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from widgetastic.widget import WidgetDescriptor


def test_can_create_descriptor():
    class MyClass(object):
        pass

    desc = WidgetDescriptor(MyClass, 1, 2, foo='bar')
    assert desc.klass is MyClass
    assert desc.args == (1, 2)
    assert desc.kwargs == {'foo': 'bar'}


def test_descriptor_increments():
    class MyClass(object):
        pass

    desc1 = WidgetDescriptor(MyClass)
    desc2 = WidgetDescriptor(MyClass)

    assert desc2._seq_id > desc1._seq_id


def test_descriptor_on_class():
    class MyClass(object):
        def __init__(self, parent):
            self.parent = parent

    class HostClass(object):
        _desc_name_mapping = {}

        def __init__(self):
            self._widget_cache = {}
            self.widget_accessed = None

        def child_widget_accessed(self, widget):
            self.widget_accessed = widget

        desc = WidgetDescriptor(MyClass)

    assert isinstance(HostClass.desc, WidgetDescriptor)
    hc = HostClass()
    obj = hc.desc
    assert isinstance(obj, MyClass)
    assert hc.desc is obj
    assert obj.parent is hc
    assert hc.widget_accessed is hc.desc
    assert hc.desc.parent_descriptor is HostClass.desc
