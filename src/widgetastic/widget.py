# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""This module contains the base classes that are used to implement the more specific behaviour."""

import inspect
import six
from copy import copy
from smartloc import Locator
from wait_for import wait_for

from .browser import Browser
from .exceptions import NoSuchElementException, LocatorNotImplemented, WidgetOperationFailed
from .log import create_base_logger, logged
from .utils import Widgetable
from .xpath import quote


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
                logger = create_base_logger(
                    '{}/{}'.format(parent_logger.name, obj._desc_name_mapping[self]))
                kwargs['logger'] = logger
            except AttributeError:
                pass
            obj._widget_cache[self] = self.klass(obj, *self.args, **kwargs)
        return obj._widget_cache[self]

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


class Widget(object):
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
        self.logger = logger or create_base_logger(type(self).__name__)
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


class ViewMetaclass(type):
    """metaclass that ensures nested widgets' functionality from the declaration point of view.

    When you pass a ``ROOT`` class attribute, it is used to generate a ``__locator__`` method on
    the view that ensures the view is resolvable.
    """
    def __new__(cls, name, bases, attrs):
        new_attrs = {}
        desc_name_mapping = {}
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

    @logged(log_args=True, log_result=True)
    def fill(self, values):
        """Implementation of form filling.

        This method goes through all widgets defined on this view one by one and calls their
        ``fill`` methods appropriately.

        Args:
            values: A dictionary of ``widget_name: value_to_fill``.

        Returns:
            :py:class:`bool` if the fill changed any value.
        """
        widget_names = self.widget_names()
        was_change = False
        self.before_fill(values)
        for name, value in six.iteritems(values):
            if name not in widget_names:
                raise NameError('View {} does not have widget {}'.format(type(self).__name__, name))
            if value is None:
                continue

            widget = getattr(self, name)
            try:
                if widget.fill(value):
                    was_change = True
            except NotImplementedError:
                continue

        self.after_fill(was_change)
        return was_change

    @logged(log_result=True)
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
            except (NotImplementedError, NoSuchElementException):
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


class Text(Widget):
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

    @logged(log_result=True)
    def read(self):
        return self.browser.text(self)


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
    @logged(log_result=True)
    def read(self):
        return self.browser.get_attribute('value', self)

    @logged(log_args=True, log_result=True)
    def fill(self, value):
        current_value = self.read()
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

    @logged(log_result=True)
    def read(self):
        return self.browser.is_selected(self)

    @logged(log_args=True, log_result=True)
    def fill(self, value):
        value = bool(value)
        current_value = self.read()
        if value == current_value:
            return False
        else:
            self.click()
            if self.read() != value:
                # TODO: More verbose here
                raise WidgetOperationFailed('Failed to set the checkbox to requested value.')
            return True
