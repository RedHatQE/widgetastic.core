from widgetastic.ouia import OUIAGenericWidget


class TextInput(OUIAGenericWidget):
    """OUIA version of the :py:class:`widgetastic.widget.TextInput` widget.

    Args:
        component_id: value of data-ouia-component-id attribute.
        component_type: value of data-ouia-component-type attribute.
    """

    @property
    def value(self):
        return self.browser.get_attribute("value", self)

    def read(self):
        return self.value

    def fill(self, value):
        current_value = self.value
        if value == current_value:
            return False
        # Clear and type everything
        self.browser.click(self)
        self.browser.clear(self)
        self.browser.send_keys(value, self)
        return True
