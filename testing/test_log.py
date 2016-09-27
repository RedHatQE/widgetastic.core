# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from widgetastic.log import call_unlogged
from widgetastic.widget import View, Text


def test_override(browser):
    class MyText(Text):
        def read(self):
            return call_unlogged(super(MyText, self).read)

    class TestForm(View):
        h3 = MyText('.//h3')

    form = TestForm(browser)
    form.h3.read()


def test_normal_method():
    class MyClass(object):
        def method(self):
            return True

    class AnotherClass(MyClass):
        def method(self):
            return call_unlogged(super(AnotherClass, self).method)

    assert AnotherClass().method()
