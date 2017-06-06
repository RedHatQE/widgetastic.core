# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""This module contains the base classes that are used to implement the more specific behaviour."""

import inspect
import re
import six
from six.moves import html_parser
from cached_property import cached_property
from collections import defaultdict, namedtuple
from copy import copy
from jsmin import jsmin
from selenium.webdriver.remote.file_detector import LocalFileDetector
from smartloc import Locator
from wait_for import wait_for

from .browser import Browser, BrowserParentWrapper
from .exceptions import (
    NoSuchElementException, LocatorNotImplemented, WidgetOperationFailed, DoNotReadThisWidget)
from .log import PrependParentsAdapter, create_widget_logger, logged, call_sig
from .utils import (
    Widgetable, Fillable, ParametrizedLocator, ConstructorResolvable, attributize_string,
    normalize_space)
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


def process_parameters(parent_obj, args, kwargs):
    """Processes the widget input parameters - checks if args or kwarg values are parametrized."""
    new_args = []
    for arg in args:
        if isinstance(arg, ConstructorResolvable):
            new_args.append(arg.resolve(parent_obj))
        else:
            new_args.append(arg)

    new_kwargs = {}
    for k, v in kwargs.items():
        if isinstance(v, ConstructorResolvable):
            new_kwargs[k] = v.resolve(parent_obj)
        else:
            new_kwargs[k] = v

    return new_args, new_kwargs


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

            args, kwargs = process_parameters(obj, self.args, kwargs)
            if issubclass(self.klass, ParametrizedView):
                # Shortcut, don't cache as the ParametrizedViewRequest is not the widget yet
                return ParametrizedViewRequest(obj, self.klass, *args, **kwargs)
            else:
                obj._widget_cache[self] = self.klass(obj, *args, **kwargs)
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


class WidgetIncluder(Widgetable):
    """Includes widgets from another widget. Useful for sharing pieces of code."""
    def __init__(self, widget_class):
        self.widget_class = widget_class

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.widget_class.__name__)


class IncludedWidget(object):
    def __init__(self, included_id, widget_name):
        self.included_id = included_id
        self.widget_name = widget_name

    def __get__(self, o, t=None):
        if o is None:
            return self

        return o._get_included_widget(self.included_id, self.widget_name)

    def __repr__(self):
        return '{}({}, {!r})'.format(type(self).__name__, self.included_id, self.widget_name)


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
        desc_name_mapping = {}
        included_widgets = []
        for base in bases:
            for key, value in six.iteritems(getattr(base, '_desc_name_mapping', {})):
                desc_name_mapping[key] = value
        for key, value in six.iteritems(attrs):
            if inspect.isclass(value) and issubclass(value, View):
                new_attrs[key] = WidgetDescriptor(value)
                desc_name_mapping[new_attrs[key]] = key
            elif isinstance(value, WidgetIncluder):
                included_widgets.append(value)
                # Now generate accessors for each included widget
                for widget_name in value.widget_class.cls_widget_names():
                    new_attrs[widget_name] = IncludedWidget(value._seq_id, widget_name)
            elif isinstance(value, Widgetable):
                new_attrs[key] = value
                desc_name_mapping[value] = key
                for widget in value.child_items:
                    if not isinstance(widget, (Widgetable, Widget)):
                        continue
                    desc_name_mapping[widget] = key
            elif key == 'fill':
                # handle fill() specifics
                new_attrs[key] = logged(log_args=True, log_result=True)(wrap_fill_method(value))
            elif key == 'read':
                # handle read() specifics
                new_attrs[key] = logged(log_result=True)(value)
            else:
                # Do nothing
                new_attrs[key] = value
        if 'ROOT' in new_attrs and '__locator__' not in new_attrs:
            # For handling the root locator of the View
            root = new_attrs['ROOT']
            if isinstance(root, ParametrizedLocator):
                new_attrs['__locator__'] = _gen_locator_root()
            else:
                new_attrs['__locator__'] = _gen_locator_meth(Locator(root))
        new_attrs['_included_widgets'] = tuple(sorted(included_widgets, key=lambda w: w._seq_id))
        new_attrs['_desc_name_mapping'] = desc_name_mapping
        return super(WidgetMetaclass, cls).__new__(cls, name, bases, new_attrs)


class Widget(six.with_metaclass(WidgetMetaclass, object)):
    """Base class for all UI objects.

    Does couple of things:

        * Ensures it gets instantiated with a browser or another widget as parent. If you create an
          instance in a class, it then creates a WidgetDescriptor which is then invoked on the
          instance and instantiates the widget with underlying browser.
        * Implements some basic interface for all widgets.
    """

    # Helper methods
    @staticmethod
    def include(*args, **kwargs):
        """Include another widget with exposing the given widget's widgets in this widget."""
        return WidgetIncluder(*args, **kwargs)

    def __new__(cls, *args, **kwargs):
        """Implement some typing saving magic.

        Unless you are passing a :py:class:`Widget` or :py:class:`widgetastic.browser.Browser`
        as a first argument which implies the instantiation of an actual widget, it will return
        :py:class:`WidgetDescriptor` instead which will resolve automatically inside of
        :py:class:`View` instance.

        This allows you a sort of Django-ish access to the defined widgets then.
        """
        if (args and isinstance(args[0], (Widget, Browser))) \
                or ('parent' in kwargs and isinstance(kwargs['parent'], (Widget, Browser))):
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
        self._widget_cache = {}
        self._initialized_included_widgets = {}

    def _get_included_widget(self, includer_id, widget_name):
        if includer_id not in self._initialized_included_widgets:
            for widget_includer in self._included_widgets:
                if widget_includer._seq_id == includer_id:
                    self._initialized_included_widgets[widget_includer._seq_id] =\
                        widget_includer.widget_class(self.parent, self.logger)
                    break
            else:
                raise ValueError('Could not find includer #{}'.format(includer_id))
        return getattr(self._initialized_included_widgets[includer_id], widget_name)

    def flush_widget_cache(self):
        """FLush the widget cache recursively for the whole View tree structure"""
        for widget in self.cached_sub_widgets:
            try:
                widget.flush_widget_cache()
            except AttributeError:
                # ParametrizedViewRequest does this, we can safely ignore that
                pass
        self._widget_cache.clear()
        for widget in self._initialized_included_widgets.values():
            try:
                widget.flush_widget_cache()
            except AttributeError:
                # ParametrizedViewRequest does this, we can safely ignore that
                pass
        self._initialized_included_widgets.clear()

    @classmethod
    def cls_widget_names(cls):
        """Returns a list of widget names in the order they were defined on the class.

        Returns:
            A :py:class:`list` of :py:class:`Widget` instances.
        """
        result = []
        for key in dir(cls):
            value = getattr(cls, key)
            if isinstance(value, Widgetable):
                result.append((key, value))
        for includer in cls._included_widgets:
            result.append((None, includer))
        presorted_widgets = sorted(result, key=lambda pair: pair[1]._seq_id)
        result = []
        for name, widget in presorted_widgets:
            if isinstance(widget, WidgetIncluder):
                result.extend(widget.widget_class.cls_widget_names())
            else:
                result.append(name)
        return tuple(result)

    @property
    def widget_names(self):
        """Returns a list of widget names in the order they were defined on the class.

        Returns:
            A :py:class:`list` of :py:class:`Widget` instances.
        """
        return self.cls_widget_names()

    @property
    def hierarchy(self):
        """Returns a list of widgets from the top level to this one."""
        if not isinstance(self.parent, Widget):
            return [self]
        else:
            return self.parent.hierarchy + [self]

    @property
    def locatable_parent(self):
        """If the widget has a parent that is locatable, returns it. Otherwise returns None"""
        for locatable in list(reversed(self.hierarchy))[1:]:
            if hasattr(locatable, '__locator__') and not getattr(locatable, 'INDIRECT', False):
                return locatable
        else:
            return None

    @property
    def browser(self):
        """Returns the instance of parent browser.

        If the view defines ``__locator__`` or ``ROOT`` then a new wrapper is created that injects
        the ``parent=``

        Returns:
            :py:class:`widgetastic.browser.Browser` instance

        Raises:
            :py:class:`ValueError` when the browser is not defined, which is an error.
        """
        try:
            super_browser = self.parent.browser
            if hasattr(self, '__locator__') and not getattr(self, 'INDIRECT', False):
                # Wrap it so we have automatic parent injection
                return BrowserParentWrapper(self, super_browser)
            else:
                # This view has no locator, therefore just use the parent browser
                return super_browser
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

        For actual filling, please use :py:meth:`fill_with`. It offers richer interface for filling.

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

    def _process_fill_handler(self, handler):
        """Processes a given handler in the way that it is usable as a callable + its representation

        Handlers can come in variety of ways. Simplest thing is to pass a callable, it will get
        executed. The handler can also work with classes that mix in :py:class:`ClickableMixin`
        where they use the :py:meth:`CallableMixin.click` as the handler action. If you pass a
        string, it will first get resolved by getting it as an attribute of the instance. Then all
        abovementioned steps are tried.

        Args:
            handler: The handler. More explanation in the description of this method.

        Returns:
            A 2-tuple consisting of ``(action_callable, obj_for_repr)``. The ``obj_for_repr`` is an
            object that can be passed to a logger that uses ``%r``.
        """
        if isinstance(handler, six.string_types):
            try:
                handler = getattr(self, handler)
            except AttributeError:
                raise TypeError('{} does not exist on {!r}'.format(handler, self))

        if isinstance(handler, ClickableMixin):
            return (handler.click, handler)
        elif callable(handler):
            return (handler, handler)
        else:
            raise TypeError('Fill handler must be callable or clickable.')

    def fill_with(self, value, on_change=None, no_change=None):
        """Method to fill the widget, especially usable when filling in forms.

        Args:
            value: Value to fill - gets passed to :py:meth:`fill`
            on_change: Optional handler to be executed when there was a change. See
                :py:meth`_process_fill_handler` for details
            no_change: Optional handler to be executed when there was no change. See
                :py:meth`_process_fill_handler` for details

        Returns:
            Whether there was any change. Same as :py:meth:`fill`.
        """
        changed = self.fill(value)
        if changed:
            if on_change is not None:
                action, rep = self._process_fill_handler(on_change)
                self.logger.info('invoking after fill on_change=%r', rep)
                action()
        else:
            if no_change is not None:
                action, rep = self._process_fill_handler(no_change)
                self.logger.info('invoking after fill no_change=%r', rep)
                action()
        return changed

    @property
    def sub_widgets(self):
        """Returns all sub-widgets of this widget.

        Returns:
            A :py:class:`list` of :py:class:`Widget`
        """
        return [getattr(self, widget_name) for widget_name in self.widget_names]

    @property
    def cached_sub_widgets(self):
        """Returns all cached sub-widgets of this widgets.

        Returns:
            A :py:class:`list` of :py:class:`Widget`
        """
        return [
            getattr(self, widget_name)
            for widget_name in self.widget_names
            # Grab the descriptor
            if getattr(type(self), widget_name) in self._widget_cache]

    @property
    def width(self):
        return self.browser.size_of(self, parent=self.parent)[0]

    @property
    def height(self):
        return self.browser.size_of(self, parent=self.parent)[1]

    def __iter__(self):
        """Allows iterating over the widgets on the view."""
        for widget_attr in self.widget_names:
            yield getattr(self, widget_attr)


def _gen_locator_meth(loc):
    def __locator__(self):  # noqa
        return loc
    return __locator__


def _gen_locator_root():
    def __locator__(self):  # noqa
        return self.ROOT
    return __locator__


class View(Widget):
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
    INDIRECT = False

    def __init__(self, parent, logger=None, **kwargs):
        Widget.__init__(self, parent, logger=logger)
        self.context = kwargs.pop('additional_context', {})

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

    @property
    def is_displayed(self):
        """Overrides the :py:meth:`Widget.is_displayed`. The difference is that if the view does
        not have the root locator, it assumes it is displayed.

        Returns:
            :py:class:`bool`
        """
        try:
            return self.parent.browser.is_displayed(self)
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

        It will log any skipped fill items.
        It will log a warning if you pass any extra values for filling.

        Args:
            values: A dictionary of ``widget_name: value_to_fill``.

        Returns:
            :py:class:`bool` if the fill changed any value.
        """
        was_change = False
        self.before_fill(values)
        extra_keys = set(values.keys()) - set(self.widget_names)
        if extra_keys:
            self.logger.warning(
                'Extra values that have no corresponding fill fields passed: ',
                ', '.join(extra_keys))
        for name in self.widget_names:
            if name not in values or values[name] is None:
                if name not in values:
                    self.logger.debug(
                        'Skipping fill of %r because value was not specified', name)
                else:
                    self.logger.debug(
                        'Skipping fill of %r because value was None', name)
                continue

            widget = getattr(self, name)
            try:
                value = values[name]
                if widget.fill(value):
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
        for widget_name in self.widget_names:
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


class ParametrizedView(View):
    """View that needs parameters to be run."""
    PARAMETERS = ()

    @classmethod
    def all(cls, browser):
        """Method that returns tuples of parameters that correspond to PARAMETRS attribute.

        It is required for proper functionality of :py:meth:`read` so it knows the exact instances
        of the view.

        Returns:
            An iterable that contains tuples. Values in the tuples must map exactly to the keys in
            the PARAMETERS class attribute.
        """
        raise NotImplementedError('You need to implement the all() classmethod')


class ParametrizedViewRequest(object):
    def __init__(self, parent_object, view_class, *args, **kwargs):
        self.parent_object = parent_object
        self.view_class = view_class
        self.args = args
        self.kwargs = kwargs

    def __call__(self, *args, **kwargs):
        if len(args) > len(self.view_class.PARAMETERS):
            raise TypeError(
                'You passed more parameters than {} accepts'.format(self.view_class.__name__))
        param_dict = {}
        for passed_arg, required_arg in zip(args, self.view_class.PARAMETERS):
            param_dict[required_arg] = passed_arg
        for key, value in kwargs.items():
            if key not in self.view_class.PARAMETERS:
                raise TypeError('Unknown view parameter {}'.format(key))
            param_dict[key] = value

        for param in self.view_class.PARAMETERS:
            if param not in param_dict:
                raise TypeError(
                    'You did not pass the required parameter {} into {}'.format(
                        param, self.view_class.__name__))

        new_kwargs = copy(self.kwargs)
        if 'additional_context' not in self.kwargs:
            new_kwargs['additional_context'] = {}
        new_kwargs['additional_context'].update(param_dict)
        # And finally, set up a nice logger
        parent_logger = self.parent_object.logger
        current_name = self.view_class.__name__
        # Now add the params to the name so it is class_name(args)
        current_name += call_sig((), param_dict)  # no args because we process everything into dict
        if isinstance(parent_logger, PrependParentsAdapter):
            # If it already is adapter, then pull the logger itself out and append
            # the widget name
            widget_path = '{}/{}'.format(parent_logger.extra['widget_path'], current_name)
            parent_logger = parent_logger.logger
        else:
            # Seems like first in the line.
            widget_path = current_name

        new_kwargs['logger'] = create_widget_logger(widget_path, parent_logger)
        result = self.view_class(self.parent_object, *self.args, **new_kwargs)
        self.parent_object.child_widget_accessed(result)
        return result

    def __getitem__(self, int_or_slice):
        """Emulates list-like behaviour.

        Maps into the dict-like structure by utilizing all() to get the list of all items and then
        it picks the one selected by the list-like accessor. Supports both integers and slices.
        """
        all_items = self.view_class.all(self.parent_object.browser)
        items = all_items[int_or_slice]
        single = isinstance(int_or_slice, int)
        if single:
            items = [items]
        views = []
        for args in items:
            views.append(self(*args))

        if single:
            return views[0]
        else:
            return views

    def __iter__(self):
        for args in self.view_class.all(self.parent_object.browser):
            yield self(*args)

    def __len__(self):
        return len(self.view_class.all(self.parent_object.browser))

    def __getattr__(self, attr):
        raise AttributeError(
            'This is not an instance of {}. You need to call this object and pass the required '
            'parameters of the view.'.format(self.view_class.__name__))

    def read(self):
        # Special handling of the parametrized views
        all_presences = self.view_class.all(self.parent_object.browser)
        value = {}
        for param_tuple in all_presences:
            # For each presence store it in a dictionary
            args = param_tuple
            if len(param_tuple) < 2:
                # Single value - no tuple
                param_tuple = param_tuple[0]
            value[param_tuple] = self(*args).read()
        return value

    def fill(self, value):
        was_change = False
        if not isinstance(value, dict):
            raise ValueError('When filling parametrized view a dict is required')
        for param_tuple, fill_value in value.items():
            if not isinstance(param_tuple, tuple):
                param_tuple = (param_tuple, )
            if self(*param_tuple).fill(fill_value):
                was_change = True
        return was_change


class ClickableMixin(object):

    @logged()
    def click(self):
        return self.browser.click(self)


class GenericLocatorWidget(Widget, ClickableMixin):
    """A base class for any widgets with a locator.

    Clickable.

    Args:
        locator: Locator of the object ob the page.
    """
    ROOT = ParametrizedLocator('{@locator}')

    def __init__(self, parent, locator, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.locator = locator

    def __repr__(self):
        return '{}({!r})'.format(type(self).__name__, self.locator)


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


class Checkbox(BaseInput, ClickableMixin):
    """This widget represents the bogo-standard form checkbox.

    Args:
        name: If you want to look the input up by name, use this parameter, pass the name.
        id: If you want to look the input up by id, use this parameter, pass the id.
        locator: If you have specific locator, use it here.
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

    def __repr__(self):
        return '{}({!r}, {!r})'.format(type(self).__name__, self.parent, self.position)

    @property
    def column_name(self):
        """If there is a name associated with this column, return it. Otherwise returns None."""
        try:
            return self.row.position_to_column_name(self.position)
        except KeyError:
            return None

    @cached_property
    def widget(self):
        """Returns the associated widget if defined. If there is none defined, returns None."""
        args = ()
        kwargs = {}
        if self.column_name is None:
            if self.position not in self.table.column_widgets:
                return None
            wcls = self.table.column_widgets[self.position]
        else:
            if self.column_name not in self.table.column_widgets:
                return None
            wcls = self.table.column_widgets[self.column_name]

        # We cannot use WidgetDescriptor's facility for instantiation as it does caching and all
        # that stuff
        if isinstance(wcls, WidgetDescriptor):
            args = wcls.args
            kwargs = wcls.kwargs
            wcls = wcls.klass
        kwargs = copy(kwargs)
        if 'logger' not in kwargs:
            kwargs['logger'] = self.logger
        return wcls(self, *args, **kwargs)

    @property
    def text(self):
        return self.browser.text(self)

    @property
    def row(self):
        return self.parent

    @property
    def table(self):
        return self.row.table

    def read(self):
        """Reads the content of the cell. If widget is present and visible, it is read, otherwise
        the text of the cell is returned.
        """
        if self.widget is not None and self.widget.is_displayed:
            return self.widget.read()
        else:
            return self.text

    def fill(self, value):
        """Fills the cell with the value if the widget is present. If not, raises a TypeError."""
        if self.widget is not None:
            return self.widget.fill(value)
        else:
            raise TypeError('Cannot fill column {}, no widget'.format(self.column_name))


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

    @property
    def table(self):
        return self.parent

    def __repr__(self):
        return '{}({!r}, {!r})'.format(type(self).__name__, self.parent, self.index)

    def __locator__(self):
        loc = self.parent.ROW_AT_INDEX.format(self.index + 1)
        return self.browser.element(loc, parent=self.parent)

    def position_to_column_name(self, position):
        """Maps the position index into the column name (pretty)"""
        return self.table.index_header_mapping[position]

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.Column(self, item, logger=self.logger)
        elif isinstance(item, six.string_types):
            return self[self.table.header_index_mapping[self.table.ensure_normal(item)]]
        else:
            raise TypeError('row[] accepts only integers and strings')

    def __getattr__(self, attr):
        try:
            return self[self.table.ensure_normal(attr)]
        except KeyError:
            raise AttributeError('Cannot find column {} in the table'.format(attr))

    def __dir__(self):
        result = super(TableRow, self).__dir__()
        result.extend(self.table.attributized_headers.keys())
        return sorted(result)

    def __iter__(self):
        for i, header in enumerate(self.table.headers):
            yield header, self[i]

    def read(self):
        """Read the row - the result is a dictionary"""
        result = {}
        for i, (header, cell) in enumerate(self):
            if header is None:
                header = i
            result[header] = cell.read()
        return result

    def fill(self, value):
        """Row filling.

        Accepts either a dictionary or an iterable that can be zipped with headers to create a dict.
        """
        if isinstance(value, (list, tuple)):
            # make it a dict
            value = dict(zip(self.table.headers, value))
        elif not isinstance(value, dict):
            if self.table.assoc_column_position is None:
                raise ValueError(
                    'For filling rows with single value you need to specify assoc_column')
            value = {self.table.assoc_column_position: value}
        return any(self[key].fill(value) for key, value in value.items() if value is not None)


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
        # You can also look the rows up by their indices
        rows = view.table.rows((0, 'asdf'))  # First column has asdf exactly
        rows = view.table.rows((1, 'contains', 'asdf'))  # Second column contains asdf
        # The partial search methods are the same like for keywords.
        # You can add multiple tuple queries and also combine them with keyword search
        # You are also able to filter based on some row-based filters
        # Yield only those rows who have data-foo=bar in their tr:
        view.table.rows(_row__attr=('data-foo', 'bar'))
        # You can do it similarly for the other operations
        view.table.rows(_row__attr_startswith=('data-foo', 'bar'))
        view.table.rows(_row__attr_endswith=('data-foo', 'bar'))
        view.table.rows(_row__attr_contains=('data-foo', 'bar'))
        # First item in the tuple is the attribute name, second the operand of the operation.
        # It is perfectly possibly to combine these queries with other kinds

        # When you have a row, you can do these things.
        row[0]  # => gives you the first column cell in the row
        row['Column Name'] # => Gives you the column that is named "Column Name". Non-attributized
        row.column_name # => Gives you the column whose attributized name is "column_name"

        # Basic row column can give you text
        assert row.column_name.text == 'some text'
        # Or you can click at it
        assert row.column_name.click()

        # Table cells can contain widgets or whole groups of widgets:
        Table(locator, column_widgets={column_name_or_index: widget_class_or_definition, ...})
        # The on TableColumn instances you can access .widget
        # This is also taken into account with reading or filling
        # For filling such table, fill takes a list, one entry per row, goes from start
        table.fill([{'Column1': 'value1'}, ...])

        # You can also designate one column as "special" associative column using assoc_column
        # You can specify it with column name
        Table(locator, column_widgets={...}, assoc_column='Display Name')
        # Or by the column index
        Table(locator, column_widgets={...}, assoc_column=0)
        # When you use assoc_column, you can use dictionary instead of the list, which means that
        # you can pick the rows to fill by the value in given column.
        # The same example as previous article
        table.fill({'foo': {'Column1': 'value1'}})  # Given that the assoc_column column has 'foo'
                                                    # on that line

    If you subclass :py:class:`Table`, :py:class:`TableRow`, or :py:class:`TableColumn`, do not
    forget to update the :py:attr:`Table.Row` and :py:attr:`TableRow.Column` in order for the
    classes to use the correct class.

    Args:
        locator: A locator to the table ``<table>`` tag.
        column_widgets: A mapping to widgets that are present in cells. Keys signify column name,
            value is the widget definition.
        assoc_column: Index or name of the column used for associative filling.
    """
    ROWS = './tbody/tr[./td]|./tr[not(./th) and ./td]'
    HEADER_IN_ROWS = './tbody/tr[1]/th'
    HEADERS = './thead/tr/th|./tr/th' + '|' + HEADER_IN_ROWS
    ROW_AT_INDEX = './tbody/tr[{0}]|./tr[not(./th)][{0}]'

    Row = TableRow

    def __init__(self, parent, locator, column_widgets=None, assoc_column=None, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.locator = locator
        self.column_widgets = column_widgets or {}
        self.assoc_column = assoc_column

    def __repr__(self):
        return '{}({!r}, column_widgets={!r})'.format(
            type(self).__name__, self.locator, self.column_widgets)

    def __locator__(self):
        return self.locator

    def clear_cache(self):
        for item in [
                'headers', 'attributized_headers', 'header_index_mapping', 'index_header_mapping',
                'assoc_column_position']:
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

    def ensure_normal(self, name):
        """When you pass string in, it ensures it comes out as non-attributized string."""
        if name in self.attributized_headers:
            return self.attributized_headers[name]
        else:
            return name

    @cached_property
    def attributized_headers(self):
        """Contains mapping between attributized headers and pretty headers"""
        return {attributize_string(h): h for h in self.headers if h is not None}

    @cached_property
    def header_index_mapping(self):
        """Contains mapping between header name (pretty) and position index."""
        return {h: i for i, h in enumerate(self.headers) if h is not None}

    @cached_property
    def index_header_mapping(self):
        """Contains mapping between hposition index and header name (pretty)."""
        return {i: h for h, i in self.header_index_mapping.items()}

    @cached_property
    def assoc_column_position(self):
        """Returns the position of the column specified as associative. If not specified, None
        returned.
        """
        if self.assoc_column is None:
            return None
        elif isinstance(self.assoc_column, int):
            return self.assoc_column
        elif isinstance(self.assoc_column, six.string_types):
            if self.assoc_column in self.attributized_headers:
                header = self.attributized_headers[self.assoc_column]
            elif self.assoc_column in self.headers:
                header = self.assoc_column
            else:
                raise ValueError(
                    'Could not find the assoc_value={!r} in headers'.format(self.assoc_column))
            return self.header_index_mapping[header]
        else:
            raise TypeError(
                'Wrong type passed for assoc_column= : {}'.format(type(self.assoc_column).__name__))

    def __getitem__(self, at_index):
        if not isinstance(at_index, int):
            raise TypeError('table indexing only accepts integers')
        return self.Row(self, at_index, logger=self.logger)

    def row(self, *extra_filters, **filters):
        return list(self.rows(*extra_filters, **filters))[0]

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

    def map_column(self, column):
        if isinstance(column, int):
            return column
        else:
            try:
                return self.header_index_mapping[self.attributized_headers[column]]
            except KeyError:
                try:
                    return self.header_index_mapping[column]
                except KeyError:
                    raise NameError('Could not find column {!r} in the table'.format(column))

    @cached_property
    def _is_header_in_body(self):
        return len(self.browser.elements(self.HEADER_IN_ROWS, parent=self)) > 0

    def rows(self, *extra_filters, **filters):
        if not (filters or extra_filters):
            return self._all_rows()
        else:
            return self._filtered_rows(*extra_filters, **filters)

    def _all_rows(self):
        for row_pos in range(len(self.browser.elements(self.ROWS, parent=self))):
            row_pos = row_pos if not self._is_header_in_body else row_pos + 1
            yield self.Row(self, row_pos, logger=self.logger)

    def _filtered_rows(self, *extra_filters, **filters):
        # Pre-process the filters
        processed_filters = defaultdict(list)
        regexp_filters = []
        row_filters = []
        for filter_column, filter_value in six.iteritems(filters):
            if filter_column.startswith('_row__'):
                row_filters.append((filter_column.split('__', 1)[-1], filter_value))
                continue
            if '__' in filter_column:
                column, method = filter_column.rsplit('__', 1)
            else:
                column = filter_column
                method = None
                if isinstance(filter_value, re._pattern_type):
                    regexp_filters.append((self.map_column(column), filter_value))
                    continue

            processed_filters[self.map_column(column)].append((method, filter_value))

        for argfilter in extra_filters:
            if not isinstance(argfilter, (tuple, list)):
                raise TypeError('Wrong type passed into tuplefilters (expected tuple or list)')
            if len(argfilter) == 2:
                # Column / string match
                column, value = argfilter
                method = None
                if isinstance(value, re._pattern_type):
                    regexp_filters.append((self.map_column(column), value))
                    continue
            elif len(argfilter) == 3:
                # Column / method / string match
                column, method, value = argfilter
            else:
                raise ValueError(
                    'tuple filters can only be (column, string) or (column, method, string)')

            processed_filters[self.map_column(column)].append((method, value))

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

        # Row query
        row_parts = []
        for row_action, row_value in row_filters:
            row_action = row_action.lower()
            if row_action.startswith('attr'):
                try:
                    attr_name, attr_value = row_value
                except ValueError:
                    raise ValueError(
                        'When passing _row__{}= into the row filter, you must pass it a 2-tuple'
                        .format(row_action))
                if row_action == 'attr_startswith':
                    row_parts.append('starts-with(@{}, {})'.format(attr_name, quote(attr_value)))
                elif row_action == 'attr':
                    row_parts.append('@{}={}'.format(attr_name, quote(attr_value)))
                elif row_action == 'attr_endswith':
                    row_parts.append(
                        ('substring(@{attr}, '
                         'string-length(@{attr}) - string-length({value}) + 1)={value}').format(
                            attr=attr_name,
                            value='normalize-space({value})'.format(value=quote(attr_value))))
                elif row_action == 'attr_contains':
                    row_parts.append('contains(@{}, {})'.format(attr_name, quote(attr_value)))
                else:
                    raise ValueError('Unsupported action {}'.format(row_action))
            else:
                raise ValueError('Unsupported action {}'.format(row_action))

        if query_parts and row_parts:
            query = './/tr[{}][{}]'.format(' and '.join(row_parts), ' and '.join(query_parts))
        elif query_parts:
            query = './/tr[{}]'.format(' and '.join(query_parts))
        elif row_parts:
            query = './/tr[{}]'.format(' and '.join(row_parts))
        else:
            # When using ONLY regexps, we might see no query_parts, therefore default query
            query = self.ROWS

        # Preload the rows to prevent stale element exceptions
        rows = []
        for row_element in self.browser.elements(query, parent=self):
            row_pos = self._get_number_preceeding_rows(row_element)
            row_pos = row_pos if not self._is_header_in_body else row_pos + 1
            rows.append(
                self.Row(self, row_pos, logger=self.logger))

        for row in rows:
            if regexp_filters:
                for regexp_column, regexp_filter in regexp_filters:
                    if regexp_filter.search(row[regexp_column].text) is None:
                        break
                else:
                    yield row
            else:
                yield row

    def read(self):
        """Reads the table. Returns a list, every item in the list is contents read from the row."""
        if self.assoc_column_position is None:
            return [row.read() for row in self]
        else:
            result = {}
            for row in self:
                row_read = row.read()
                try:
                    key = row_read.pop(self.header_index_mapping[self.assoc_column_position])
                except KeyError:
                    try:
                        key = row_read.pop(self.assoc_column_position)
                    except KeyError:
                        raise ValueError(
                            'The assoc_column={!r} could not be retrieved'.format(
                                self.assoc_column))
                if key in result:
                    raise ValueError('Duplicate value for {}={!r}'.format(key, result[key]))
                result[key] = row_read
            return result

    def fill(self, value):
        """Fills the table, accepts list which is dispatched to respective rows."""
        if isinstance(value, dict):
            if self.assoc_column_position is None:
                raise TypeError('In order to support dict you need to specify assoc_column')
            return any(
                self.row((self.assoc_column_position, key)).fill(fill_value)
                for key, fill_value
                in six.iteritems(value))
        else:
            if not isinstance(value, (list, tuple)):
                value = [value]
            return any(row.fill(value) for row, value in zip(self, value))


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
        opt = self.browser.element(
            ".//option[normalize-space(.)={}]".format(quote(normalize_space(text))),
            parent=self)
        return self.browser.get_attribute("value", opt)

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


class ConditionalSwitchableView(Widgetable):
    """Conditional switchable view implementation.

    This widget proxy is useful when you have a form whose parts displayed depend on certain
    conditions. Eg. when you select certain value from a dropdown, one form is displayed next,
    when other value is selected, a different form is displayed next. This widget proxy is designed
    to register those multiple views and then upon accessing decide which view to use based on the
    registration conditions.

    The resulting widget proxy acts similarly like a nested view (if you use view of course).

    Example:

        .. code-block:: python

            class SomeForm(View):
                foo = Input('...')
                action_type = Select(name='action_type')

                action_form = ConditionalSwitchableView(reference='action_type')

                # Simple value matching. If Action type 1 is selected in the select, use this view.
                # And if the action_type value does not get matched, use this view as default
                @action_form.register('Action type 1', default=True)
                class ActionType1Form(View):
                    widget = Widget()

                # You can use a callable to declare the widget values to compare
                @action_form.register(lambda action_type: action_type == 'Action type 2')
                class ActionType2Form(View):
                    widget = Widget()

                # With callable, you can use values from multiple widgets
                @action_form.register(
                    lambda action_type, foo: action_type == 'Action type 2' and foo == 2)
                class ActionType2Form(View):
                    widget = Widget()

        You can see it gives you the flexibility of decision based on the values in the view.

    Args:
        reference: For using non-callable conditions, this must be specified. Specifies the name of
            the widget whose value will be used for comparing non-callable conditions.
    """
    def __init__(self, reference=None):
        self.reference = reference
        self.registered_views = []
        self.default_view = None

    @property
    def child_items(self):
        return [
            descriptor
            for _, descriptor
            in self.registered_views
            if isinstance(descriptor, WidgetDescriptor)]

    def register(self, condition, default=False, widget=None):
        """Register a view class against given condition.

        Args:
            condition: Condition check for switching to appropriate view. Can be callable or
                non-callable. If callable, then callable parameters are resolved as values from
                widgets resolved by the argument name, then the callable is invoked with the params.
                If the invocation result is truthy, that view class is used. If it is a non-callable
                then it is compared with the value read from the widget specified as ``reference``.
            default: If no other condition matches any registered view, use this one. Can only be
                specified for one registration.
            widget: In case you do not want to use this as a decorator, you can pass the widget
                class or instantiated widget as this parameter.
        """
        def view_process(cls_or_descriptor):
            if not (
                    isinstance(cls_or_descriptor, WidgetDescriptor) or
                    (inspect.isclass(cls_or_descriptor) and issubclass(cls_or_descriptor, Widget))):
                raise TypeError(
                    'Unsupported object registered into the selector (!r})'.format(
                        cls_or_descriptor))
            self.registered_views.append((condition, cls_or_descriptor))
            if default:
                if self.default_view is not None:
                    raise TypeError('Multiple default views specified')
                self.default_view = cls_or_descriptor
            # We explicitly return None
            return None
        if widget is None:
            return view_process
        else:
            return view_process(widget)

    def __get__(self, o, t):
        if o is None:
            return self

        condition_arg_cache = {}
        for condition, cls_or_descriptor in self.registered_views:
            if not callable(condition):
                # Compare it to a known value (if present)
                if self.reference is None:
                    # No reference to check against
                    raise TypeError(
                        'reference= not set so you cannot use non-callables as conditions')
                else:
                    if self.reference not in condition_arg_cache:
                        try:
                            condition_arg_cache[self.reference] = getattr(o, self.reference).read()
                        except AttributeError:
                            raise TypeError(
                                'Wrong widget name specified as reference=: {}'.format(
                                    self.reference))
                    if condition == condition_arg_cache[self.reference]:
                        view_object = cls_or_descriptor
                        break
            else:
                # Parse the callable's args and inject the correct args
                c_args, c_varargs, c_keywords, c_defaults = inspect.getargspec(condition)
                if c_varargs or c_keywords or c_defaults:
                    raise TypeError('You can only use simple arguments in lambda conditions')
                arg_values = []
                for arg in c_args:
                    if arg not in condition_arg_cache:
                        try:
                            condition_arg_cache[arg] = getattr(o, arg).read()
                        except AttributeError:
                            raise TypeError(
                                'Wrong widget name specified as parameter {}'.format(arg))
                    arg_values.append(condition_arg_cache[arg])

                if condition(*arg_values):
                    view_object = cls_or_descriptor
                    break
        else:
            if self.default_view is not None:
                view_object = self.default_view
            else:
                raise ValueError('Could not find a corresponding registered view.')
        if inspect.isclass(view_object):
            view_class = view_object
        else:
            view_class = type(view_object)
        o.logger.info('Picked %s', view_class.__name__)
        if isinstance(view_object, Widgetable):
            # We init the widget descriptor here
            return view_object.__get__(o, t)
        else:
            return view_object(o, additional_context=o.context)
