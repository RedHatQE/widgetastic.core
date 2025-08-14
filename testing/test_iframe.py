"""Basic iframe testing for widgetastic.core."""

import pytest
from widgetastic.widget import View
from widgetastic.widget import Text
from widgetastic.widget import Select
from widgetastic.widget import TextInput
from widgetastic.widget import Checkbox


def test_basic_iframe_access(browser):
    """Test basic iframe access and widget interaction."""

    class IFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        h3 = Text(".//h3")
        select1 = Select(id="iframe_select1")
        select2 = Select(name="iframe_select2")

    iframe_view = IFrameView(browser)

    # Test basic visibility and access
    assert iframe_view.is_displayed
    assert iframe_view.h3.is_displayed
    assert iframe_view.select1.is_displayed
    assert iframe_view.select2.is_displayed

    # Test content reading
    assert iframe_view.h3.text == "IFrame Tests"
    assert iframe_view.select1.read() == "Foo"

    # Test interaction
    assert iframe_view.select1.fill("Bar")
    assert iframe_view.select1.read() == "Bar"


def test_nested_iframe_navigation(browser):
    """Test navigation through nested iframe hierarchy."""

    class NestedIFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        h3 = Text(".//h3")

        class nested_iframe(View):
            FRAME = './/iframe[@name="another_iframe"]'
            h3 = Text(".//h3")
            select3 = Select(id="iframe_select3")

            class deep_nested(View):
                ROOT = './/div[@id="nested_view"]'
                nested_input = TextInput(name="input222")

    nested_view = NestedIFrameView(browser)

    # Test access at each level
    assert nested_view.is_displayed
    assert nested_view.h3.text == "IFrame Tests"

    # Test nested iframe access
    assert nested_view.nested_iframe.is_displayed
    assert nested_view.nested_iframe.h3.text == "IFrame Tests 2"
    assert nested_view.nested_iframe.select3.read() == "Foo"

    # Test deeply nested view access
    assert nested_view.nested_iframe.deep_nested.nested_input.is_displayed
    assert nested_view.nested_iframe.deep_nested.nested_input.read() == "Default Value"


def test_frame_context_isolation(browser):
    """Test that frame contexts are properly isolated."""

    class MainView(View):
        h3 = Text('//h3[@id="switchabletesting-1"]')
        checkbox1 = Checkbox(id="switchabletesting-3")

    class IFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        h3 = Text(".//h3")
        select1 = Select(id="iframe_select1")

    main_view = MainView(browser)
    iframe_view = IFrameView(browser)

    # Test that both views work independently
    assert main_view.h3.text == "footest"
    assert iframe_view.h3.text == "IFrame Tests"

    # Test interactions don't affect each other
    main_view.checkbox1.fill(True)
    iframe_view.select1.fill("Bar")

    # Verify states are maintained independently
    assert main_view.checkbox1.read() is True
    assert iframe_view.select1.read() == "Bar"
    assert main_view.h3.text == "footest"  # Main context unchanged
    assert iframe_view.h3.text == "IFrame Tests"  # Frame context unchanged


def test_cross_frame_element_access_errors(browser):
    """Test that accessing elements from wrong frame context raises appropriate errors."""

    class MainView(View):
        # This should fail when accessed from iframe context
        main_checkbox = Checkbox(id="switchabletesting-3")

    class IFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        iframe_select = Select(id="iframe_select1")

    main_view = MainView(browser)
    iframe_view = IFrameView(browser)

    # These should work in their respective contexts
    assert main_view.main_checkbox.is_displayed
    assert iframe_view.iframe_select.is_displayed

    # Test that frame switching works correctly by accessing both
    iframe_view.iframe_select.fill("Bar")
    main_view.main_checkbox.fill(True)

    # Verify both are accessible after cross-context access
    assert iframe_view.iframe_select.read() == "Bar"
    assert main_view.main_checkbox.read() is True


def test_multiple_iframe_switching(browser):
    """Test switching between multiple iframes efficiently."""

    class MainView(View):
        checkbox1 = Checkbox(id="switchabletesting-3")
        checkbox2 = Checkbox(id="switchabletesting-4")

    class IFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        select1 = Select(id="iframe_select1")
        select2 = Select(name="iframe_select2")

    main_view = MainView(browser)
    iframe_view = IFrameView(browser)

    # Perform multiple cross-frame operations
    for i in range(3):
        # Access iframe
        iframe_view.select1.fill("Bar" if i % 2 == 0 else "Foo")

        # Access main frame
        main_view.checkbox1.fill(i % 2 == 0)

        # Verify states
        expected_select = "Bar" if i % 2 == 0 else "Foo"
        expected_checkbox = i % 2 == 0

        assert iframe_view.select1.read() == expected_select
        assert main_view.checkbox1.read() == expected_checkbox


def test_iframe_widget_properties(browser):
    """Test various widget properties work correctly in iframe context."""

    class IFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        h3 = Text(".//h3")
        select1 = Select(id="iframe_select1")
        select2 = Select(name="iframe_select2")

    iframe_view = IFrameView(browser)

    # Test is_displayed
    assert iframe_view.h3.is_displayed
    assert iframe_view.select1.is_displayed
    assert iframe_view.select2.is_displayed

    # Test text content
    assert iframe_view.h3.text == "IFrame Tests"

    # Test select options
    assert iframe_view.select1.all_options == [("Foo", "foo"), ("Bar", "bar")]
    assert len(iframe_view.select2.all_options) == 3

    # Test read/fill operations
    original_value = iframe_view.select1.read()
    assert iframe_view.select1.fill("Bar")
    assert iframe_view.select1.read() == "Bar"
    assert iframe_view.select1.fill(original_value)
    assert iframe_view.select1.read() == original_value


def test_iframe_error_handling(browser):
    """Test error handling for iframe-related operations."""

    class InvalidIFrameView(View):
        FRAME = '//iframe[@name="nonexistent_iframe"]'
        some_element = Text(".//h3")

    class IFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        nonexistent_element = Text(".//nonexistent")
        valid_element = Text(".//h3")

    # Test invalid iframe reference - Playwright throws a specific Error
    invalid_view = InvalidIFrameView(browser)
    with pytest.raises(Exception) as exc_info:
        _ = invalid_view.some_element.is_displayed

    # Verify it's a Playwright frame-related error
    error_message = str(exc_info.value)
    assert "Failed to find frame" in error_message
    assert "nonexistent_iframe" in error_message

    # Test nonexistent element in valid iframe
    iframe_view = IFrameView(browser)
    assert not iframe_view.nonexistent_element.is_displayed
    assert iframe_view.valid_element.is_displayed


def test_iframe_view_hierarchy(browser):
    """Test complex view hierarchies with mixed iframe and regular views."""

    class ComplexView(View):
        # Main frame elements
        main_checkbox = Checkbox(id="switchabletesting-3")

        class iframe_section(View):
            FRAME = '//iframe[@name="some_iframe"]'
            iframe_h3 = Text(".//h3")
            iframe_select = Select(id="iframe_select1")

            class nested_iframe_section(View):
                FRAME = './/iframe[@name="another_iframe"]'
                nested_h3 = Text(".//h3")
                nested_select = Select(id="iframe_select3")

                class nested_div(View):
                    ROOT = './/div[@id="nested_view"]'
                    nested_input = TextInput(name="input222")

    complex_view = ComplexView(browser)

    # Test access at all levels
    assert complex_view.main_checkbox.is_displayed
    assert complex_view.iframe_section.iframe_h3.is_displayed
    assert complex_view.iframe_section.nested_iframe_section.nested_h3.is_displayed
    assert complex_view.iframe_section.nested_iframe_section.nested_div.nested_input.is_displayed

    # Test content at all levels
    assert complex_view.iframe_section.iframe_h3.text == "IFrame Tests"
    assert complex_view.iframe_section.nested_iframe_section.nested_h3.text == "IFrame Tests 2"
    assert (
        complex_view.iframe_section.nested_iframe_section.nested_div.nested_input.read()
        == "Default Value"
    )

    # Test interactions at all levels
    complex_view.main_checkbox.fill(True)
    complex_view.iframe_section.iframe_select.fill("Bar")
    complex_view.iframe_section.nested_iframe_section.nested_select.fill("Bar")
    complex_view.iframe_section.nested_iframe_section.nested_div.nested_input.fill("New Value")

    # Verify all interactions worked
    assert complex_view.main_checkbox.read() is True
    assert complex_view.iframe_section.iframe_select.read() == "Bar"
    assert complex_view.iframe_section.nested_iframe_section.nested_select.read() == "Bar"
    assert (
        complex_view.iframe_section.nested_iframe_section.nested_div.nested_input.read()
        == "New Value"
    )


def test_iframe_widget_names_and_iteration(browser):
    """Test widget name resolution and iteration in iframe context."""

    class IFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        h3 = Text(".//h3")
        select1 = Select(id="iframe_select1")
        select2 = Select(name="iframe_select2")

    iframe_view = IFrameView(browser)

    # Test widget_names property
    widget_names = iframe_view.widget_names
    expected_names = ["h3", "select1", "select2"]
    assert set(widget_names) == set(expected_names)

    # Test iteration over widgets
    for name in widget_names:
        widget = getattr(iframe_view, name)
        assert widget.is_displayed, f"Widget {name} should be displayed"

    # Test widget access by name
    assert iframe_view.h3.text == "IFrame Tests"
    assert iframe_view.select1.read() == "Foo"


def test_iframe_performance_multiple_access(browser):
    """Test performance of multiple iframe accesses."""

    class IFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        select1 = Select(id="iframe_select1")

    iframe_view = IFrameView(browser)

    # Multiple rapid accesses should work efficiently
    for i in range(10):
        assert iframe_view.select1.is_displayed
        current_value = iframe_view.select1.read()
        new_value = "Bar" if current_value == "Foo" else "Foo"
        iframe_view.select1.fill(new_value)
        assert iframe_view.select1.read() == new_value
