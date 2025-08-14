from widgetastic.exceptions import WidgetOperationFailed
from widgetastic.ouia import OUIAGenericWidget


class Checkbox(OUIAGenericWidget):
    """OUIA version of the :py:class:`widgetastic.widget.CheckBox` widget.

    Args:
        component_id: value of data-ouia-component-id attribute.
        component_type: value of data-ouia-component-type attribute.
    """

    @property
    def selected(self) -> bool:
        return self.browser.is_checked(self)

    def read(self) -> bool:
        return self.selected

    def fill(self, value: bool | str) -> bool:
        value = bool(value)
        current_value = self.selected
        if value == current_value:
            return False

        if value:
            self.browser.check(self)
        else:
            self.browser.uncheck(self)
        if self.selected != value:
            raise WidgetOperationFailed("Failed to set the checkbox to requested value.")
        return True
