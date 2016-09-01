# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from widgetastic.core.utils import Version, VersionPick


def test_empty_verpick_fails():
    """VersionPick requires a non-empty dictionary."""
    with pytest.raises(ValueError):
        VersionPick({})


@pytest.fixture(scope='function')
def basic_verpick():
    return VersionPick({
        Version.lowest(): 0,
        '1.0.0': 1,
        '2.0.0': 2,
        '2.0.5': 3,
        Version.latest(): 4,
    })


@pytest.fixture(scope='function')
def descriptor_verpick():
    class MyClass(object):
        class browser(object):  # NOQA
            product_version = None

        verpicked = VersionPick({
            Version.lowest(): 0,
            '1.0.0': 1,
            '2.0.0': 2,
            '2.0.5': 3,
            Version.latest(): 4,
        })

    return MyClass()


def test_picking_works_lowest_version(basic_verpick):
    assert basic_verpick.pick(Version.lowest()) == 0


def test_picking_works_latest_version(basic_verpick):
    assert basic_verpick.pick(Version.latest()) == 4


def test_specific_version(basic_verpick):
    assert basic_verpick.pick('1.0.0') == 1


def test_version_in_between(basic_verpick):
    assert basic_verpick.pick('2.0.2') == 2


def test_unmatched_version_fails():
    with pytest.raises(ValueError):
        VersionPick({'1.0.0': 0}).pick('0.0.0')


def test_descriptor_verpick_basic(descriptor_verpick):
    descriptor_verpick.browser.product_version = '1.0.0'
    assert descriptor_verpick.verpicked == 1
