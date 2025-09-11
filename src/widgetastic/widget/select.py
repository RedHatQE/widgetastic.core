from collections import namedtuple
from html import unescape

from cached_property import cached_property

from .base import ClickableMixin
from .base import Widget
from widgetastic.utils import normalize_space
from widgetastic.xpath import quote


class Select(Widget, ClickableMixin):
    """Representation of the bogo-standard ``<select>`` tag.

    Check documentation for each method. The API is based on the playwright select, but modified so
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

    ALL_OPTIONS = """
            (select) => {
                var result_arr = [];
                var opt_elements = select.options;
                for(var i = 0; i < opt_elements.length; i++){
                    var option = opt_elements[i];
                    var value = option.getAttribute("value");
                    result_arr.push([
                        option.innerHTML,
                        value === null ? option.textContent : value
                    ]);
                }
                return result_arr;
            }
        """

    SELECTED_OPTIONS_TEXT = """
            (select) => {
                var result_arr = [];
                var opt_elements = select.selectedOptions;
                for(var i = 0; i < opt_elements.length; i++){
                    result_arr.push(opt_elements[i].innerHTML);
                }
                return result_arr;
            }
        """

    SELECTED_OPTIONS_VALUE = """
            (select) => {
                var result_arr = [];
                var opt_elements = select.selectedOptions;
                for(var i = 0; i < opt_elements.length; i++){
                    result_arr.push(opt_elements[i].getAttribute("value"));
                }
                return result_arr;
            }
        """

    def __init__(self, parent, locator=None, id=None, name=None, logger=None):
        Widget.__init__(self, parent, logger=logger)
        if (locator and id) or (id and name) or (locator and name):
            raise TypeError("You can only pass one of the params locator, id, name into Select")
        if locator is not None:
            self.locator = locator
        elif id is not None:
            self.locator = f".//select[@id={quote(id)}]"
        else:  # name
            self.locator = f".//select[@name={quote(name)}]"

    def __locator__(self):
        return self.locator

    def __repr__(self):
        return f"{type(self).__name__}(locator={self.locator!r})"

    @cached_property
    def is_multiple(self):
        """Detects and returns whether this ``<select>`` is multiple"""
        return self.browser.get_attribute("multiple", self) is not None

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
        select_element = self.browser.element(self)
        options = select_element.evaluate(self.ALL_OPTIONS)

        return [
            self.Option(normalize_space(unescape(option[0])), option[1]) for option in options
        ]  # pragma: no cover

    @property
    def all_selected_options(self):
        """Returns a list of all selected options as their displayed texts."""
        select_element = self.browser.element(self)
        selected_texts = select_element.evaluate(self.SELECTED_OPTIONS_TEXT)

        return [normalize_space(unescape(option)) for option in selected_texts]  # pragma: no cover

    @property
    def all_selected_values(self):
        """Returns a list of all selected options as their values.

        If the value is not present, it is ignored.
        """
        select_element = self.browser.element(self)
        selected_values = select_element.evaluate(self.SELECTED_OPTIONS_VALUE)

        return [value for value in selected_values if value is not None]  # pragma: no cover

    @property
    def first_selected_option(self):
        """Returns the first selected option (or the only selected option)

        Raises:
            :py:class:`ValueError` - in case there is not item selected.
        """
        try:
            return self.all_selected_options[0]
        except IndexError:
            # returning None if nothing is selected
            return None

    def deselect_all(self):
        """Deselect all items. Only works for multiselect.

        Raises:
            :py:class:`NotImplementedError` - If you call this on non-multiselect.
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect all options of a multi-select")

        # In Playwright, passing an empty list deselects all.
        self.browser.element(self).select_option(value=[])

    def get_value_by_text(self, text):
        """Given the visible text, retrieve the underlying value."""
        normalized_text = normalize_space(text)
        for opt_text, opt_value in self.all_options:
            if opt_text == normalized_text:
                return opt_value
        raise ValueError(f"Option with text '{text}' not found in Select")

    def select_by_value(self, *items):
        """Selects item(s) by their respective values in the select.

        Args:
            *items: Items' values to be selected.

        Raises:
            :py:class:`ValueError` - if you pass multiple values and the select is not multiple.
        """
        if len(items) > 1 and not self.is_multiple:
            raise ValueError(f"The Select {self!r} does not allow multiple selections")
        self.browser.element(self).select_option(value=list(items))

    def select_by_visible_text(self, *items):
        """Selects item(s) by their respective displayed text in the select.

        Args:
            *items: Items' visible texts to be selected.

        Raises:
            :py:class:`ValueError` - if you pass multiple values and the select is not multiple.
            :py:class:`ValueError` - if the text was not found.
        """
        if len(items) > 1 and not self.is_multiple:
            raise ValueError(f"The Select {self!r} does not allow multiple selections")

        values_to_select = [self.get_value_by_text(text) for text in items]
        if not values_to_select and items:
            available = ", ".join(repr(opt.text) for opt in self.all_options)
            raise ValueError(
                "Cannot locate option with visible text: {!r}. Available options: {}".format(
                    items[0], available
                )
            )
        self.select_by_value(*values_to_select)

    def read(self):
        """Reads the selected value(s)."""
        items = self.all_selected_options
        if self.is_multiple:
            return items
        else:
            try:
                return items[0]
            except IndexError:
                return None

    def fill(self, item_or_items):
        """Fills the select, accepts list which is dispatched to respective rows."""
        if item_or_items is None:
            items = []
        elif isinstance(item_or_items, list):
            items = item_or_items
        else:
            items = [item_or_items]

        selected_values = set(self.all_selected_values)
        options_to_select = []
        values_to_select = []

        for item in items:
            if isinstance(item, tuple):
                try:
                    mod, value = item
                    if not isinstance(mod, str):
                        raise ValueError("The select modifier must be a string")
                    mod = mod.lower()
                except ValueError:
                    raise ValueError("If passing tuples into the S.fill(), they must be 2-tuples")
            else:
                mod = "by_text"
                value = item

            if mod == "by_text":
                options_to_select.append(value)
            elif mod == "by_value":
                values_to_select.append(value)
            else:
                raise ValueError(f"Unknown select modifier {mod}")

        target_values_to_select = set(values_to_select)

        for text in options_to_select:
            target_values_to_select.add(self.get_value_by_text(text))

        if selected_values == target_values_to_select:
            return False

        if self.is_multiple:
            self.deselect_all()

        self.browser.element(self).select_option(value=list(target_values_to_select))

        return True
