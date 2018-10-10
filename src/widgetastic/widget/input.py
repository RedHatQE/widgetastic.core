# -*- coding: utf-8 -*-
from jsmin import jsmin
from selenium.webdriver.remote.file_detector import LocalFileDetector

from widgetastic.exceptions import DoNotReadThisWidget
from .base import Widget
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
            raise TypeError('You can only pass one of name, id or locator!')
        Widget.__init__(self, parent, logger=logger)
        self.name = None
        self.id = None
        if name or id:
            if name is not None:
                id_attr = '@name={}'.format(quote(name))
                self.name = name
            elif id is not None:
                id_attr = '@id={}'.format(quote(id))
                self.id = id
            self.locator = './/*[(self::input or self::textarea) and {}]'.format(id_attr)
        else:
            self.locator = locator

    def __repr__(self):
        return '{}(locator={!r})'.format(type(self).__name__, self.locator)

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
        return self.browser.get_attribute('value', self)

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


class FileInput(BaseInput):
    """This represents the file input.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
        locator: If you have specific locator, use it here.
    """

    def read(self):
        raise DoNotReadThisWidget()

    def fill(self, value):
        with self.browser.selenium.file_detector_context(LocalFileDetector):
            self.browser.send_keys(value, self)
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
        return self.browser.execute_script('return arguments[0].value;', self)

    @colour.setter
    def colour(self, value):
        self.browser.execute_script(jsmin('''
            arguments[0].value = arguments[1];
            if(arguments[0].onchange !== null) {
                arguments[0].onchange();
            }
        '''), self, value)

    def read(self):
        return self.colour

    def fill(self, value):
        if self.colour == value:
            return False
        self.colour = value
        return True
