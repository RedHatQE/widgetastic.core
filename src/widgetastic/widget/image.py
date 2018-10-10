# -*- coding: utf-8 -*-
from .base import GenericLocatorWidget

if __name__ == "__main__":
    pass


class Image(GenericLocatorWidget):
    """A widget that represents an image.

    Args:
        locator: Locator of the object on the page.
    """
    @property
    def src(self):
        return self.browser.get_attribute('src', self, parent=self.parent)

    @property
    def alt(self):
        return self.browser.get_attribute('alt', self, parent=self.parent)

    @property
    def title(self):
        return self.browser.get_attribute('title', self, parent=self.parent)
