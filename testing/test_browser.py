import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from widgetastic.browser import BrowserParentWrapper
from widgetastic.exceptions import LocatorNotImplemented
from widgetastic.exceptions import NoSuchElementException
from widgetastic.widget import Text
from widgetastic.widget import View
from playwright.sync_api import Locator


@pytest.fixture()
def current_and_new_handle(request, window_manager, testing_page_url):
    """Fixture to open a new window and return both browser instances."""
    main_browser = window_manager.current
    new_browser = window_manager.new_browser(url=testing_page_url)

    @request.addfinalizer
    def _close_window():
        if not new_browser.is_browser_closed:
            window_manager.close_browser(new_browser)

    return main_browser, new_browser


@pytest.fixture()
def invoke_alert(browser):
    """fixture to invoke sample alert."""
    alert_btn = browser.element("#alert_button")
    alert_btn.click()
    yield
    if browser.alert_present:
        alert = browser.get_alert()
        alert.dismiss()


def test_is_displayed(browser):
    assert browser.is_displayed("#hello")


def test_is_displayed_negative(browser):
    assert not browser.is_displayed("#invisible")


def test_elements_bad_locator(browser):
    with pytest.raises(LocatorNotImplemented):
        browser.element(1)


def test_elements_string_locator_xpath(browser):
    assert len(browser.elements("//h1")) == 1


def test_elements_string_locator_css(browser):
    # TODO: Why this doesnt work properly?
    # assert len(browser.elements('h1')) == 1
    assert len(browser.elements("#hello")) == 1
    assert len(browser.elements("h1#hello")) == 1
    assert len(browser.elements("h1#hello.foo")) == 1
    assert len(browser.elements("h1#hello.foo.bar")) == 1
    assert len(browser.elements("h1.foo.bar")) == 1
    assert len(browser.elements(".foo.bar")) == 1


def test_elements_dict(browser):
    assert len(browser.elements({"xpath": "//h1"})) == 1


def test_elements_webelement(browser):
    element = browser.element("#hello")
    assert browser.elements(element)[0] is element


def test_elements_locatable_locator(browser):
    class Object:
        def __locator__(self):
            return "#hello"

    assert len(browser.elements(Object())) == 1


def test_elements_with_parent(browser):
    parent = browser.elements("#random_visibility")[0]
    assert len(browser.elements("./p", parent=parent, check_visibility=False)) == 5


def test_elements_check_visibility(browser):
    assert len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=True)) == 3
    assert len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=False)) == 5


def test_wait_for_element_visible(browser):
    # Click on the button
    browser.click("#invisible_appear_button")
    try:
        assert isinstance(browser.wait_for_element("#invisible_appear_p", visible=True), Locator)
    except NoSuchElementException:
        pytest.fail("NoSuchElementException raised when webelement expected")


@pytest.mark.parametrize("exception", [True, False], ids=["with_exception", "without_exception"])
def test_wait_for_element_exception_control(browser, exception):
    # Click on the button, element will not appear
    browser.click("#invisible_appear_button")
    wait_for_args = dict(
        locator="#invisible_appear_p", visible=True, timeout=1.5, exception=exception
    )
    if exception:
        with pytest.raises(NoSuchElementException):
            browser.wait_for_element(**wait_for_args)
    else:
        assert browser.wait_for_element(**wait_for_args) is None


def test_element_only_invisible(browser):
    browser.element("#hello", check_visibility=False)


def test_element_only_visible(browser):
    browser.element("#invisible", check_visibility=False)


def test_element_visible_after_invisible_and_classes_and_execute_script(browser):
    assert "invisible" in browser.classes(
        '//div[@id="visible_invisible"]/p', check_visibility=False
    )


def test_element_nonexisting(browser):
    with pytest.raises(NoSuchElementException):
        browser.element("#badger", check_visibility=False)


def test_move_to_element_option(browser):
    el = browser.move_to_element("#myoption")
    assert browser.tag(el) == "option"


def test_click(browser):
    assert len(browser.classes("#a_button")) == 0
    browser.click("#a_button")
    assert "clicked" in browser.classes("#a_button")


def test_raw_click(browser):
    assert len(browser.classes("#a_button")) == 0
    browser.raw_click("#a_button")
    assert "clicked" in browser.classes("#a_button")


def test_tag(browser):
    assert browser.tag("#hello") == "h1"


def test_text_visible(browser):
    assert browser.text("#hello") == "Hello"


def test_text_invisible(browser):
    assert browser.text("#invisible") == "This is invisible"


def test_attributes(browser):
    assert browser.attributes("//h1") == {"class": "foo bar", "id": "hello"}


def test_get_attribute(browser):
    assert browser.get_attribute("id", "//h1") == "hello"


def test_set_attribute(browser):
    browser.set_attribute("foo", "bar", "//h1")
    assert browser.get_attribute("foo", "//h1") == "bar"


def test_simple_input_send_keys_clear(browser):
    browser.send_keys("test!", "#input")
    assert browser.get_attribute("value", "#input") == "test!"
    browser.clear("#input")
    assert browser.get_attribute("value", "#input") == ""


def test_clear_input_type_number(browser):
    browser.send_keys("3", "#input_number")
    assert browser.get_attribute("value", "#input_number") == "3"
    browser.clear("#input_number")
    assert browser.get_attribute("value", "#input") == ""


def test_copy_paste(browser):
    t = "copy and paste text"
    browser.send_keys(t, "#input")
    assert browser.get_attribute("value", "#input") == t
    browser.copy("#input")
    browser.paste("#input_paste")
    assert browser.get_attribute("value", "#input_paste") == t


def test_nested_views_parent_injection(browser):
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


def test_element_force_visibility_check_by_locator(browser):
    class MyLocator:
        CHECK_VISIBILITY = True  # Always check visibility no matter what

        def __locator__(self):
            return "#invisible"

    loc = MyLocator()
    with pytest.raises(NoSuchElementException):
        browser.element(loc)

    with pytest.raises(NoSuchElementException):
        browser.element(loc, check_visibility=False)

    loc.CHECK_VISIBILITY = False  # Never check visibility no matter what
    browser.element(loc)
    browser.element(loc, check_visibility=True)


def test_size(browser):
    width, height = browser.size_of("#exact_dimensions")
    assert width == 42
    assert height == 69


def test_title(browser):
    """Test title of current window"""
    assert browser.title == "Test page"


def test_current_window_handle(window_manager):
    """Test current window handle property"""
    assert window_manager.current.page


@pytest.mark.parametrize("focus", [False, True], ids=["no_focus", "focus"])
def test_new_window(request, window_manager, focus, testing_page_url):
    """Test open new window with and without focus"""
    main_browser = window_manager.current

    # open new window focus/no-focus
    new_browser = window_manager.new_browser(url=testing_page_url, focus=focus)

    @request.addfinalizer
    def _close_window():
        if not new_browser.is_browser_closed:
            window_manager.close_browser(new_browser)

    assert new_browser.page is not None

    if focus:
        assert window_manager.current is new_browser
    else:
        assert window_manager.current is main_browser


def test_window_handles(window_manager, current_and_new_handle):
    """Test window handles property"""
    main_browser, new_browser = current_and_new_handle
    # Compare the Page objects, not the Browser wrappers
    expected_pages = {main_browser.page, new_browser.page}
    assert len(window_manager.all_pages) == 2
    assert set(window_manager.all_pages) == expected_pages


def test_close_window(window_manager, current_and_new_handle):
    """Test close window"""
    main_browser, new_browser = current_and_new_handle

    assert new_browser.page in window_manager.all_pages
    window_manager.close_browser(new_browser)
    assert new_browser.page not in window_manager.all_pages


def test_switch_to_window(window_manager, current_and_new_handle):
    """Test switch to other window"""
    main_browser, new_browser = current_and_new_handle

    # switch to new window
    window_manager.switch_to(new_browser)
    assert window_manager.current is new_browser
    # switch back to main window
    window_manager.switch_to(main_browser)
    assert window_manager.current is main_browser


#
#
# def test_alert(browser):
#     """Test alert_present, get_alert object"""
#     assert not browser.alert_present
#     alert_btn = browser.element("#alert_button")
#     alert_btn.click()
#     assert browser.alert_present
#
#     alert = browser.get_alert()
#     assert alert.text == "Please enter widget name:"
#     alert.dismiss()
#     assert not browser.alert_present
#
#
# def test_dismiss_any_alerts(browser, invoke_alert):
#     """Test dismiss_any_alerts"""
#     assert browser.alert_present
#     browser.dismiss_any_alerts()
#     assert not browser.alert_present
#
#
# @pytest.mark.parametrize(
#     "cancel_text",
#     [(True, "User dismissed alert."), (False, "User accepted alert:")],
#     ids=["dismiss", "accept"],
# )
# @pytest.mark.parametrize("prompt", [None, "Input"], ids=["without_prompt", "with_prompt"])
# def test_handle_alert(browser, cancel_text, prompt, invoke_alert):
#     """Test handle_alert method with cancel and prompt"""
#     cancel, alert_out_text = cancel_text
#     assert browser.alert_present
#     assert browser.handle_alert(cancel=cancel, prompt=prompt)
#     if not cancel:
#         alert_out_text = alert_out_text + ("Input" if prompt else "TextBox")
#     assert browser.text("#alert_out") == alert_out_text
#     assert not browser.alert_present


def test_save_screenshot(browser):
    """Test browser save screenshot method."""
    tmp_dir = tempfile._get_default_tempdir()
    filename = Path(tmp_dir) / f"{datetime.now()}.png"
    assert not filename.exists()
    browser.save_screenshot(filename=filename.as_posix())
    assert filename.exists()
