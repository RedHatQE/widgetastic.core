# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import inspect
from smartloc import Locator
from threading import Lock
from wait_for import wait_for

from .browser import Browser
from .exceptions import NoSuchElementException, LocatorNotImplemented


class WidgetDescriptor(object):
    """This class handles instantiating and caching of the widgets on view."""
    _seq_cnt = 0
    _seq_cnt_lock = Lock()

    def __new__(cls, *args, **kwargs):
        o = super(WidgetDescriptor, cls).__new__(cls)
        with WidgetDescriptor._seq_cnt_lock:
            o._seq_id = WidgetDescriptor._seq_cnt
            WidgetDescriptor._seq_cnt += 1
        return o

    def __init__(self, klass, *args, **kwargs):
        self.klass = klass
        self.args = args
        self.kwargs = kwargs

    def __get__(self, obj, type=None):
        if obj is None:  # class access
            return self

        # Cache on WidgetDescriptor
        if self not in obj._widget_cache:
            obj._widget_cache[self] = self.klass(obj, *self.args, **self.kwargs)
        return obj._widget_cache[self]

    def __repr__(self):
        if self.args:
            args = ', ' + ', '.join(repr(arg) for arg in self.args)
        else:
            args = ''
        if self.kwargs:
            kwargs = ', ' + ', '.join(
                '{}={}'.format(k, repr(v)) for k, v in self.kwargs.iteritems())
        else:
            kwargs = ''
        return '{}({}{}{})'.format(type(self).__name__, self.klass.__name__, args, kwargs)


class Widget(object):
    """Base class for all UI objects.

    Does couple of things:
    * Ensures it gets instantiated with a browser or another widget as parent. If you create an
      instance in a class, it then creates a WidgetDescriptor which is then invoked on the instance
      and instantiates the widget with underlying browser.
    * Implements some basic interface for all widgets.
    """

    def __new__(cls, *args, **kwargs):
        """Implement some typing saving magic.

        Unless you are passing a Widget or Browser as a first argument which implies the
        instantiation of an actual widget, it will return WidgetDescriptor instead which will
        resolve automatically inside of View instance.
        """
        if args and isinstance(args[0], (Widget, Browser)):
            return super(Widget, cls).__new__(cls, *args, **kwargs)
        else:
            return WidgetDescriptor(cls, *args, **kwargs)

    def __init__(self, parent):
        self.parent = parent

    @property
    def browser(self):
        try:
            return self.parent.browser
        except AttributeError:
            raise ValueError('Unknown value {} specified as parent.'.format(repr(self.parent)))

    @property
    def parent_view(self):
        if isinstance(self.parent, View):
            return self.parent
        else:
            return None

    @property
    def is_displayed(self):
        return self.browser.is_displayed(self)

    def wait_displayed(self):
        wait_for(lambda: self.is_displayed, timeout='15s', delay=0.2)

    def move_to(self):
        return self.browser.move_to_element(self)

    def fill(self):
        """Interactive objects like inputs, selects, checkboxes, et cetera should implement fill.

        Returns:
            A boolean whether it changed the value or not.
        """
        raise NotImplementedError(
            'Widget {} does not implement fill()!'.format(type(self).__name__))

    def read(self):
        """Each object should implement read so it is easy to get the value of such object."""
        raise NotImplementedError(
            'Widget {} does not implement read()!'.format(type(self).__name__))

    def __element__(self):
        """Default functionality, resolves :py:meth:`__locator__`."""
        try:
            return self.browser.element(self)
        except AttributeError:
            raise LocatorNotImplemented('You have to implement __locator__ or __element__')


def _gen_locator_meth(loc):
    def __locator__(self):  # noqa
        return loc
    return __locator__


class ViewMetaclass(type):
    """metaclass that ensures nested widgets' functionality from the declaration point of view."""
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        for key, value in attrs.iteritems():
            if inspect.isclass(value) and getattr(value, '__metaclass__', None) is cls:
                new_attrs[key] = WidgetDescriptor(value)
            else:
                new_attrs[key] = value
        if 'ROOT' in new_attrs:
            # For handling the root locator of the View
            rl = Locator(new_attrs['ROOT'])
            new_attrs['__locator__'] = _gen_locator_meth(rl)
        return super(ViewMetaclass, cls).__new__(cls, name, bases, new_attrs)


class View(Widget):
    """View is a kind of abstract widget that can hold another widgets. Remembers the order,
    so therefore it can function like a form with defined filling order.
    """
    __metaclass__ = ViewMetaclass

    def __init__(self, parent, additional_context=None):
        super(View, self).__init__(parent)
        self.context = additional_context or {}
        self._widget_cache = {}

    def flush_widget_cache(self):
        # Recursively ...
        for view in self._views:
            view._widget_cache.clear()
        self._widget_cache.clear()

    @classmethod
    def widget_names(cls):
        result = []
        for key in dir(cls):
            value = getattr(cls, key)
            if isinstance(value, WidgetDescriptor):
                result.append((key, value))
        return [name for name, _ in sorted(result, key=lambda pair: pair[1]._seq_id)]

    @property
    def _views(self):
        return [view for view in self if isinstance(view, View)]

    @property
    def is_displayed(self):
        try:
            return super(View, self).is_displayed
        except LocatorNotImplemented:
            return True

    def move_to(self):
        try:
            return super(View, self).move_to()
        except LocatorNotImplemented:
            return None

    def fill(self, values):
        widget_names = self.widget_names()
        was_change = False
        for name, value in values.iteritems():
            if name not in widget_names:
                raise NameError('View {} does not have widget {}'.format(type(self).__name__, name))
            if value is None:
                continue

            widget = getattr(self, name)
            if widget.fill(value):
                was_change = True

        self.after_fill(was_change)
        return was_change

    def read(self):
        result = {}
        for widget_name in self.widget_names():
            widget = getattr(self, widget_name)
            try:
                value = widget.read()
            except (NotImplementedError, NoSuchElementException):
                continue

            result[widget_name] = value

        return result

    def after_fill(self, was_change):
        pass

    def __iter__(self):
        for widget_attr in self.widget_names():
            yield getattr(self, widget_attr)
