import pytest

from widgetastic.ouia import OUIAGenericView
from widgetastic.ouia import OUIAGenericWidget
from widgetastic.widget import View


class Button(OUIAGenericWidget):
    OUIA_COMPONENT_TYPE = "PF/Button"


class SelectOption(OUIAGenericWidget):
    OUIA_COMPONENT_TYPE = "PF/SelectOption"


class Select(OUIAGenericView):
    OUIA_COMPONENT_TYPE = "PF/Select"
    first_option = SelectOption("first option")
    second_option = SelectOption("second option")

    def choose(self, option):
        getattr(self, option).click()


@pytest.fixture
def testing_view(browser):
    class TestView(View):
        ROOT = ".//div[@id='ouia']"
        button = Button("This is a button")
        select = Select("some_id")

    return TestView(browser)


def test_basic(testing_view):
    assert testing_view.is_displayed
    assert testing_view.button.is_displayed
    assert testing_view.select.is_displayed
    assert not testing_view.button.is_safe
    assert testing_view.select.is_safe
    testing_view.button.click()
    testing_view.select.choose("first_option")
    testing_view.select.choose("second_option")
