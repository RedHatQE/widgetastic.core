from .base import GenericLocatorWidget


class Text(GenericLocatorWidget):
    """A widget that can represent anything that can be read from the webpage as a text content of
    a tag.

    Args:
        locator: Locator of the object on the page.
    """

    @property
    def text(self):
        return self.browser.text(self, parent=self.parent)

    def read(self):
        return self.text
