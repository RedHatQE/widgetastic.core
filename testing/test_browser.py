# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from widgetastic.browser import BrowserParentWrapper, WebElement
from widgetastic.exceptions import NoSuchElementException, LocatorNotImplemented
from widgetastic.widget import View, Text


@pytest.fixture()
def current_and_new_handle(request, browser, test_server):
    """fixture return current and newly open window handle"""
    handle = browser.new_window(url=test_server.url)

    @request.addfinalizer
    def _close_window():
        if handle in browser.window_handles:
            browser.close_window(handle)
    return browser.current_window_handle, handle


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
    class Object(object):
        def __locator__(self):
            return '#hello'

    assert len(browser.elements(Object())) == 1


def test_elements_with_parent(browser):
    parent = browser.elements('#random_visibility')[0]
    assert len(browser.elements('./p', parent=parent, check_visibility=False)) == 5


def test_elements_check_visibility(browser):
    assert len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=True)) == 3
    assert len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=False)) == 5


def test_wait_for_element_visible(browser):
    # Click on the button
    browser.click('#invisible_appear_button')
    try:
        assert isinstance(browser.wait_for_element('#invisible_appear_p', visible=True), WebElement)
    except NoSuchElementException:
        pytest.fail('NoSuchElementException raised when webelement expected')


@pytest.mark.parametrize('exception', [True, False], ids=['with_exception', 'without_exception'])
def test_wait_for_element_exception_control(browser, exception):
    # Click on the button, element will not appear
    browser.click('#invisible_appear_button')
    wait_for_args = dict(
        locator='#invisible_appear_p',
        visible=True,
        timeout=1.5,
        exception=exception
    )
    if exception:
        with pytest.raises(NoSuchElementException):
            browser.wait_for_element(**wait_for_args)
    else:
        assert browser.wait_for_element(**wait_for_args) is None


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


def test_nested_views_parent_injection(browser):
    class MyView(View):
        ROOT = '#proper'

        class c1(View):  # noqa
            ROOT = '.c1'

            w = Text('.lookmeup')

        class c2(View):  # noqa
            ROOT = '.c2'

            w = Text('.lookmeup')

        class c3(View):  # noqa
            ROOT = '.c3'

            w = Text('.lookmeup')

        class without(View):  # noqa
            # This one receives the parent browser wrapper
            class nested(View):  # noqa
                # and it should work in multiple levels
                pass

    view = MyView(browser)
    assert isinstance(view.browser, BrowserParentWrapper)
    assert len(view.c1.browser.elements('.lookmeup')) == 1
    assert view.c1.w.text == 'C1'
    assert view.c1.browser.text('.lookmeup') == 'C1'
    assert len(view.c2.browser.elements('.lookmeup')) == 1
    assert view.c2.w.text == 'C2'
    assert view.c2.browser.text('.lookmeup') == 'C2'
    assert len(view.c3.browser.elements('.lookmeup')) == 1
    assert view.c3.w.text == 'C3'
    assert view.c3.browser.text('.lookmeup') == 'C3'

    assert len(view.browser.elements('.lookmeup')) == 3
    assert view.c3.browser.text('.lookmeup') == 'C3'

    assert view.c1.locatable_parent is view
    assert view.c1.w.locatable_parent is view.c1
    assert view.without.nested.locatable_parent is view


def test_element_force_visibility_check_by_locator(browser):
    class MyLocator(object):
        CHECK_VISIBILITY = True  # Always check visibility no matter what

        def __locator__(self):
            return '#invisible'

    loc = MyLocator()
    with pytest.raises(NoSuchElementException):
        browser.element(loc)

    with pytest.raises(NoSuchElementException):
        browser.element(loc, check_visibility=False)

    loc.CHECK_VISIBILITY = False  # Never check visibility no matter what
    browser.element(loc)
    browser.element(loc, check_visibility=True)


def test_size(browser):
    width, height = browser.size_of('#exact_dimensions')
    assert width == 42
    assert height == 69


def test_title(browser):
    """Test title of current window"""
    assert browser.title == "Test page"


def test_current_window_handle(browser):
    """Test current window handle property"""
    assert browser.current_window_handle


@pytest.mark.parametrize("focus", [False, True], ids=["no_focus", "focus"])
def test_new_window(request, browser, focus, test_server):
    """Test open new window with and without focus"""
    # main window handle
    main_handle = browser.current_window_handle

    # open new window focus/no-focus
    handle = browser.new_window(url=test_server.url, focus=focus)

    @request.addfinalizer
    def _close_window():
        browser.close_window(handle)

    assert handle

    if focus:
        assert handle == browser.current_window_handle

        @request.addfinalizer
        def _back_to_main():
            browser.switch_to_window(main_handle)
    else:
        assert handle != browser.current_window_handle


def test_window_handles(browser, current_and_new_handle):
    """Test window handles property"""
    assert len(browser.window_handles) == 2
    assert set(browser.window_handles) == set(current_and_new_handle)


def test_close_window(browser, current_and_new_handle):
    """Test close window"""
    main_handle, new_handle = current_and_new_handle

    assert new_handle in browser.window_handles
    browser.close_window(new_handle)
    assert new_handle not in browser.window_handles


def test_switch_to_window(browser, current_and_new_handle):
    """Test switch to other window"""
    main_handle, new_handle = current_and_new_handle

    # switch to new window
    browser.switch_to_window(new_handle)
    assert new_handle == browser.current_window_handle
    browser.switch_to_window(main_handle)
    assert main_handle == browser.current_window_handle
