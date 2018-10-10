# -*- coding: utf-8 -*-
from widgetastic.exceptions import WidgetOperationFailed
from .input import BaseInput
from .base import ClickableMixin


class Checkbox(BaseInput, ClickableMixin):
    """This widget represents the bogo-standard form checkbox.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
        locator: If you have specific locator, use it here.
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
                raise WidgetOperationFailed('Failed to set the checkbox to requested value.')
            return True
