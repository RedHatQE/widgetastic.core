from widgetastic.exceptions import WidgetOperationFailed
from widgetastic.ouia import OUIAGenericWidget


class Checkbox(OUIAGenericWidget):
    """OUIA version of the :py:class:`widgetastic.widget.CheckBox` widget.

    Args:
        component_id: value of data-ouia-component-id attribute.
        component_type: value of data-ouia-component-type attribute.
    """

    @property
    def selected(self):
        return self.browser.is_selected(self)

    def read(self):
        return self.selected

    def fill(self, value):
        value = bool(value)
        current_value = self.selected
        if value == current_value:
            return False
        else:
            self.click()
            if self.selected != value:
                # TODO: More verbose here
                raise WidgetOperationFailed("Failed to set the checkbox to requested value.")
            return True
