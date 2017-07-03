# -*- coding: utf-8 -*-
import pytest

from widgetastic.utils import nested_getattr


def test_nested_getattr_wrong_type():
    with pytest.raises(TypeError):
        nested_getattr(object(), 654)


def test_nested_getattr_empty():
    with pytest.raises(ValueError):
        nested_getattr(object(), '')


def test_nested_getattr_single_level():
    class Obj(object):
        x = 1

    assert nested_getattr(Obj, 'x') == 1
    assert nested_getattr(Obj, ['x']) == 1


def test_nested_getattr_multi_level():
    class Obj(object):
        class foo(object):  # noqa
            class bar(object):  # noqa
                lol = 'heh'

    assert nested_getattr(Obj, 'foo.bar.lol') == 'heh'
    assert nested_getattr(Obj, ['foo', 'bar', 'lol']) == 'heh'
