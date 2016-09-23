# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from widgetastic.widget import View, Widget, do_not_read_this_widget


def test_can_create_view(browser):
    class MyView(View):
        pass

    MyView(browser)


def test_view_browser(browser):
    class MyView(View):
        pass

    view = MyView(browser)
    assert view.browser is browser


def test_view_root_locator(browser):
    class MyView(View):
        ROOT = '#foo'

    view = MyView(browser)
    assert view.__locator__() == ('css selector', '#foo')


def test_view_widget_names():
    class MyView(View):
        w1 = Widget()
        w2 = Widget()

    assert MyView.widget_names() == ['w1', 'w2']


def test_view_no_subviews(browser):
    class MyView(View):
        w = Widget()

    assert not MyView(browser)._views


def test_view_with_subviews(browser):
    class MyView(View):
        w = Widget()

        class AnotherView(View):
            another_widget = Widget()

        class Foo(View):
            bar = Widget()

    view = MyView(browser)
    assert {type(v).__name__ for v in view._views} == {'AnotherView', 'Foo'}
    assert isinstance(view.w, Widget)
    assert isinstance(view.AnotherView, View)
    assert isinstance(view.Foo, View)
    assert isinstance(view.AnotherView.another_widget, Widget)
    assert isinstance(view.Foo.bar, Widget)


def test_view_is_displayed_without_root_locator(browser):
    class MyView(View):
        pass

    assert MyView(browser).is_displayed


def test_view_is_displayed_with_root_locator(browser):
    class MyView(View):
        ROOT = '#hello'

    assert MyView(browser).is_displayed


def test_view_is_not_displayed_with_root_locator(browser):
    class MyView(View):
        ROOT = '#thisdoesnotexist'

    view = MyView(browser)
    assert not view.is_displayed


def test_inherited_view(browser):
    class AView1(View):
        widget1 = Widget()

    class AView2(AView1):
        widget2 = Widget()

    view = AView2(browser)
    assert view.widget1.parent_view is view


def test_do_not_read_widget(browser):
    class AWidget1(Widget):
        def read(self):
            return 1

    class AWidget2(Widget):
        def read(self):
            do_not_read_this_widget()

    class AView(View):
        w1 = AWidget1()
        w2 = AWidget2()

    view = AView(browser)
    data = view.read()
    assert 'w2' not in data
