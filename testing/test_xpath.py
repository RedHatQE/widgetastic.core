# -*- coding: utf-8 -*-
import pytest

from widgetastic.xpath import quote


@pytest.mark.parametrize(
    ('a', 'b'), [
        ('<>', '"<>"'),
        ('&', '"&"'),
        ('"\'', '"&quot;\'"'),
    ])
def test_xpath_quote(a, b):
    assert quote(a) == b
