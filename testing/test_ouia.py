import pytest
from ouia_widgets import Button
from ouia_widgets import Select

from widgetastic.ouia.checkbox import Checkbox
from widgetastic.ouia.input import TextInput
from widgetastic.ouia.text import Text
from widgetastic.widget import View


@pytest.fixture
def testing_view(browser):
    class TestView(View):
        ROOT = ".//div[@id='ouia']"
        button = Button("This is a button")
        select = Select("some_id")
        text = Text(component_id="unique_id", component_type="Text")
        text_input = TextInput(component_id="unique_id", component_type="TextInput")
        checkbox = Checkbox(component_id="unique_id", component_type="CheckBox")

    return TestView(browser)


@pytest.mark.parametrize("widget", ["button", "select", "text", "text_input", "checkbox"])
def test_is_displayed(testing_view, widget):
    widget = getattr(testing_view, widget)
    assert widget.is_displayed


def test_button_click(testing_view):
    testing_view.button.click()


def test_safety(testing_view):
    assert not testing_view.button.is_safe
    assert testing_view.select.is_safe


def test_select(testing_view):
    testing_view.select.choose("first_option")
    testing_view.select.choose("second_option")
