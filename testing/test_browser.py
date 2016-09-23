# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest

from widgetastic.exceptions import NoSuchElementException, LocatorNotImplemented


def test_is_displayed(browser):
    assert browser.is_displayed('#hello')


def test_is_displayed_negative(browser):
    assert not browser.is_displayed('#invisible')


def test_elements_bad_locator(browser):
    with pytest.raises(LocatorNotImplemented):
        browser.element(1)


def test_elements_string_locator_xpath(browser):
    assert len(browser.elements('//h1')) == 1


def test_elements_string_locator_css(browser):
    # TODO: Why this doesnt work properly?
    # assert len(browser.elements('h1')) == 1
    assert len(browser.elements('#hello')) == 1
    assert len(browser.elements('h1#hello')) == 1
    assert len(browser.elements('h1#hello.foo')) == 1
    assert len(browser.elements('h1#hello.foo.bar')) == 1
    assert len(browser.elements('h1.foo.bar')) == 1
    assert len(browser.elements('.foo.bar')) == 1


def test_elements_dict(browser):
    assert len(browser.elements({'xpath': '//h1'})) == 1


def test_elements_webelement(browser):
    element = browser.element('#hello')
    assert browser.elements(element)[0] is element


def test_elements_locatable_locator(browser):
    class O(object):
        def __locator__(self):
            return '#hello'

    assert len(browser.elements(O())) == 1


def test_elements_with_parent(browser):
    parent = browser.elements('#random_visibility')[0]
    assert len(browser.elements('./p', parent=parent, check_visibility=False)) == 5


def test_elements_check_visibility(browser):
    assert len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=True)) == 3
    assert len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=False)) == 5


def test_element_only_invisible(browser):
    browser.element('#hello', check_visibility=False)


def test_element_only_visible(browser):
    browser.element('#invisible', check_visibility=False)


def test_element_visible_after_invisible_and_classes_and_execute_script(browser):
    assert 'visible' in browser.classes('//div[@id="visible_invisible"]/p', check_visibility=False)


def test_element_nonexisting(browser):
    with pytest.raises(NoSuchElementException):
        browser.element('#badger', check_visibility=False)


def test_move_to_element_option(browser):
    assert browser.move_to_element('#myoption').tag_name == 'option'


def test_click(browser):
    assert len(browser.classes('#a_button')) == 0
    browser.click('#a_button')
    assert 'clicked' in browser.classes('#a_button')


def test_raw_click(browser):
    assert len(browser.classes('#a_button')) == 0
    browser.raw_click('#a_button')
    assert 'clicked' in browser.classes('#a_button')


def test_tag(browser):
    assert browser.tag('#hello') == 'h1'


def test_text_visible(browser):
    assert browser.text('#hello') == 'Hello'


def test_text_invisible(browser):
    assert browser.text('#invisible') == 'This is invisible'


def test_get_attribute(browser):
    assert browser.get_attribute('id', '//h1') == 'hello'


def test_set_attribute(browser):
    browser.set_attribute('foo', 'bar', '//h1')
    assert browser.get_attribute('foo', '//h1') == 'bar'


def test_simple_input_send_keys_clear(browser):
    browser.send_keys('test!', '#input')
    assert browser.get_attribute('value', '#input') == 'test!'
    browser.clear('#input')
    assert browser.get_attribute('value', '#input') == ''
