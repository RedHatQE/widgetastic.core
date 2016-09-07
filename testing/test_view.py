# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from widgetastic.core.widget import View, Widget


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
