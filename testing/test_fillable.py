# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from widgetastic.utils import Fillable


def test_basic_fillable():
    class MyFillable(Fillable):
        def as_fill_value(self):
            return 'foo'

    x = MyFillable()
    assert Fillable.coerce(x) == 'foo'
    assert Fillable.coerce(123) == 123
