import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from widgetastic.browser import BrowserParentWrapper
from widgetastic.browser import WebElement
from widgetastic.exceptions import LocatorNotImplemented
from widgetastic.exceptions import NoSuchElementException
from widgetastic.widget import Text
from widgetastic.widget import View


@pytest.fixture()
def current_and_new_handle(request, browser, testing_page_url):
    """fixture return current and newly open window handle"""
    if request.config.getoption("--engine") == "selenium":
        handle = browser.new_window(url=testing_page_url)

        @request.addfinalizer
        def _close_window():
            if handle in browser.window_handles:
                browser.close_window(handle)

        return browser.current_window_handle, handle
    else:
        pass


@pytest.fixture()
def invoke_alert(request, browser):
    """fixture to invoke sample alert."""
    if request.config.getoption("--engine") == "selenium":
        alert_btn = browser.element("#alert_button")
        alert_btn.click()
        yield
        if browser.alert_present:
            alert = browser.get_alert()
            alert.dismiss()
    else:
        yield


def test_is_displayed(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.is_displayed("#hello")
    elif engine == "playwright":
        assert browser.is_displayed_play("#hello")


def test_is_displayed_negative(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert not browser.is_displayed("#invisible")
    elif engine == "playwright":
        assert not browser.is_displayed_play("#invisible")


def test_elements_bad_locator(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        with pytest.raises(LocatorNotImplemented):
            browser.element(1)
    elif engine == "playwright":
        # TODO: Needs to be implemented
        pass


def test_elements_string_locator_xpath(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert len(browser.elements("//h1")) == 1
    elif engine == "playwright":
        assert len(browser.elements_play("//h1")) == 1


def test_elements_string_locator_css(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        # TODO: Why this doesnt work properly?
        # assert len(browser.elements('h1')) == 1
        assert len(browser.elements("#hello")) == 1
        assert len(browser.elements("h1#hello")) == 1
        assert len(browser.elements("h1#hello.foo")) == 1
        assert len(browser.elements("h1#hello.foo.bar")) == 1
        assert len(browser.elements("h1.foo.bar")) == 1
        assert len(browser.elements(".foo.bar")) == 1
    elif engine == "playwright":
        assert len(browser.elements_play("#hello")) == 1
        assert len(browser.elements_play("h1#hello")) == 1
        assert len(browser.elements_play("h1#hello.foo")) == 1
        assert len(browser.elements_play("h1#hello.foo.bar")) == 1
        assert len(browser.elements_play("h1.foo.bar")) == 1
        assert len(browser.elements_play(".foo.bar")) == 1


def test_elements_dict(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert len(browser.elements({"xpath": "//h1"})) == 1
    elif engine == "playwright":
        assert len(browser.elements_play({"xpath": "//h1"})) == 1


def test_elements_webelement(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        element = browser.element("#hello")
        assert browser.elements(element)[0] is element
    elif engine == "playwright":
        element = browser.element_play("#hello")
        assert browser.elements_play(element)[0] is element


def test_elements_locatable_locator(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":

        class Object:
            def __locator__(self):
                return "#hello"

        assert len(browser.elements(Object())) == 1
    elif engine == "playwright":
        # TODO: Needs to be implemented
        pass


def test_elements_with_parent(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        parent = browser.elements("#random_visibility")[0]
        assert len(browser.elements("./p", parent=parent, check_visibility=False)) == 5
    elif engine == "playwright":
        parent = browser.elements_play("#random_visibility")[0]
        assert len(browser.elements_play("p", parent=parent, check_visibility=False)) == 5


def test_elements_check_visibility(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=True)) == 3
        assert (
            len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=False)) == 5
        )
    elif engine == "playwright":
        assert (
            len(browser.elements_play('//div[@id="random_visibility"]/p', check_visibility=True))
            == 3
        )
        assert (
            len(browser.elements_play('//div[@id="random_visibility"]/p', check_visibility=False))
            == 5
        )


def test_wait_for_element_visible(request, browser):
    # Click on the button
    from playwright.sync_api import Locator

    engine = request.config.getoption("--engine")
    if engine == "selenium":
        browser.click("#invisible_appear_button")
        try:
            assert isinstance(
                browser.wait_for_element("#invisible_appear_p", visible=True), WebElement
            )
        except NoSuchElementException:
            pytest.fail("NoSuchElementException raised when webelement expected")
    elif engine == "playwright":
        browser.click_play("#invisible_appear_button")
        try:
            assert isinstance(
                browser.wait_for_element_play("#invisible_appear_p", visible=True), Locator
            )
        except Exception:
            pytest.fail("NoSuchElementException raised when webelement expected")


@pytest.mark.parametrize("exception", [True, False], ids=["with_exception", "without_exception"])
def test_wait_for_element_exception_control(request, browser, exception):
    # Click on the button, element will not appear
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        browser.click("#invisible_appear_button")
        wait_for_args = dict(
            locator="#invisible_appear_p", visible=True, timeout=1.5, exception=exception
        )
        if exception:
            with pytest.raises(NoSuchElementException):
                browser.wait_for_element(**wait_for_args)
        else:
            assert browser.wait_for_element(**wait_for_args) is None
    elif engine == "playwright":
        browser.click_play("#invisible_appear_button")
        wait_for_args = dict(
            locator="#invisible_appear_p", visible=True, timeout=500, exception=exception
        )
        if exception:
            with pytest.raises(Exception):
                browser.wait_for_element_play(**wait_for_args)
        else:
            assert browser.wait_for_element_play(**wait_for_args) is None


def test_element_only_invisible(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        browser.element("#hello", check_visibility=False)
    elif engine == "playwright":
        browser.element_play("#hello", check_visibility=False)


def test_element_only_visible(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        browser.element("#invisible", check_visibility=False)
    elif engine == "playwright":
        browser.element_play("#invisible", check_visibility=False)


def test_element_visible_after_invisible_and_classes_and_execute_script(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert "invisible" in browser.classes(
            '//div[@id="visible_invisible"]/p', check_visibility=False
        )
    elif engine == "playwright":
        pass  # Todo:: Needs to be implemented


def test_element_nonexisting(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        with pytest.raises(NoSuchElementException):
            browser.element("#badger", check_visibility=False)
    elif engine == "playwright":
        with pytest.raises(Exception):
            browser.element_play("#badger", check_visibility=False)


def test_move_to_element_option(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.move_to_element("#myoption").tag_name == "option"
    elif engine == "playwright":
        element = browser.move_to_element_play("#myoption")
        element.evaluate("(el) => el.tagName.toLowerCase()") == "option"


def test_click(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert len(browser.classes("#a_button")) == 0
        browser.click("#a_button")
        assert "clicked" in browser.classes("#a_button")
    elif engine == "playwright":
        assert len(browser.classes_play("#a_button")) == 0
        browser.click_play("#a_button")
        assert "clicked" in browser.classes_play("#a_button")


def test_raw_click(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert len(browser.classes("#a_button")) == 0
        browser.raw_click("#a_button")
        assert "clicked" in browser.classes("#a_button")
    elif engine == "playwright":
        pass


def test_tag(browser, request):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.tag("#hello") == "h1"
    elif engine == "playwright":
        assert browser.tag_play("#hello") == "h1"


def test_text_visible(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.text("#hello") == "Hello"
    elif engine == "playwright":
        assert browser.text_play("#hello") == "Hello"


def test_text_invisible(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.text("#invisible") == "This is invisible"
    elif engine == "playwright":
        assert browser.text_play("#invisible") == "This is invisible"


def test_attributes(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.attributes("//h1") == {"class": "foo bar", "id": "hello"}
    elif engine == "playwright":
        assert browser.attributes_play("//h1") == {"class": "foo bar", "id": "hello"}


def test_get_attribute(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.get_attribute("id", "//h1") == "hello"
    elif engine == "playwright":
        assert browser.get_attribute_play("id", "//h1") == "hello"


def test_set_attribute(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        browser.set_attribute("foo", "bar", "//h1")
        assert browser.get_attribute("foo", "//h1") == "bar"
    elif engine == "playwright":
        browser.set_attribute_play(
            "//h1",
            "foo",
            "bar",
        )
        assert browser.get_attribute_play("foo", "//h1") == "bar"


def test_simple_input_send_keys_clear(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        browser.send_keys("test!", "#input")
        assert browser.get_attribute("value", "#input") == "test!"
        browser.clear("#input")
        assert browser.get_attribute("value", "#input") == ""
    elif engine == "playwright":
        browser.send_keys_play("test!", "#input")
        # assert browser.get_attribute_play("value", "#input") == "test!"
        browser.clear_play("#input")
        assert browser.get_attribute_play("value", "#input") == ""


def test_copy_paste(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        t = "copy and paste text"
        browser.send_keys(t, "#input")
        assert browser.get_attribute("value", "#input") == t
        browser.copy("#input")
        browser.paste("#input_paste")
        assert browser.get_attribute("value", "#input_paste") == t
    elif engine == "playwright":
        t = "copy and paste text"
        browser.send_keys_play(t, "#input")
        # assert browser.get_attribute_play("value", "#input") == t
        browser.copy_play("#input")
        # assert browser.get_attribute_play("value", "#input_paste") == t


def test_nested_views_parent_injection(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":

        class MyView(View):
            ROOT = "#proper"

            class c1(View):  # noqa
                ROOT = ".c1"

                w = Text(".lookmeup")

            class c2(View):  # noqa
                ROOT = ".c2"

                w = Text(".lookmeup")

            class c3(View):  # noqa
                ROOT = ".c3"

                w = Text(".lookmeup")

            class without(View):  # noqa
                # This one receives the parent browser wrapper
                class nested(View):  # noqa
                    # and it should work in multiple levels
                    pass

        view = MyView(browser)
        assert isinstance(view.browser, BrowserParentWrapper)
        assert len(view.c1.browser.elements(".lookmeup")) == 1
        assert view.c1.w.text == "C1"
        assert view.c1.browser.text(".lookmeup") == "C1"
        assert len(view.c2.browser.elements(".lookmeup")) == 1
        assert view.c2.w.text == "C2"
        assert view.c2.browser.text(".lookmeup") == "C2"
        assert len(view.c3.browser.elements(".lookmeup")) == 1
        assert view.c3.w.text == "C3"
        assert view.c3.browser.text(".lookmeup") == "C3"

        assert len(view.browser.elements(".lookmeup")) == 3
        assert view.c3.browser.text(".lookmeup") == "C3"

        assert view.c1.locatable_parent is view
        assert view.c1.w.locatable_parent is view.c1
        assert view.without.nested.locatable_parent is view
    elif engine == "playwright":
        pass  # needs implementation


def test_element_force_visibility_check_by_locator(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":

        class MyLocator:
            CHECK_VISIBILITY = True  # Always check visibility no matter what

            def __locator__(self):
                return "#invisible"

        loc = MyLocator()
        with pytest.raises(NoSuchElementException):
            browser.element(loc)


def test_clear_input_type_number(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        browser.send_keys("3", "#input_number")
        assert browser.get_attribute("value", "#input_number") == "3"
        browser.clear("#input_number")
        assert browser.get_attribute("value", "#input") == ""
    elif engine == "playwright":
        browser.send_keys_play("3", "#input_number")
        # assert browser.get_attribute_play("value", "#input_number") == "3" (application issue)
        browser.clear_play("#input_number")
        assert browser.get_attribute_play("value", "#input") == ""


def test_size(request, browser):
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        width, height = browser.size_of("#exact_dimensions")
        assert width == 42
        assert height == 69
    elif engine == "playwright":
        width, height = browser.size_of_play("#exact_dimensions")
        assert width == 42
        assert height == 69


def test_title(request, browser):
    """Test title of current window"""
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.title == "Test page"
    elif engine == "playwright":
        assert browser.title_play == "Test page"


def test_current_window_handle(request, browser):
    """Test current window handle property"""
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.current_window_handle
    elif engine == "playwright":
        pass  # needs implementation


@pytest.mark.parametrize("focus", [False, True], ids=["no_focus", "focus"])
def test_new_window(request, browser, focus, testing_page_url):
    """Test open new window with and without focus"""
    # main window handle
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        main_handle = browser.current_window_handle

        # open new window focus/no-focus
        handle = browser.new_window(url=testing_page_url, focus=focus)

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
    elif engine == "playwright":
        pass  # needs implementation


def test_window_handles(request, browser, current_and_new_handle):
    """Test window handles property"""
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert len(browser.window_handles) == 2
        assert set(browser.window_handles) == set(current_and_new_handle)
    elif engine == "playwright":
        pass  # needs implementation


def test_close_window(request, browser, current_and_new_handle):
    """Test close window"""
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        main_handle, new_handle = current_and_new_handle

        assert new_handle in browser.window_handles
        browser.close_window(new_handle)
        assert new_handle not in browser.window_handles
    elif engine == "playwright":
        pass  # needs implementation


def test_switch_to_window(request, browser, current_and_new_handle):
    """Test switch to other window"""
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        main_handle, new_handle = current_and_new_handle

        # switch to new window
        browser.switch_to_window(new_handle)
        assert new_handle == browser.current_window_handle
        browser.switch_to_window(main_handle)
        assert main_handle == browser.current_window_handle
    elif engine == "playwright":
        pass  # needs implementation


def test_alert(request, browser):
    """Test alert_present, get_alert object"""
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert not browser.alert_present
        alert_btn = browser.element("#alert_button")
        alert_btn.click()
        assert browser.alert_present

        alert = browser.get_alert()
        assert alert.text == "Please enter widget name:"
        alert.dismiss()
        assert not browser.alert_present
    elif engine == "playwright":
        pass  # needs implementation


def test_dismiss_any_alerts(request, browser, invoke_alert):
    """Test dismiss_any_alerts"""
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        assert browser.alert_present
        browser.dismiss_any_alerts()
        assert not browser.alert_present
    elif engine == "playwright":
        pass  # needs implementation


@pytest.mark.parametrize(
    "cancel_text",
    [(True, "User dismissed alert."), (False, "User accepted alert:")],
    ids=["dismiss", "accept"],
)
@pytest.mark.parametrize("prompt", [None, "Input"], ids=["without_prompt", "with_prompt"])
def test_handle_alert(request, browser, cancel_text, prompt, invoke_alert):
    """Test handle_alert method with cancel and prompt"""
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        cancel, alert_out_text = cancel_text
        assert browser.alert_present
        assert browser.handle_alert(cancel=cancel, prompt=prompt)
        if not cancel:
            alert_out_text = alert_out_text + ("Input" if prompt else "TextBox")
        assert browser.text("#alert_out") == alert_out_text
        assert not browser.alert_present
    elif engine == "playwright":
        pass  # needs implementation


def test_save_screenshot(request, browser):
    """Test browser save screenshot method."""
    engine = request.config.getoption("--engine")
    if engine == "selenium":
        tmp_dir = tempfile._get_default_tempdir()
        filename = Path(tmp_dir) / f"{datetime.now()}.png"
        assert not filename.exists()
        browser.save_screenshot(filename=filename.as_posix())
        assert filename.exists()
    elif engine == "playwright":
        tmp_dir = tempfile._get_default_tempdir()
        filename = Path(tmp_dir) / f"{datetime.now()}.png"
        assert not filename.exists()
        browser.save_screenshot_play(filename=filename.as_posix())
        assert filename.exists()
