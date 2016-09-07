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


def test_views_no_subviews(browser):
    class MyView(View):
        w = Widget()

    assert not MyView(browser)._views
