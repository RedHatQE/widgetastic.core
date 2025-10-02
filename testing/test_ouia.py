import pytest
from ouia_widgets import Button
from ouia_widgets import Select

from widgetastic.ouia import OUIAGenericView
from widgetastic.ouia.checkbox import Checkbox
from widgetastic.ouia.input import TextInput
from widgetastic.ouia.text import Text


@pytest.fixture
def testing_view(browser):
    class TestView(OUIAGenericView):
        OUIA_COMPONENT_TYPE = "TestView"
        OUIA_ID = "ouia"
        button = Button("This is a button")
        select = Select("some_id")
        text = Text(component_id="unique_id", component_type="Text")
        text_input = TextInput(component_id="unique_id", component_type="TextInput")
        checkbox = Checkbox(component_id="unique_id", component_type="CheckBox")

    return TestView(browser)


def test_ouia_view_without_id(browser):
    class TestView(OUIAGenericView):
        OUIA_COMPONENT_TYPE = "TestView"

    view = TestView(browser)
    assert view.is_displayed
    assert view.locator == './/*[contains(@data-ouia-component-type,"TestView")]'


def test_ouia_view(testing_view):
    assert (
        testing_view.locator
        == './/*[contains(@data-ouia-component-type,"TestView") and @data-ouia-component-id="ouia"]'
    )
    assert testing_view.is_displayed


@pytest.mark.parametrize("widget", ["button", "select", "text", "text_input", "checkbox"])
def test_ouia_widgets_display_and_repr(testing_view, widget):
    """Test OUIA widget display and __repr__."""
    widget = getattr(testing_view, widget)
    assert widget.is_displayed

    # Test __repr__ method
    repr_str = repr(widget)
    assert "ouia type:" in repr_str
    # All test widgets have component_id defined, so should include it
    assert "ouia id:" in repr_str


def test_button_click(testing_view):
    testing_view.button.click()


def test_safety(testing_view):
    assert not testing_view.button.is_safe
    assert testing_view.select.is_safe


def test_ouia_widget_functionality(testing_view):
    """Test comprehensive OUIA widget functionality for full coverage"""

    # Test Select widget functionality
    assert "second" in testing_view.select.choose("second option")
    assert "first" in testing_view.select.choose("first option")

    # Test Text widget read functionality
    text_widget = testing_view.text
    text_value = text_widget.text
    assert text_widget.read() == text_value

    # Test TextInput read/fill functionality
    input_widget = testing_view.text_input
    initial_value = input_widget.value
    assert input_widget.read() == initial_value

    # Test fill method
    test_input = "test value"
    changed = input_widget.fill(test_input)
    assert changed
    assert input_widget.read() == test_input

    # Test no change when filling same value
    no_change = input_widget.fill(test_input)
    assert not no_change

    # Test Checkbox read/fill functionality
    checkbox = testing_view.checkbox
    initial_checked = checkbox.selected
    assert checkbox.read() == initial_checked

    # Test checkbox fill method
    new_state = not initial_checked
    changed = checkbox.fill(new_state)
    assert changed
    assert checkbox.selected == new_state

    # Test no change when filling same checkbox value
    no_change = checkbox.fill(new_state)
    assert not no_change


def test_widget_without_id(browser):
    """Test widgets without component_id"""

    class TestView(OUIAGenericView):
        OUIA_COMPONENT_TYPE = "TestView"
        button = Button()

    view = TestView(browser)
    assert view.is_displayed
    assert view.button.locator == './/*[contains(@data-ouia-component-type,"PF/Button")]'

    # Test __repr__ method for widget without component_id
    repr_str = repr(view.button)
    assert 'ouia type: "PF/Button"' in repr_str
    # Button without component_id should not include "ouia id" in repr
    assert 'ouia id: ""' in repr_str
