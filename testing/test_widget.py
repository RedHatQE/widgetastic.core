# -*- coding: utf-8 -*-
from __future__ import absolute_import
import pytest

from widgetastic.widget import View, Widget, WidgetDescriptor


def test_widget_correctly_collapses_to_descriptor(browser):
    assert isinstance(Widget(), WidgetDescriptor)
    assert isinstance(Widget(browser), Widget)
    assert isinstance(Widget(parent=browser), Widget)


def test_widget_browser(browser):
    w = Widget(browser)
    assert w.browser is browser


def test_widget_broken_browser(browser):
    w = Widget(browser)
    w.parent = object()

    with pytest.raises(ValueError):
        w.browser


def test_widget_with_parent_view(browser):
    class AView(View):
        w = Widget()

    view = AView(browser)
    assert view.w.parent_view is view


def test_widget_without_parent_view(browser):
    w = Widget(browser)

    assert w.parent_view is None


def test_widget_extra_data(browser):
    class AView(View):
        widget = Widget()

    view = AView(browser)
    assert not dir(view.extra)
    browser.extra_objects['testobject'] = 2
    assert dir(view.extra) == ['testobject']
    assert view.extra.testobject == 2


def test_included_widgets(browser):
    class MyWidget(Widget):
        def __init__(self, parent, id, logger=None):
            Widget.__init__(self, parent, logger=logger)
            self.id = id

    class MyClass1(Widget):
        ham = MyWidget('ham')

    class MyClass2(Widget):
        beef = MyWidget('beef')

    class MyClass3(Widget):
        foo = MyWidget('foo')

        included1 = Widget.include(MyClass1)

        bar = MyWidget('bar')

        included2 = Widget.include(MyClass2)

    class MyClass4(Widget):
        alice = MyWidget('alice')

        included1 = Widget.include(MyClass3)

        bob = MyWidget('bob')

    assert MyClass3.cls_widget_names() == ('foo', 'ham', 'bar', 'beef')
    assert MyClass4.cls_widget_names() == ('alice', 'foo', 'ham', 'bar', 'beef', 'bob')

    testw = MyClass4(browser)
    assert isinstance(testw.alice, MyWidget)
    assert testw.alice.id == 'alice'
    assert isinstance(testw.foo, MyWidget)
    assert testw.foo.id == 'foo'
    assert isinstance(testw.ham, MyWidget)
    assert testw.ham.id == 'ham'
    assert isinstance(testw.bar, MyWidget)
    assert testw.bar.id == 'bar'
    assert isinstance(testw.beef, MyWidget)
    assert testw.beef.id == 'beef'
    assert isinstance(testw.bob, MyWidget)
    assert testw.bob.id == 'bob'
