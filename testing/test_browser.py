import os
import tempfile
import time
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


# ======================== BROWSER & PAGE MANAGEMENT TESTS ========================


def test_browser_property(browser):
    """Test browser property returns self."""
    assert browser.browser is browser


def test_root_browser_property(browser):
    """Test root_browser property returns self."""
    assert browser.root_browser is browser


def test_product_version_implemented(browser):
    """Test product_version is implemented in CustomBrowser."""
    assert browser.product_version == "1.0.0"


def test_base_browser_product_version_not_implemented():
    """Test base Browser class product_version raises NotImplementedError."""
    from widgetastic.browser import Browser

    # Create a mock browser object
    class MockBrowser:
        def __init__(self):
            self.context = self
            self.browser = self
            self.browser_type = self
            self.name = "test"

    base_browser = Browser(MockBrowser())
    with pytest.raises(NotImplementedError, match="You have to implement product_version"):
        _ = base_browser.product_version


@pytest.mark.parametrize(
    "wait_unitle",
    ["domcontentloaded", "load", "networkidle", None],
    ids=["domcontentloaded", "load", "networkidle", "normal"],
)
def test_goto_method(browser, testing_page_url, wait_unitle):
    """Test goto method with different wait_until parameters."""
    browser.goto(testing_page_url, wait_until=wait_unitle)
    assert browser.url == testing_page_url


def test_url_property_setter(browser, testing_page_url):
    """Test url property and setter navigation."""
    browser.url = testing_page_url
    assert browser.url == testing_page_url


def test_title(browser):
    """Test title of current window"""
    assert browser.title == "Widgetastic.Core - Testing Page"


def test_refresh_method(browser):
    """Test refresh method reloads the page."""
    original_title = browser.title
    browser.refresh()
    # After refresh, title should still be the same
    assert browser.title == original_title


def test_close_browser_method(current_and_new_handle):
    """Test browser close method and is_browser_closed property."""
    main_browser, new_browser = current_and_new_handle
    assert not main_browser.is_browser_closed
    assert not new_browser.is_browser_closed
    new_browser.close()
    assert new_browser.is_browser_closed
    assert not main_browser.is_browser_closed


def test_browser_type_property(browser):
    """Test browser_type property returns browser engine name."""
    browser_type = browser.browser_type
    assert browser_type in ["chromium", "firefox", "webkit"]


def test_browser_version_property(browser):
    """Test browser_version property returns major version number."""
    version = browser.browser_version
    assert isinstance(version, int)
    assert version > 0


def test_save_screenshot(browser):
    """Test browser save screenshot method."""
    tmp_dir = tempfile._get_default_tempdir()
    filename = Path(tmp_dir) / f"{datetime.now()}.png"
    assert not filename.exists()
    browser.save_screenshot(filename=filename.as_posix())
    assert filename.exists()


# ======================= ELEMENT DISCOVERY & WAITING TESTS =======================


def test_elements_bad_locator(browser):
    with pytest.raises(LocatorNotImplemented):
        browser.element(1)


def test_elements_string_locator_xpath(browser):
    assert len(browser.elements("//h1")) == 1


def test_elements_string_locator_css(browser):
    assert len(browser.elements("h1")) == 1
    assert len(browser.elements("#wt-core-title")) == 1
    assert len(browser.elements("h1#wt-core-title")) == 1
    assert len(browser.elements("h1#wt-core-title.foo")) == 1
    assert len(browser.elements("h1#wt-core-title.foo.bar")) == 1
    assert len(browser.elements("h1.foo.bar")) == 1
    assert len(browser.elements(".foo.bar")) == 2


def test_elements_dict(browser):
    assert len(browser.elements({"xpath": "//h1"})) == 1


def test_elements_webelement(browser):
    element = browser.element("#wt-core-title")
    assert browser.elements(element)[0] is element


def test_elements_locatable_locator(browser):
    """Test _process_locator with object implementing __locator__."""

    class LocatorProtocol:
        def __locator__(self):
            return "#wt-core-title"

    locator = LocatorProtocol()
    assert len(browser.elements(locator)) == 1

    # Verify _process_locator SmartLocator was returned.
    element = browser._process_locator(locator)
    from widgetastic.locator import SmartLocator

    assert isinstance(element, SmartLocator)


def test_process_locator_invalid_type(browser):
    """Test _process_locator with invalid locator type."""

    class InvalidLocator:
        pass

    with pytest.raises(LocatorNotImplemented):
        browser.element(InvalidLocator())


def test_elements_with_locator_protocol_parent(browser):
    """Test elements method with LocatorProtocol parent."""

    class LocatorParent:
        def __locator__(self):
            return "#random_visibility"

    parent = LocatorParent()
    elements = browser.elements("./p", parent=parent, check_visibility=False)
    assert len(elements) > 0


def test_elements_with_no_locator_protocol_parent(browser):
    """Test elements method when parent has no __locator__."""

    class InvalidParent:
        pass

    invalid_parent = InvalidParent()
    elements = browser.elements("div", parent=invalid_parent, check_visibility=False)

    with pytest.raises(LocatorNotImplemented):
        browser.element(invalid_parent)
    assert isinstance(elements, list)


def test_process_locator_with_locator_returning_element_handle(browser):
    """Test _process_locator with __locator__ returning ElementHandle."""

    class ElementHandleReturningLocator:
        def __locator__(self):
            # Return an ElementHandle
            return browser.element("#wt-core-title").element_handle()

    locator_obj = ElementHandleReturningLocator()
    element = browser.element(locator_obj)
    assert element is not None


def test_elements_with_parent(browser):
    parent = browser.elements("#random_visibility")[0]
    assert len(browser.elements("./p", parent=parent, check_visibility=False)) == 5


def test_elements_with_browser_parent(browser):
    """Test elements method with browser as parent."""
    elements = browser.elements("#wt-core-title", parent=browser)
    assert len(elements) > 0


def test_elements_with_widget_parent(browser):
    """Test elements method with widget as parent."""
    from widgetastic.widget import Widget, View

    class TestView(View):
        pass

    class TestWidget(Widget):
        ROOT = "#random_visibility"

    view = TestView(browser)
    widget = TestWidget(parent=view)

    # Test with widget as parent
    elements = browser.elements("./p", parent=widget, check_visibility=False)
    assert len(elements) > 0


def test_elements_with_force_check_safe_deprecated(browser):
    """Test elements method with deprecated force_check_safe parameter."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        elements = browser.elements("#wt-core-title", force_check_safe=True)
        assert len(elements) > 0
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)


def test_elements_check_visibility(browser):
    assert len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=True)) == 3
    assert len(browser.elements('//div[@id="random_visibility"]/p', check_visibility=False)) == 5


def test_wait_for_element_visible(browser):
    """Test wait_for_element method."""
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


def test_wait_for_element_with_ensure_page_safe(browser):
    """Test wait_for_element with ensure_page_safe parameter."""
    element = browser.wait_for_element("#wt-core-title", ensure_page_safe=True)
    assert element is not None


def test_wait_for_element_with_parent(browser):
    """Test wait_for_element with parent parameter."""
    parent = browser.element("#random_visibility")
    element = browser.wait_for_element("./p", parent=parent, timeout=2)
    assert element is not None


def test_element_only_invisible(browser):
    browser.element("#wt-core-title", check_visibility=False)


def test_element_only_visible(browser):
    browser.element("#invisible", check_visibility=False)


def test_element_visible_after_invisible_and_classes_and_execute_script(browser):
    assert "invisible" in browser.classes(
        '//div[@id="visible_invisible"]/p', check_visibility=False
    )


def test_element_nonexisting(browser):
    with pytest.raises(NoSuchElementException):
        browser.element("#badger", check_visibility=False)


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


# ==================== ELEMENT STATE & PROPERTY QUERIES ====================


def test_is_displayed_element(browser):
    """Test is_displayed returns correct state for existing/ non-existing element."""
    assert browser.is_displayed("#wt-core-title")
    assert not browser.is_displayed("#invisible")
    assert not browser.is_displayed("#nonexistent")


def test_is_enabled_element(browser):
    """Test is_enabled returns correct state for existing/ non-existing element."""
    assert browser.is_enabled("#a_button") is True
    assert browser.is_enabled("#disabled_button") is False
    assert browser.is_enabled("#nonexistent") is False


def test_is_disabled_element(browser):
    """Test is_disabled returns correct state for existing/ non-existing element."""
    assert browser.is_disabled("#a_button") is False
    assert browser.is_disabled("#disabled_button") is True
    assert browser.is_disabled("#nonexistent") is False


def test_is_hidden_element(browser):
    """Test is_hidden returns correct state for existing/ non-existing element."""
    assert browser.is_hidden("#wt-core-title") is False
    assert browser.is_hidden("#hidden_input") is True
    assert browser.is_hidden("#nonexistent") is False


def test_is_editable_element(browser):
    """Test is_editable returns correct state for existing/ non-existing element."""
    assert browser.is_editable("#input") is True
    assert browser.is_editable("#editable_content") is True
    assert browser.is_editable("#textarea_input") is True
    assert browser.is_editable("#nonexistent") is False


def test_is_checked_element(browser):
    """Test is_checked returns correct state for existing/ non-existing checkbox."""
    assert browser.is_checked("#input2") is False
    browser.check("#input2")
    assert browser.is_checked("#input2") is True
    browser.uncheck("#input2")
    assert browser.is_checked("#input2") is False
    assert browser.is_checked("#nonexistent") is False


def test_is_selected_element(browser):
    """Test is_selected for elements."""
    # checkbox
    assert browser.is_selected("#input2") is False
    browser.check("#input2")
    assert browser.is_selected("#input2") is True

    # First radio is checked by default
    assert browser.is_selected("#choice1") is True
    assert browser.is_selected("#choice2") is False

    # Click second radio
    browser.click("#choice2")
    assert browser.is_selected("#choice1") is False
    assert browser.is_selected("#choice2") is True


def test_text_method(browser):
    assert browser.text("#wt-core-title") == "Widgetastic.Core - Testing Page"
    assert browser.text("#invisible") == "This is invisible"


def test_text_method_with_none_content(browser):
    """Test text method handles None text_content."""
    # Create element that might return None for text_content
    browser.execute_script("""
        var el = document.createElement('div');
        el.id = 'empty_text_element';
        document.body.appendChild(el);
    """)
    text = browser.text("#empty_text_element")
    assert text == ""


def test_input_value_method(browser):
    """Test input_value method for various input types."""

    # Test input value for text input
    browser.send_keys("test value", "#input")
    value = browser.input_value("#input")
    assert value == "test value"

    # Test input value for textarea
    browser.send_keys("textarea content", "#textarea_input")
    textarea_value = browser.input_value("#textarea_input")
    assert textarea_value == "textarea content"


def test_input_value_method_with_none_value(browser):
    """Test input_value method handles None input_value."""
    # Create an input that might return None
    browser.execute_script("""
        var el = document.createElement('input');
        el.id = 'no_value_input';
        el.value = null;
        document.body.appendChild(el);
    """)
    value = browser.input_value("#no_value_input")
    assert value == ""


def test_simple_file_input_detection(browser):
    """Test basic file input functionality."""
    import tempfile

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test content")
        temp_file = f.name

    try:
        # This should work with file inputs
        browser.send_keys(temp_file, "#fileinput")

        # Verify file input was handled
        file_input = browser.element("#fileinput")
        assert file_input is not None

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_tag_method(browser):
    assert browser.tag("#wt-core-title") == "h1"
    assert browser.tag("#myoption") == "option"


def test_type_method(browser):
    """Test type method returns element type."""
    assert browser.type("#input") == "text"
    assert browser.type("#input_number") == "number"
    assert browser.type("#fileinput") == "file"
    assert browser.type("#colourinput") == "color"


def test_classes_method(browser):
    assert browser.classes("#wt-core-title") == {"foo", "bar"}
    assert browser.classes("#invisible") == {"foo", "wt-invisible", "bar"}


def test_attributes(browser):
    assert browser.attributes("//h1") == {"class": "foo bar", "id": "wt-core-title"}
    assert browser.attributes("#invisible") == {
        "class": "foo bar wt-invisible",
        "style": "display: none;",
        "id": "invisible",
    }


def test_get_attribute(browser):
    assert browser.get_attribute("id", "//h1") == "wt-core-title"
    assert browser.get_attribute("style", "#invisible") == "display: none;"


def test_get_attribute_value_special_handling(browser):
    """Test get_attribute with 'value' attribute uses input_value for input elements."""
    # Set a value in input
    browser.send_keys("test input value", "#input")

    # Get attribute should use input_value() for value attribute
    value = browser.get_attribute("value", "#input")
    assert value == "test input value"

    # Test with textarea
    browser.send_keys("textarea content", "#textarea_input")
    textarea_value = browser.get_attribute("value", "#textarea_input")
    assert textarea_value == "textarea content"


def test_set_attribute(browser):
    browser.set_attribute("foo", "bar", "//h1")
    assert browser.get_attribute("foo", "//h1") == "bar"
    browser.set_attribute("foo", "bar", "#invisible")
    assert browser.get_attribute("foo", "#invisible") == "bar"


# ================== ELEMENT GEOMETRY & VISUAL PROPERTIES TESTS ==================


def test_size_of_method(browser):
    """Test size_of method."""
    # Exact dimensions
    width, height = browser.size_of("#exact_dimensions")
    assert width == 100
    assert height == 50

    # Invisible element
    size = browser.size_of("#hidden_input")
    assert size.width == 0
    assert size.height == 0


def test_location_of_method(browser):
    """Test location_of method."""
    location = browser.location_of("#exact_dimensions")
    # not fixed location so assert int
    assert isinstance(location.x, (int, float))
    assert isinstance(location.y, (int, float))

    # Invisible element
    location = browser.location_of("#hidden_input")
    assert location.x == 0
    assert location.y == 0


def test_middle_of_method(browser):
    """Test middle_of method returns element center point."""
    middle = browser.middle_of("#exact_dimensions")
    assert isinstance(middle.x, int)
    assert isinstance(middle.y, int)

    # Should be center of 100x50 element
    size = browser.size_of("#exact_dimensions")
    location = browser.location_of("#exact_dimensions")
    expected_x = int(location.x + size.width / 2)
    expected_y = int(location.y + size.height / 2)
    assert middle.x == expected_x
    assert middle.y == expected_y


def test_highlight_method(browser):
    """Test highlight method."""
    # Highlight is visual, we just test it doesn't throw an error
    browser.highlight("#wt-core-title")


# ====================== MOUSE & POINTER INTERACTIONS TESTS ======================


def test_click(browser):
    assert len(browser.classes("#a_button")) == 0
    browser.click("#a_button")
    assert "clicked" in browser.classes("#a_button")


def test_click_with_no_wait_after(browser):
    """Test click method with no_wait_after parameter."""
    browser.click("#a_button", no_wait_after=True)
    assert "clicked" in browser.classes("#a_button")


def test_click_with_ignore_ajax(browser):
    """Test click method with ignore_ajax parameter."""
    browser.click("#a_button", ignore_ajax=True)
    assert "clicked" in browser.classes("#a_button")


def test_click_with_invalid_button(browser):
    """Test click method with invalid button parameter raises ValueError."""
    with pytest.raises(ValueError, match="Invalid button 'invalid'"):
        browser.click("#a_button", button="invalid")


def test_click_ensure_page_safe_coverage(browser, monkeypatch):
    """Test click method ensure_page_safe path."""

    # Mock ensure_page_safe to pass normally first
    ensure_page_safe_called = False
    after_click_safe_timeout_called = False

    def mock_ensure_page_safe():
        nonlocal ensure_page_safe_called
        ensure_page_safe_called = True

    def mock_after_click_safe_timeout(el, locator):
        nonlocal after_click_safe_timeout_called
        after_click_safe_timeout_called = True

    monkeypatch.setattr(browser.plugin, "ensure_page_safe", mock_ensure_page_safe)
    monkeypatch.setattr(browser.plugin, "after_click_safe_timeout", mock_after_click_safe_timeout)

    # Normal click should call ensure_page_safe
    browser.click("#wt-core-title")
    assert ensure_page_safe_called


@pytest.mark.parametrize("button", ["left", "right", "middle"])
def test_mouse_click(browser, button):
    """Test click method with left, right, and middle button parameter."""
    # Test with click method button parameter
    browser.click("#multi_button", button=button)
    result = browser.text("#click_result")
    assert button in result

    # Test with click method without button parameter
    browser.refresh()
    expected_result = None

    if button == "left":
        browser.click("#multi_button")
        expected_result = "left click"
    elif button == "right":
        browser.right_click("#multi_button")
        expected_result = "right click"
    elif button == "middle":
        browser.middle_click("#multi_button")
        expected_result = "middle click"

    assert result == expected_result


def test_double_click_method(browser):
    """Test double_click method."""
    initial_classes = browser.classes("#a_button")
    browser.double_click("#a_button")
    final_classes = browser.classes("#a_button")
    assert "clicked" in final_classes
    assert "clicked" not in initial_classes


def test_double_click_with_ignore_ajax(browser):
    """Test double_click method with ignore_ajax parameter."""
    browser.double_click("#a_button", ignore_ajax=True)
    assert "clicked" in browser.classes("#a_button")


def test_double_click_with_timed_out_error_in_ensure_page_safe(browser, monkeypatch):
    """Test double_click method handles TimedOutError from plugin.ensure_page_safe."""
    from wait_for import TimedOutError

    # Store original ensure_page_safe method
    original_ensure_page_safe = browser.plugin.ensure_page_safe
    call_count = 0

    def mock_ensure_page_safe():
        nonlocal call_count
        call_count += 1
        # Only raise TimedOutError on the second call (inside double_click method)
        if call_count == 2:
            raise TimedOutError("Mocked timeout")
        return original_ensure_page_safe()

    # Track if after_click_safe_timeout was called
    timeout_called = False
    original_timeout_method = browser.plugin.after_click_safe_timeout

    def mock_after_click_safe_timeout(el, locator):
        nonlocal timeout_called
        timeout_called = True
        return original_timeout_method(el, locator)

    monkeypatch.setattr(browser.plugin, "ensure_page_safe", mock_ensure_page_safe)
    monkeypatch.setattr(browser.plugin, "after_click_safe_timeout", mock_after_click_safe_timeout)

    # Double-click should handle the TimedOutError
    browser.double_click("#a_button")

    # Verify the timeout handler was called
    assert timeout_called is True
    assert "clicked" in browser.classes("#a_button")


def test_raw_click(browser):
    initial_classes = browser.classes("#a_button")
    browser.raw_click("#a_button")
    final_classes = browser.classes("#a_button")

    # Should behave exactly like click
    assert "clicked" in final_classes
    assert "clicked" not in initial_classes


def test_perform_click_deprecated(browser):
    """Test perform_click deprecated method issues warning."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        browser.perform_click()
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "perform_click is a no-op in Playwright" in str(w[0].message)


def test_perform_double_click_deprecated(browser):
    """Test perform_double_click deprecated method issues warning."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        browser.perform_double_click()
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "perform_double_click is a no-op in Playwright" in str(w[0].message)


def test_hover_method(browser):
    """Test hover method returns element."""
    element = browser.hover("#wt-core-title")
    assert element is not None
    assert hasattr(element, "hover")


def test_position_reference_and_hover_elements(browser):
    """Test position reference and hover target elements exist and are interactive."""
    # Test position reference element
    assert browser.is_displayed("#position_reference")
    pos_ref_size = browser.size_of("#position_reference")
    assert pos_ref_size.width == 120
    assert pos_ref_size.height == 120

    # Test hover target element
    assert browser.is_displayed("#hover_target")

    # Test hover functionality
    hover_result = browser.hover("#hover_target")
    assert hover_result is not None


def test_move_to_element_with_option(browser):
    """Test move_to_element with option element moves to parent select."""
    element = browser.move_to_element("#myoption")
    assert browser.tag(element) == "option"


def test_move_to_element_with_non_option_element(browser):
    """Test move_to_element with regular (non-option) elements."""
    element = browser.move_to_element("#wt-core-title")
    assert element is not None
    assert browser.tag(element) == "h1"


def test_move_to_element_with_highlight(browser):
    """Test move_to_element with highlight_element parameter."""
    element = browser.move_to_element("#wt-core-title", highlight_element=True)
    assert element is not None


def test_move_to_element_option_select_return(browser):
    """Test move_to_element option select return."""
    # Create a select with an option to trigger the special case
    browser.execute_script("""
        var select = document.createElement('select');
        select.id = 'test_select_for_option';
        var option = document.createElement('option');
        option.id = 'test_option_for_select';
        option.value = 'test';
        option.textContent = 'Test Option';
        select.appendChild(option);
        document.body.appendChild(select);
    """)

    # Test moving to option should return the option element (line 637)
    result = browser.move_to_element("#test_option_for_select")
    assert result is not None

    # Cleanup
    browser.execute_script("""
        var select = document.getElementById('test_select_for_option');
        if (select) select.remove();
    """)


def test_move_by_offset_method(browser):
    """Test move_by_offset method."""
    # Test moving from reference element
    browser.move_by_offset("#position_reference", 20, 30)

    # Test with negative offsets
    browser.move_by_offset("#position_reference", -10, -15)


def test_move_by_offset_invalid_element(browser):
    """Test move_by_offset method with invalid element."""
    from widgetastic.exceptions import WidgetOperationFailed

    # Create a hidden element that won't have bounding box
    browser.execute_script("""
        var el = document.createElement('div');
        el.id = 'no_bounding_box';
        el.style.display = 'none';
        document.body.appendChild(el);
    """)

    with pytest.raises(WidgetOperationFailed):
        browser.move_by_offset("#no_bounding_box", 10, 10)


# ========================= KEYBOARD & FORM INPUT TESTS =========================


def test_send_keys_method(browser):
    browser.send_keys("test!", "#input")
    assert browser.get_attribute("value", "#input") == "test!"
    browser.clear("#input")
    assert browser.get_attribute("value", "#input") == ""


def test_send_keys_with_sensitive_data(browser):
    """Test send_keys method with sensitive parameter masks data in logs."""
    browser.send_keys("sensitive_password", "#input", sensitive=True)
    value = browser.get_attribute("value", "#input")
    assert value == "sensitive_password"


def test_fill_method(browser):
    """Test fill method fills element with text."""
    browser.fill("filled text", "#input")
    value = browser.get_attribute("value", "#input")
    assert value == "filled text"


def test_fill_with_sensitive_data(browser):
    """Test fill method with sensitive parameter."""
    browser.fill("sensitive_data", "#input", sensitive=True)
    value = browser.get_attribute("value", "#input")
    assert value == "sensitive_data"


def test_clear_method(browser):
    """Test clear method clears input field."""
    # First add some text
    browser.send_keys("test text", "#input")
    assert browser.get_attribute("value", "#input") == "test text"

    # Clear the field
    result = browser.clear("#input")
    assert result is True
    assert browser.get_attribute("value", "#input") == ""


def test_clear_method_return_value_false(browser, monkeypatch):
    """Test clear method returns False when clearing fails."""
    browser.send_keys("persistent text", "#input")

    # Mock browser.element to return an element that fails to clear
    original_element = browser.element

    def mock_element_function(*args, **kwargs):
        el = original_element(*args, **kwargs)

        # Create a mock element with failing clear behavior
        class MockElement:
            def __getattr__(self, name):
                return getattr(el, name)

            def clear(self):
                pass  # Don't actually clear

            def input_value(self):
                return "still has text"  # Simulate clear failure

        return MockElement()

    # Only mock when called with "#input"
    def selective_mock_element(*args, **kwargs):
        if args and args[0] == "#input":
            return mock_element_function(*args, **kwargs)
        else:
            return original_element(*args, **kwargs)

    monkeypatch.setattr(browser, "element", selective_mock_element)

    result = browser.clear("#input")
    # Should return False since input_value is not empty
    assert result is False


def test_clear_input_type_number(browser):
    browser.send_keys("3", "#input_number")
    assert browser.get_attribute("value", "#input_number") == "3"
    browser.clear("#input_number")
    assert browser.get_attribute("value", "#input") == ""


def test_send_keys_enter_key_handling(browser):
    """Test send_keys with Enter key skips after_keyboard_input hook."""
    # Clear input first
    browser.clear("#input")

    # Send keys with Enter - this should skip the after_keyboard_input hook
    browser.send_keys("test\nEnter", "#input")

    # Verify text was entered (though behavior may vary with Enter)
    value = browser.get_attribute("value", "#input")
    assert "test" in value


def test_send_keys_with_detached_element_exception(browser, monkeypatch):
    """Test send_keys handles element detachment gracefully."""
    from playwright.sync_api import Error as PlaywrightError

    # Mock after_keyboard_input to raise a detachment error
    def mock_after_keyboard_input(el, text):
        raise PlaywrightError("is not a valid selector")

    monkeypatch.setattr(browser.plugin, "after_keyboard_input", mock_after_keyboard_input)

    # This should handle the exception gracefully (lines 940-953)
    browser.send_keys("test text", "#input")

    # Should complete without raising exception
    value = browser.get_attribute("value", "#input")
    assert value == "test text"


def test_send_keys_with_file_input(browser):
    """Test send_keys method with file input automatically detects file upload."""
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test file content")
        temp_file_path = f.name

    try:
        # Test file input detection and upload
        browser.send_keys(temp_file_path, "#fileinput")
        file_name = temp_file_path.split("/")[-1]
        assert file_name in browser.get_attribute("value", "#fileinput")
    finally:
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def test_send_keys_to_focused_element(browser):
    """Test send_keys_to_focused_element method."""
    # Focus an input element first
    browser.element("#input").focus()

    # Send keys to focused element
    browser.send_keys_to_focused_element("focused text")

    # Verify text was entered
    value = browser.get_attribute("value", "#input")
    assert "focused text" in value


def test_copy_paste_methods(browser):
    """Test copy and paste methods."""
    test_text = "copy paste test"
    browser.send_keys(test_text, "#input")

    browser.copy("#input")
    browser.paste("#input_paste")

    pasted_value = browser.get_attribute("value", "#input_paste")
    assert test_text in pasted_value


# ======================== CHECKBOX & FORM CONTROLS TESTS ========================


def test_check_and_uncheck_methods(browser):
    """Test check() and uncheck() methods."""
    # Initially unchecked
    assert browser.is_checked("#input2") is False

    # Check the element
    browser.check("#input2")
    assert browser.is_checked("#input2") is True

    # Uncheck the element
    browser.uncheck("#input2")
    assert browser.is_checked("#input2") is False


# ========================= DRAG & DROP OPERATIONS =========================


def test_drag_and_drop_basic_functionality(browser):
    """Test basic drag_and_drop method with visual feedback verification."""
    assert browser.is_displayed("#drag_source")
    assert browser.is_displayed("#drop_target")

    # Clear the drag log before test
    browser.execute_script("clearDragLog()")
    # Perform drag and drop
    browser.drag_and_drop("#drag_source", "#drop_target")
    log_content = browser.text("#drag_log")
    assert len(log_content.strip()) > 0

    drop_status = browser.text("#drop_status")
    assert "Dropped!Count: 1" in drop_status

    browser.drag_and_drop("#drag_source", "#drop_target")
    drop_status = browser.text("#drop_status")
    assert "Dropped!Count: 2" in drop_status


def test_drag_and_drop_by_offset_functionality(browser):
    """Test drag_and_drop_by_offset method with offset testing element."""
    assert browser.is_displayed("#drag_source2")

    offset_x, offset_y = 50, 30
    browser.drag_and_drop_by_offset("#drag_source2", offset_x, offset_y)


def test_drag_and_drop_to_coordinates(browser):
    """Test drag_and_drop_to method with absolute coordinates."""
    # Ensure element exists
    assert browser.is_displayed("#drag_source2")

    # both coordinates
    browser.drag_and_drop_to("#drag_source2", to_x=200, to_y=150)

    # only x coordinate
    browser.drag_and_drop_to("#drag_source2", to_x=250)

    # only y coordinate
    browser.drag_and_drop_to("#drag_source2", to_y=200)


def test_drag_and_drop_to_requires_coordinates(browser):
    """Test drag_and_drop_to method raises error when no coordinates provided."""
    with pytest.raises(TypeError, match="You need to pass either to_x or to_y or both"):
        browser.drag_and_drop_to("#drag_source2")


def test_sortable_list_drag_functionality(browser):
    """Test simplified sortable list drag and drop functionality."""
    # Ensure sortable list exists
    sortable_items = browser.elements(".sortable-item")
    assert len(sortable_items) == 3, "Should have 3 sortable items"

    # Get initial order
    initial_order = browser.execute_script("return getSortableOrder();")
    assert initial_order == ["First Item", "Second Item", "Third Item"]
    browser.move_to_element(".//div[@id='sortable_list']")  # Just to focus it.
    # Test drag first item to second position
    time.sleep(0.5)
    browser.drag_and_drop(sortable_items[0], sortable_items[1])
    expected_order = ["Second Item", "First Item", "Third Item"]
    time.sleep(0.5)
    assert browser.execute_script("return getSortableOrder();") == expected_order

    # now drag current second item to third position
    browser.drag_and_drop(sortable_items[1], sortable_items[2])
    time.sleep(0.5)
    expected_order = ["Second Item", "Third Item", "First Item"]
    assert browser.execute_script("return getSortableOrder();") == expected_order

    # Verify drag action was logged
    log_content = browser.text("#drag_log")
    assert "Started sorting:" in log_content or "Moved item" in log_content


# ========================= JAVASCRIPT EXECUTION TESTS =========================


def test_execute_script_basic(browser):
    """Test execute_script method with basic script."""
    result = browser.execute_script("return 'test result';")
    assert result == "test result"


def test_execute_script_with_arguments(browser):
    """Test execute_script method with arguments."""
    result = browser.execute_script("return arguments[0] + arguments[1];", 10, 20)
    assert result == 30


def test_execute_script_with_element_argument(browser):
    """Test execute_script method with element argument."""
    element = browser.element("#wt-core-title")
    result = browser.execute_script("return arguments[0].tagName;", element)
    assert result.lower() == "h1"


def test_execute_script_with_silent_parameter(browser):
    """Test execute_script method with silent parameter."""
    result = browser.execute_script("return 'silent test';", silent=True)
    assert result == "silent test"


def test_execute_script_complex_with_widget(browser):
    """Test execute_script method with widget arguments."""
    from widgetastic.widget import Text, View

    class TestView(View):
        text_widget = Text("#wt-core-title")

    view = TestView(browser)

    # Test with widget argument - should convert to element
    result = browser.execute_script("return arguments[0].textContent;", view.text_widget)
    assert "Widgetastic.Core" in result


# =================== FRAME & WINDOW CONTEXT MANAGEMENT TESTS ===================


def test_switch_to_frame_and_back(browser):
    """Test switching to iframe and back to main frame."""
    # Switch to iframe
    browser.switch_to_frame("iframe[name='some_iframe']")
    assert browser.text("//h3") == "IFrame Widget Testing"

    # Switch back to main frame
    browser.switch_to_main_frame()
    assert browser.text("//h3") == "Form Testing Examples"


def test_get_current_location_method(browser):
    """Test get_current_location method returns current URL."""
    current_location = browser.get_current_location()
    assert isinstance(current_location, str)
    assert "testing_page.html" in current_location


# =================== OVERALL FUNCTIONALITY & BrowserParentWrapper TESTS ===================


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


def test_browser_parent_wrapper_equality(browser):
    """Test BrowserParentWrapper equality method."""
    from widgetastic.browser import BrowserParentWrapper
    from widgetastic.widget import Widget, View

    class TestView(View):
        pass

    class TestWidget(Widget):
        ROOT = "#wt-core-title"

    view = TestView(browser)
    widget1 = TestWidget(parent=view)
    widget2 = TestWidget(parent=view)

    wrapper1 = BrowserParentWrapper(widget1, browser)
    wrapper2 = BrowserParentWrapper(widget1, browser)  # Same widget
    wrapper3 = BrowserParentWrapper(widget2, browser)  # Different widget

    # Test equality
    assert wrapper1 == wrapper2
    assert wrapper1 != wrapper3
    assert wrapper1 != "not a wrapper"


def test_browser_parent_wrapper_repr(browser):
    """Test BrowserParentWrapper __repr__ method."""
    from widgetastic.browser import BrowserParentWrapper
    from widgetastic.widget import Widget, View

    class TestView(View):
        pass

    class TestWidget(Widget):
        ROOT = "#wt-core-title"

    view = TestView(browser)
    widget = TestWidget(parent=view)
    wrapper = BrowserParentWrapper(widget, browser)

    repr_str = repr(wrapper)
    assert "BrowserParentWrapper" in repr_str
    assert "TestWidget" in repr_str


def test_browser_parent_wrapper_method_delegation(browser):
    """Test BrowserParentWrapper delegates methods correctly."""
    from widgetastic.browser import BrowserParentWrapper
    from widgetastic.widget import Widget, View

    class TestView(View):
        pass

    class TestWidget(Widget):
        ROOT = "#random_visibility"

    view = TestView(browser)
    widget = TestWidget(parent=view)
    wrapper = BrowserParentWrapper(widget, browser)

    # Test method delegation - element() should work through the wrapper
    element = wrapper.element("./p")
    assert element is not None

    # Test that elements() method includes parent correctly
    elements = wrapper.elements("./p", check_visibility=False)
    assert len(elements) > 0


# =================== DEFAULT PLUGIN TESTS ===================


def test_default_plugin_logger_property(browser):
    """Test DefaultPlugin.logger property creates logger with plugin name."""
    logger = browser.plugin.logger
    assert logger is not None
    assert hasattr(logger, "debug")
    assert hasattr(logger, "info")


def test_default_plugin_hook_methods(browser):
    """Test DefaultPlugin hook methods execute without error."""
    element = browser.element("#wt-core-title")

    # These methods should not raise errors
    browser.plugin.before_click(element, "#wt-core-title")
    browser.plugin.after_click(element, "#wt-core-title")
    browser.plugin.after_click_safe_timeout(element, "#wt-core-title")
    browser.plugin.before_keyboard_input(element, "test")
    browser.plugin.after_keyboard_input(element, "test")


def test_default_plugin_highlight_element_deprecated(browser):
    """Test DefaultPlugin.highlight_element method issues deprecation warning."""
    import warnings

    element = browser.element("#wt-core-title")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        browser.plugin.highlight_element(element)
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "build-in functionality for highlighting" in str(w[0].message)
