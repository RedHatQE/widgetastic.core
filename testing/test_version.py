# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from widgetastic.utils import Version


@pytest.mark.parametrize(
    ('a', 'b'), [
        ('0.0.1', '1.0.0'),
        ('1', '2'),
        ('1.0-beta', '1.0'),
        ('1.0-beta', '1.0-rc'),
    ])
def test_compare_lt(a, b):
    assert Version(a) < b
    assert not Version(a) > b


@pytest.mark.parametrize(
    'a', [
        '0.0.1',
        '1.2.3-beta',
        '3.4.5-rc-beta'
    ])
def test_compare_eq(a):
    assert Version(a) == a


@pytest.mark.parametrize(
    ('a', 'b'), [
        ('1.0.0', '0.0.1'),
        ('2', '1'),
        ('1.0', '1.0-beta'),
        ('1.0-rc', '1.0-beta'),
    ])
def test_compare_gt(a, b):
    assert Version(a) > b
    assert not Version(a) < b
