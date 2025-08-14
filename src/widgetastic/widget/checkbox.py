from .base import ClickableMixin
from .input import BaseInput
from widgetastic.exceptions import WidgetOperationFailed


class Checkbox(BaseInput, ClickableMixin):
    """This widget represents the bogo-standard form checkbox.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
        locator: If you have specific locator, use it here.
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
