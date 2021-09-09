from widgetastic.ouia import OUIAGenericWidget


class Text(OUIAGenericWidget):
    """OUIA version of the :py:class:`widgetastic.widget.Text` widget.

    Args:
        component_id: value of data-ouia-component-id attribute.
        component_type: value of data-ouia-component-type attribute.
    """

    @property
    def text(self) -> str:
        return self.browser.text(self, parent=self.parent)

    def read(self) -> str:  # type: ignore
        return self.text
