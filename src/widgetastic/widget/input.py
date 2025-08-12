from .base import Widget
from widgetastic.exceptions import DoNotReadThisWidget
from widgetastic.xpath import quote


class BaseInput(Widget):
    """This represents the bare minimum to interact with bogo-standard form inputs.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
        locator: If you have specific locator, use it here.
    """

    def __init__(self, parent, name=None, id=None, locator=None, logger=None):
        if (locator and (name or id)) or (name and (id or locator)) or (id and (name or locator)):
            raise TypeError("You can only pass one of name, id or locator!")
        Widget.__init__(self, parent, logger=logger)
        self.name = None
        self.id = None
        if name or id:
            if name is not None:
                id_attr = f"@name={quote(name)}"
                self.name = name
            elif id is not None:
                id_attr = f"@id={quote(id)}"
                self.id = id
            self.locator = f".//*[(self::input or self::textarea) and {id_attr}]"
        else:
            self.locator = locator

    def __repr__(self):
        return f"{type(self).__name__}(locator={self.locator!r})"

    def __locator__(self):
        return self.locator


class TextInput(BaseInput):
    """This represents the bare minimum to interact with bogo-standard text form inputs.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
        locator: If you have specific locator, use it here.
    """

    @property
    def value(self):
        return self.browser.input_value(self)

    def read(self):
        return self.value

    def fill(self, value, sensitive=False):
        """Fill TextInput widget with value
        Args:
           value: Text to be filled into the input.
           sensitive: Bool, If is set to True do not log sensitive data.
        """
        current_value = self.value
        if value == current_value:
            return False

        # Clear and type everything
        self.browser.clear(self)
        self.browser.send_keys(value, self, sensitive)
        return True


class FileInput(BaseInput):
    """This represents the file input.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
        locator: If you have specific locator, use it here.
    """

    def read(self):
        """Reading a file input's value is not a reliable operation and is disabled."""
        raise DoNotReadThisWidget()

    def fill(self, value):
        """Fills the file input with a path to a local file.

        Uses Playwright's dedicated method for handling file uploads.
        """
        self.browser.element(self).set_input_files(value)
        return True


class ColourInput(BaseInput):
    """Represents the input for inputting colour values.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
        locator: If you have specific locator, use it here.
    """

    @property
    def colour(self):
        """Returns the current color value of the input."""
        return self.browser.input_value(self)

    @colour.setter
    def colour(self, value):
        """Sets the color value of the input."""
        self.browser.fill(value, self)

    def read(self):
        """Reads the current color value."""
        return self.colour

    def fill(self, value):
        """Fills the input with a new color value."""
        if self.colour == value:
            return False
        self.colour = value
        return True
