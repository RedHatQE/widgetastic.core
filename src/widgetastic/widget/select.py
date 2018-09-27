# -*- coding: utf-8 -*-
import six
from collections import namedtuple

from cached_property import cached_property
from jsmin import jsmin
from six.moves import html_parser

from widgetastic.utils import normalize_space
from .base import Widget
from widgetastic.xpath import quote


class Select(Widget):
    """Representation of the bogo-standard ``<select>`` tag.

    Check documentation for each method. The API is based on the selenium select, but modified so
    we don't bother with WebElements.

    Fill and read work as follows:

    .. code-block:: python

        view.select.fill('foo')
        view.select.fill(['foo'])
        # Are equivalent


    This implies that you can fill either single value or multiple values. If you need to fill
    the select using the value and not the text, you can pass a tuple instead of the string like
    this:

    .. code-block:: python

        view.select.fill(('by_value', 'some_value'))
        # Or if you have multiple items
        view.select.fill([('by_value', 'some_value'), 'something by text', ...])

    The :py:meth:`read` returns a :py:class:`list` in case the select is multiselect, otherwise it
    returns the value directly.

    Arguments are exclusive, so only one at time can be used.

    Args:
        locator: If you have a full locator to locate this select.
        id: If you want to locate the select by the ID
        name: If you want to locate the select by name.

    Raises:
        :py:class:`TypeError` - if you pass more than one of the abovementioned args.
    """
    Option = namedtuple("Option", ["text", "value"])

    ALL_OPTIONS = jsmin('''\
            var result_arr = [];
            var opt_elements = arguments[0].options;
            for(var i = 0; i < opt_elements.length; i++){
                var option = opt_elements[i];
                result_arr.push([option.innerHTML, option.getAttribute("value")]);
            }
            return result_arr;
        ''')

    SELECTED_OPTIONS = jsmin('return arguments[0].selectedOptions;')
    SELECTED_OPTIONS_TEXT = jsmin('''\
            var result_arr = [];
            var opt_elements = arguments[0].selectedOptions;
            for(var i = 0; i < opt_elements.length; i++){
                result_arr.push(opt_elements[i].innerHTML);
            }
            return result_arr;
        ''')

    SELECTED_OPTIONS_VALUE = jsmin('''\
            var result_arr = [];
            var opt_elements = arguments[0].selectedOptions;
            for(var i = 0; i < opt_elements.length; i++){
                result_arr.push(opt_elements[i].getAttribute("value"));
            }
            return result_arr;
        ''')

    def __init__(self, parent, locator=None, id=None, name=None, logger=None):
        Widget.__init__(self, parent, logger=logger)
        if (locator and id) or (id and name) or (locator and name):
            raise TypeError('You can only pass one of the params locator, id, name into Select')
        if locator is not None:
            self.locator = locator
        elif id is not None:
            self.locator = './/select[@id={}]'.format(quote(id))
        else:  # name
            self.locator = './/select[@name={}]'.format(quote(name))

    def __locator__(self):
        return self.locator

    def __repr__(self):
        return '{}(locator={!r})'.format(type(self).__name__, self.locator)

    @cached_property
    def is_multiple(self):
        """Detects and returns whether this ``<select>`` is multiple"""
        return self.browser.get_attribute('multiple', self) is not None

    @property
    def classes(self):
        """Returns the classes associated with the select."""
        return self.browser.classes(self)

    @property
    def all_options(self):
        """Returns a list of tuples of all the options in the Select.

        Text first, value follows.


        Returns:
            A :py:class:`list` of :py:class:`Option`
        """
        # More reliable using javascript
        options = self.browser.execute_script(self.ALL_OPTIONS, self.browser.element(self))
        parser = html_parser.HTMLParser()
        return [
            self.Option(normalize_space(parser.unescape(option[0])), option[1])
            for option in options]

    @property
    def all_selected_options(self):
        """Returns a list of all selected options as their displayed texts."""
        parser = html_parser.HTMLParser()
        return [
            normalize_space(parser.unescape(option))
            for option
            in self.browser.execute_script(self.SELECTED_OPTIONS_TEXT, self.browser.element(self))]

    @property
    def all_selected_values(self):
        """Returns a list of all selected options as their values.

        If the value is not present, it is ignored.
        """
        values = self.browser.execute_script(
            self.SELECTED_OPTIONS_VALUE,
            self.browser.element(self))
        return [value for value in values if value is not None]

    @property
    def first_selected_option(self):
        """Returns the first selected option (or the only selected option)

        Raises:
            :py:class:`ValueError` - in case there is not item selected.
        """
        try:
            return self.all_selected_options[0]
        except IndexError:
            raise ValueError("No options are selected")

    def deselect_all(self):
        """Deselect all items. Only works for multiselect.

        Raises:
            :py:class:`NotImplementedError` - If you call this on non-multiselect.
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect all options of a multi-select")

        for opt in self.browser.execute_script(self.SELECTED_OPTIONS, self.browser.element(self)):
            self.browser.raw_click(opt)

    def get_value_by_text(self, text):
        """Given the visible text, retrieve the underlying value."""
        locator = ".//option[normalize-space(.)={}]".format(quote(normalize_space(text)))
        return self.browser.get_attribute("value", locator=locator, parent=self)

    def select_by_value(self, *items):
        """Selects item(s) by their respective values in the select.

        Args:
            *items: Items' values to be selected.

        Raises:
            :py:class:`ValueError` - if you pass multiple values and the select is not multiple.
            :py:class:`ValueError` - if the value was not found.
        """
        if len(items) > 1 and not self.is_multiple:
            raise ValueError(
                'The Select {!r} does not allow multiple selections'.format(self))

        for value in items:
            matched = False
            for opt in self.browser.elements(
                    './/option[@value={}]'.format(quote(value)),
                    parent=self):
                if not opt.is_selected():
                    opt.click()

                if not self.is_multiple:
                    return
                matched = True

            if not matched:
                raise ValueError("Cannot locate option with value: {!r}".format(value))

    def select_by_visible_text(self, *items):
        """Selects item(s) by their respective displayed text in the select.

        Args:
            *items: Items' visible texts to be selected.

        Raises:
            :py:class:`ValueError` - if you pass multiple values and the select is not multiple.
            :py:class:`ValueError` - if the text was not found.
        """
        if len(items) > 1 and not self.is_multiple:
            raise ValueError(
                'The Select {!r} does not allow multiple selections'.format(self))

        for text in items:
            matched = False
            for opt in self.browser.elements(
                    './/option[normalize-space(.)={}]'.format(quote(normalize_space(text))),
                    parent=self):
                if not opt.is_selected():
                    opt.click()

                if not self.is_multiple:
                    return
                matched = True

            if not matched:
                available = ", ".join(repr(opt.text) for opt in self.all_options)
                raise ValueError(
                    "Cannot locate option with visible text: {!r}. Available options: {}".format(
                        text, available))

    def read(self):
        items = self.all_selected_options
        if self.is_multiple:
            return items
        else:
            try:
                return items[0]
            except IndexError:
                return None

    def fill(self, item_or_items):
        if item_or_items is None:
            items = []
        elif isinstance(item_or_items, list):
            items = item_or_items
        else:
            items = [item_or_items]

        selected_values = self.all_selected_values
        selected_options = self.all_selected_options
        options_to_select = []
        values_to_select = []
        deselect = True
        for item in items:
            if isinstance(item, tuple):
                try:
                    mod, value = item
                    if not isinstance(mod, six.string_types):
                        raise ValueError('The select modifier must be a string')
                    mod = mod.lower()
                except ValueError:
                    raise ValueError('If passing tuples into the S.fill(), they must be 2-tuples')
            else:
                mod = 'by_text'
                value = item

            if mod == 'by_text':
                value = normalize_space(value)
                if value in selected_options:
                    deselect = False
                    continue
                options_to_select.append(value)
            elif mod == 'by_value':
                if value in selected_values:
                    deselect = False
                    continue
                values_to_select.append(value)
            else:
                raise ValueError('Unknown select modifier {}'.format(mod))

        if deselect:
            try:
                self.deselect_all()
                deselected = bool(selected_options or selected_values)
            except NotImplementedError:
                deselected = False
        else:
            deselected = False

        if options_to_select:
            self.select_by_visible_text(*options_to_select)

        if values_to_select:
            self.select_by_value(*values_to_select)

        return bool(options_to_select or values_to_select or deselected)
