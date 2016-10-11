# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""This module contains the base classes that are used to implement the more specific behaviour."""

import inspect
import six
from cached_property import cached_property
from collections import defaultdict
from copy import copy
from smartloc import Locator
from wait_for import wait_for

from .browser import Browser
from .exceptions import (
    NoSuchElementException, LocatorNotImplemented, WidgetOperationFailed, DoNotReadThisWidget)
from .log import PrependParentsAdapter, create_widget_logger, logged
from .utils import Widgetable, Fillable, attributize_string
from .xpath import quote


def do_not_read_this_widget():
    """Call inside widget's read method in case you don't want it to appear in the data."""
    raise DoNotReadThisWidget('Do not read this widget.')


def wrap_fill_method(method):
    """Generates a method that automatically coerces the first argument as Fillable."""
    @six.wraps(method)
    def wrapped(self, value, *args, **kwargs):
        return method(self, Fillable.coerce(value), *args, **kwargs)

    return wrapped


class WidgetDescriptor(Widgetable):
    """This class handles instantiating and caching of the widgets on view.

    It stores the class and the parameters it should be instantiated with. Once it is accessed from
    the instance of the class where it was defined on, it passes the instance to the widget class
    followed by args and then kwargs.

    It also acts as a counter, so you can then order the widgets by their "creation" stamp.
    """
    def __init__(self, klass, *args, **kwargs):
        self.klass = klass
        self.args = args
        self.kwargs = kwargs

    def __get__(self, obj, type=None):
        if obj is None:  # class access
            return self

        # Cache on WidgetDescriptor
        if self not in obj._widget_cache:
            kwargs = copy(self.kwargs)
            try:
                parent_logger = obj.logger
                current_name = obj._desc_name_mapping[self]
                if isinstance(parent_logger, PrependParentsAdapter):
                    # If it already is adapter, then pull the logger itself out and append
                    # the widget name
                    widget_path = '{}/{}'.format(parent_logger.extra['widget_path'], current_name)
                    parent_logger = parent_logger.logger
                else:
                    # Seems like first in the line.
                    widget_path = current_name

                kwargs['logger'] = create_widget_logger(widget_path, parent_logger)
            except AttributeError:
                pass
            obj._widget_cache[self] = self.klass(obj, *self.args, **kwargs)
        widget = obj._widget_cache[self]
        obj.child_widget_accessed(widget)
        return widget

    def __repr__(self):
        return '<Descriptor: {}, {!r}, {!r}>'.format(self.klass.__name__, self.args, self.kwargs)


class ExtraData(object):
    """This class implements a simple access to the extra data passed through
    :py:class:`widgetastic.browser.Browser` object.

    .. code-block:: python

        widget.extra.foo
        # is equivalent to
        widget.browser.extra_objects['foo']
    """
    # TODO: Possibly replace it with a descriptor of some sort?
    def __init__(self, widget):
        self._widget = widget

    @property
    def _extra_objects_list(self):
        return list(six.iterkeys(self._widget.browser.extra_objects))

    def __dir__(self):
        return self._extra_objects_list

    def __getattr__(self, attr):
        try:
            return self._widget.browser.extra_objects[attr]
        except KeyError:
            raise AttributeError('Extra object {!r} was not found ({} are available)'.format(
                attr, ', '.join(self._extra_objects_list)))


class WidgetMetaclass(type):
    """Metaclass that ensures that ``fill`` and ``read`` methods are logged and coerce Fillable
    properly.

    For ``fill`` methods placed in :py:class:`Widget` descendants it first wraps them using
    :py:func:`wrap_fill_method` that ensures that :py:class:`widgetastic.utils.Fillable` can be
    passed and then it wraps them in the :py:func:`widgetastic.log.logged`.

    The same happens for ``read`` except the ``wrap_fill_method`` which is only useful for ``fill``.

    Therefore, you shall not wrap any ``read`` or ``fill`` methods in
    :py:func:`widgetastic.log.logged`.
    """
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        for key, value in six.iteritems(attrs):
            if key == 'fill':
                # handle fill() specifics
                new_attrs[key] = logged(log_args=True, log_result=True)(wrap_fill_method(value))
            elif key == 'read':
                # handle read() specifics
                new_attrs[key] = logged(log_result=True)(value)
            else:
                # Do nothing
                new_attrs[key] = value
        return super(WidgetMetaclass, cls).__new__(cls, name, bases, new_attrs)


class Widget(six.with_metaclass(WidgetMetaclass, object)):
    """Base class for all UI objects.

    Does couple of things:

        * Ensures it gets instantiated with a browser or another widget as parent. If you create an
          instance in a class, it then creates a WidgetDescriptor which is then invoked on the
          instance and instantiates the widget with underlying browser.
        * Implements some basic interface for all widgets.
    """

    def __new__(cls, *args, **kwargs):
        """Implement some typing saving magic.

        Unless you are passing a :py:class:`Widget` or :py:class:`widgetastic.browser.Browser`
        as a first argument which implies the instantiation of an actual widget, it will return
        :py:class:`WidgetDescriptor` instead which will resolve automatically inside of
        :py:class:`View` instance.

        This allows you a sort of Django-ish access to the defined widgets then.
        """
        if args and isinstance(args[0], (Widget, Browser)):
            return super(Widget, cls).__new__(cls)
        else:
            return WidgetDescriptor(cls, *args, **kwargs)

    def __init__(self, parent, logger=None):
        """If you are inheriting from this class, you **MUST ALWAYS** ensure that the inherited class
        has an init that always takes the ``parent`` as the first argument. You can do that on your
        own, setting the parent as ``self.parent`` or you can do something like this:

        .. code-block:: python

            def __init__(self, parent, arg1, arg2, logger=None):
                super(MyClass, self).__init__(parent, logger=logger)
                # or if you have somehow complex inheritance ...
                Widget.__init__(self, parent, logger=logger)
        """
        self.parent = parent
        if isinstance(logger, PrependParentsAdapter):
            # The logger is already prepared
            self.logger = logger
        else:
            # We need a PrependParentsAdapter here.
            self.logger = create_widget_logger(type(self).__name__, logger)
        self.extra = ExtraData(self)

    @property
    def browser(self):
        """Returns the instance of parent browser.

        Returns:
            :py:class:`widgetastic.browser.Browser` instance

        Raises:
            :py:class:`ValueError` when the browser is not defined, which is an error.
        """
        try:
            return self.parent.browser
        except AttributeError:
            raise ValueError('Unknown value {!r} specified as parent.'.format(self.parent))

    @property
    def parent_view(self):
        """Returns a parent view, if the widget lives inside one.

        Returns:
            :py:class:`View` instance if the widget is defined in one, otherwise ``None``.
        """
        if isinstance(self.parent, View):
            return self.parent
        else:
            return None

    @property
    def is_displayed(self):
        """Shortcut allowing you to detect if the widget is displayed.

        If the logic behind is_displayed is more complex, you can always override this.

        Returns:
            :py:class:`bool`
        """
        return self.browser.is_displayed(self)

    @logged()
    def wait_displayed(self, timeout='10s'):
        """Wait for the element to be displayed. Uses the :py:meth:`is_displayed`

        Args:
            timout: If you want, you can override the default timeout here
        """
        wait_for(lambda: self.is_displayed, timeout=timeout, delay=0.2)

    @logged()
    def move_to(self):
        """Moves the mouse to the Selenium WebElement that is resolved by this widget.

        Returns:
            :py:class:`selenium.webdriver.remote.webelement.WebElement` instance
        """
        return self.browser.move_to_element(self)

    def child_widget_accessed(self, widget):
        """Called when a child widget of this widget gets accessed.

        Useful when eg. the containing widget needs to open for the child widget to become visible.

        Args:
            widget: The widget being accessed.
        """
        pass

    def fill(self, *args, **kwargs):
        """Interactive objects like inputs, selects, checkboxes, et cetera should implement fill.

        When you implement this method, it *MUST ALWAYS* return a boolean whether the value
        *was changed*. Otherwise it can break.

        Returns:
            A boolean whether it changed the value or not.
        """
        raise NotImplementedError(
            'Widget {} does not implement fill()!'.format(type(self).__name__))

    def read(self, *args, **kwargs):
        """Each object should implement read so it is easy to get the value of such object.

        When you implement this method, the exact return value is up to you but it *MUST* be
        consistent with what :py:meth:`fill` takes.
        """
        raise NotImplementedError(
            'Widget {} does not implement read()!'.format(type(self).__name__))


def _gen_locator_meth(loc):
    def __locator__(self):  # noqa
        return loc
    return __locator__


class ViewMetaclass(WidgetMetaclass):
    """metaclass that ensures nested widgets' functionality from the declaration point of view.

    When you pass a ``ROOT`` class attribute, it is used to generate a ``__locator__`` method on
    the view that ensures the view is resolvable.
    """
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        desc_name_mapping = {}
        for base in bases:
            for key, value in six.iteritems(getattr(base, '_desc_name_mapping', {})):
                desc_name_mapping[key] = value
        for key, value in six.iteritems(attrs):
            if inspect.isclass(value) and issubclass(value, View):
                new_attrs[key] = WidgetDescriptor(value)
                desc_name_mapping[new_attrs[key]] = key
            elif isinstance(value, Widgetable):
                new_attrs[key] = value
                desc_name_mapping[value] = key
                for widget in value.child_items:
                    if not isinstance(widget, (Widgetable, Widget)):
                        continue
                    desc_name_mapping[widget] = key
            else:
                new_attrs[key] = value
        if 'ROOT' in new_attrs:
            # For handling the root locator of the View
            rl = Locator(new_attrs['ROOT'])
            new_attrs['__locator__'] = _gen_locator_meth(rl)

        new_attrs['_desc_name_mapping'] = desc_name_mapping
        return super(ViewMetaclass, cls).__new__(cls, name, bases, new_attrs)


class View(six.with_metaclass(ViewMetaclass, Widget)):
    """View is a kind of abstract widget that can hold another widgets. Remembers the order,
    so therefore it can function like a form with defined filling order.

    It looks like this:

    .. code-block:: python

        class Login(View):
            user = SomeInputWidget('user')
            password = SomeInputWidget('pass')
            login = SomeButtonWidget('Log In')

            def a_method(self):
                do_something()

    The view is usually instantiated with an instance of
    :py:class:`widgetastic.browser.Browser`, which will then enable resolving of all of the
    widgets defined.

    Args:
        parent: A parent :py:class:`View` or :py:class:`widgetastic.browser.Browser`
        additional_context: If the view needs some context, for example - you want to check that
            you are on the page of user XYZ but you can also be on the page for user FOO, then
            you shall use the ``additional_context`` to pass in required variables that will allow
            you to detect this.
    """

    def __init__(self, parent, additional_context=None, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.context = additional_context or {}
        self._widget_cache = {}

    def flush_widget_cache(self):
        # Recursively ...
        for view in self._views:
            view._widget_cache.clear()
        self._widget_cache.clear()

    @staticmethod
    def nested(view_class):
        """Shortcut for :py:class:`WidgetDescriptor`

        Usage:

        .. code-block:: python

            class SomeView(View):
                some_widget = Widget()

                @View.nested
                class another_view(View):
                    pass

        Why? The problem is counting things. When you are placing widgets themselves on a view, they
        handle counting themselves and just work. But when you are creating a nested view, that is a
        bit of a problem. The widgets are instantiated, whereas the views are placed in a class and
        wait for the :py:class:`ViewMetaclass` to pick them up, but that happens after all other
        widgets have been instantiated into the :py:class:`WidgetDescriptor`s, which has the
        consequence of things being out of order. By wrapping the class into the descriptor we do
        the job of :py:meth:`Widget.__new__` which creates the :py:class:`WidgetDescriptor` if not
        called with a :py:class:`widgetastic.browser.Browser` or :py:class:`Widget` instance as the
        first argument.

        Args:
            view_class: A subclass of :py:class:`View`
        """
        return WidgetDescriptor(view_class)

    @classmethod
    def widget_names(cls):
        """Returns a list of widget names in the order they were defined on the class.

        Returns:
            A :py:class:`list` of :py:class:`Widget` instances.
        """
        result = []
        for key in dir(cls):
            value = getattr(cls, key)
            if isinstance(value, Widgetable):
                result.append((key, value))
        return [name for name, _ in sorted(result, key=lambda pair: pair[1]._seq_id)]

    @property
    def _views(self):
        """Returns all sub-views of this view.

        Returns:
            A :py:class:`list` of :py:class:`View`
        """
        return [view for view in self if isinstance(view, View)]

    @property
    def is_displayed(self):
        """Overrides the :py:meth:`Widget.is_displayed`. The difference is that if the view does
        not have the root locator, it assumes it is displayed.

        Returns:
            :py:class:`bool`
        """
        try:
            return super(View, self).is_displayed
        except LocatorNotImplemented:
            return True

    def move_to(self):
        """Overrides the :py:meth:`Widget.move_to`. The difference is that if the view does
        not have the root locator, it returns None.

        Returns:
            :py:class:`selenium.webdriver.remote.webelement.WebElement` instance or ``None``.
        """
        try:
            return super(View, self).move_to()
        except LocatorNotImplemented:
            return None

    def fill(self, values):
        """Implementation of form filling.

        This method goes through all widgets defined on this view one by one and calls their
        ``fill`` methods appropriately.

        ``None`` values will be ignored.

        Args:
            values: A dictionary of ``widget_name: value_to_fill``.

        Returns:
            :py:class:`bool` if the fill changed any value.
        """
        was_change = False
        self.before_fill(values)
        for name in self.widget_names():
            if name not in values or values[name] is None:
                continue

            widget = getattr(self, name)
            try:
                if widget.fill(values[name]):
                    was_change = True
            except NotImplementedError:
                continue

        self.after_fill(was_change)
        return was_change

    def read(self):
        """Reads the contents of the view and presents them as a dictionary.

        Returns:
            A :py:class:`dict` of ``widget_name: widget_read_value`` where the values are retrieved
            using the :py:meth:`Widget.read`.
        """
        result = {}
        for widget_name in self.widget_names():
            widget = getattr(self, widget_name)
            try:
                value = widget.read()
            except (NotImplementedError, NoSuchElementException, DoNotReadThisWidget):
                continue

            result[widget_name] = value

        return result

    def before_fill(self, values):
        """A hook invoked before the loop of filling is invoked.

        Args:
            values: The same values that are passed to :py:meth:`fill`
        """
        pass

    def after_fill(self, was_change):
        """A hook invoked after all the widgets were filled.

        Args:
            was_change: :py:class:`bool` signalizing whether the :py:meth:`fill` changed anything,
        """
        pass

    def __iter__(self):
        """Allows iterating over the widgets on the view."""
        for widget_attr in self.widget_names():
            yield getattr(self, widget_attr)


class ClickableMixin(object):

    @logged()
    def click(self):
        return self.browser.click(self)


class Text(Widget, ClickableMixin):
    """A widget that an represent anything that can be read from the webpage as a text content of
    a tag.

    Args:
        locator: Locator of the object ob the page.
    """
    def __init__(self, parent, locator, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.locator = locator

    def __locator__(self):
        return self.locator

    @property
    def text(self):
        return self.browser.text(self)

    def read(self):
        return self.text


class BaseInput(Widget):
    """This represents the bare minimum to interact with bogo-standard form inputs.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
    """
    def __init__(self, parent, name=None, id=None, logger=None):
        if (name is None and id is None) or (name is not None and id is not None):
            raise TypeError('TextInput must have either name= or id= specified but also not both.')
        Widget.__init__(self, parent, logger=logger)
        self.name = name
        self.id = id

    def __locator__(self):
        if self.name is not None:
            id_attr = '@name={}'.format(quote(self.name))
        else:
            id_attr = '@id={}'.format(quote(self.id))
        return './/*[(self::input or self::textarea) and {}]'.format(id_attr)


class TextInput(BaseInput):
    """This represents the bare minimum to interact with bogo-standard text form inputs.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
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
        if value.startswith(current_value):
            # only add the additional characters, like user would do
            to_fill = value[len(current_value):]
        else:
            # Clear and type everything
            self.browser.clear(self)
            to_fill = value
        self.browser.send_keys(to_fill, self)
        return True


class Checkbox(BaseInput, ClickableMixin):
    """This widget represents the bogo-standard form checkbox.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
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


class TableColumn(Widget, ClickableMixin):
    """Represents a cell in the row."""
    def __init__(self, parent, position, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.position = position

    def __locator__(self):
        return self.browser.element('./td[{}]'.format(self.position + 1), parent=self.parent)

    @property
    def text(self):
        return self.browser.text(self)


class TableRow(Widget, ClickableMixin):
    """Represents a row in the table.

    If subclassing and also changing the Column class, do not forget to set the Column to the new
    class.

    Args:
        index: Position of the row in the table.
    """
    Column = TableColumn

    def __init__(self, parent, index, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.index = index

    def __locator__(self):
        loc = self.parent.ROW_AT_INDEX.format(self.index + 1)
        return self.browser.element(loc, parent=self.parent)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.Column(self, item, logger=self.logger)
        elif isinstance(item, six.string_types):
            return self[self.parent.header_index_mapping[item]]
        else:
            raise TypeError('row[] accepts only integers and strings')

    def __getattr__(self, attr):
        try:
            return self[self.parent.attributized_headers[attr]]
        except KeyError:
            raise AttributeError('Cannot find column {} in the table'.format(attr))

    def __dir__(self):
        result = super(TableRow, self).__dir__()
        result.extend(self.parent.attributized_headers.keys())
        return sorted(result)

    def __iter__(self):
        for i, header in enumerate(self.parent.headers):
            yield header, self[i]


# TODO: read/fill? How would that work?
class Table(Widget):
    """Basic table-handling class.

    Usage is as follows assuming the table is instantiated as ``view.table``:

    .. code-block:: python

        # List the headers
        view.table.headers  # => (None, 'something', ...)
        # Access rows by their position
        view.table[0] # => gives you the first row
        # Or you can iterate through rows simply
        for row in view.table:
            do_something()
        # You can filter rows
        # The column names are "attributized"
        view.table.rows(column_name='asdf') # All rows where asdf is in "Column Name"
        # And with Django fashion:
        view.table.rows(column_name__contains='asdf')
        view.table.rows(column_name__startswith='asdf')
        view.table.rows(column_name__endswith='asdf')
        # You can put multiple filters together.
        # And you can of course query a songle row
        row = view.table.row(column_name='asdf')

        # When you have a row, you can do these things.
        row[0]  # => gives you the first column cell in the row
        row['Column Name'] # => Gives you the column that is named "Column Name". Non-attributized
        row.column_name # => Gives you the column whose attributized name is "column_name"

        # Basic row column can give you text
        assert row.column_name.text == 'some text'
        # Or you can click at it
        assert row.column_name.click()

    If you subclass Table, Row, or Column, do not forget to update the Row in Table and Column in
    Row in order for the classes to use the correct class.

    Args:
        locator: A locator to the table ``<table>`` tag.
    """
    HEADERS = './thead/tr/th|./tr/th'
    ROWS = './tbody/tr[./td]|./tr[not(./th) and ./td]'
    ROW_AT_INDEX = './tbody/tr[{0}]|./tr[not(./th)][{0}]'

    Row = TableRow

    def __init__(self, parent, locator, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.locator = locator

    def __locator__(self):
        return self.locator

    def clear_cache(self):
        for item in [
                'headers', 'attributized_headers', 'header_index_mapping', 'index_header_mapping']:
            try:
                delattr(self, item)
            except AttributeError:
                pass

    @cached_property
    def headers(self):
        result = []
        for header in self.browser.elements(self.HEADERS, parent=self):
            result.append(self.browser.text(header).strip() or None)

        without_none = [x for x in result if x is not None]

        if len(without_none) != len(set(without_none)):
            self.logger.warning(
                'Detected duplicate headers in %r. Correct functionality is not guaranteed',
                without_none)

        return tuple(result)

    @cached_property
    def attributized_headers(self):
        return {attributize_string(h): h for h in self.headers if h is not None}

    @cached_property
    def header_index_mapping(self):
        return {h: i for i, h in enumerate(self.headers) if h is not None}

    @cached_property
    def index_header_mapping(self):
        return {i: h for h, i in self.header_index_mapping.items()}

    def __getitem__(self, at_index):
        if not isinstance(at_index, int):
            raise TypeError('table indexing only accepts integers')
        return self.Row(self, at_index, logger=self.logger)

    def row(self, **filters):
        return list(self.rows(**filters))[0]

    def __iter__(self):
        return self.rows()

    def _get_number_preceeding_rows(self, row_el):
        """This is a sort of trick that helps us remove stale element errors.

        We know that correct tables only have ``<tr>`` elements next to each other. We do not want
        to pass around webelements because they can get stale. Therefore this trick will give us the
        number of elements that precede this element, effectively giving us the index of the row.

        How simple.
        """
        return self.browser.execute_script(
            """\
            var prev = []; var element = arguments[0];
            while (element.previousElementSibling)
                prev.push(element = element.previousElementSibling);
            return prev.length;
            """, row_el)

    def rows(self, **filters):
        if not filters:
            return self._all_rows()
        else:
            return self._filtered_rows(**filters)

    def _all_rows(self):
        for row_pos in range(len(self.browser.elements(self.ROWS, parent=self))):
            yield self.Row(self, row_pos, logger=self.logger)

    def _filtered_rows(self, **filters):
        # Pre-process the filters
        processed_filters = defaultdict(list)
        for filter_column, filter_value in six.iteritems(filters):
            if '__' in filter_column:
                column, method = filter_column.rsplit('__', 1)
            else:
                column = filter_column
                method = None
            column_index = self.header_index_mapping[self.attributized_headers[column]]
            processed_filters[column_index].append((method, filter_value))

        # Build the query
        query_parts = []
        for column_index, matchers in six.iteritems(processed_filters):
            col_query_parts = []
            for method, value in matchers:
                if method is None:
                    # equals
                    q = 'normalize-space(.)=normalize-space({})'.format(quote(value))
                elif method == 'contains':
                    # in
                    q = 'contains(normalize-space(.), normalize-space({}))'.format(quote(value))
                elif method == 'startswith':
                    # starts with
                    q = 'starts-with(normalize-space(.), normalize-space({}))'.format(quote(value))
                elif method == 'endswith':
                    # ends with
                    # This needs to be faked since selenium does not support this feature.
                    q = (
                        'substring(normalize-space(.), '
                        'string-length(normalize-space(.)) - string-length({0}) + 1)={0}').format(
                            'normalize-space({})'.format(quote(value)))
                else:
                    raise ValueError('Unknown method {}'.format(method))
                col_query_parts.append(q)
            query_parts.append(
                './td[{}][{}]'.format(column_index + 1, ' and '.join(col_query_parts)))

        query = './/tr[{}]'.format(' and '.join(query_parts))

        for row_element in self.browser.elements(query, parent=self):
            yield self.Row(self, self._get_number_preceeding_rows(row_element), logger=self.logger)
