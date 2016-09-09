# -*- coding: utf-8 -*-
from __future__ import absolute_import
import pytest

from widgetastic.widget import View, Widget, WidgetDescriptor


def test_widget_correctly_collapses_to_descriptor(browser):
    assert isinstance(Widget(), WidgetDescriptor)
    assert isinstance(Widget(browser), Widget)


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
