# -*- coding: utf-8 -*-
import inspect
import six
import types
from copy import copy

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from smartloc import Locator
from wait_for import wait_for

from widgetastic.browser import Browser, BrowserParentWrapper
from widgetastic.exceptions import DoNotReadThisWidget, LocatorNotImplemented
from widgetastic.log import (create_child_logger, call_sig, logged, PrependParentsAdapter,
                             create_widget_logger)
from widgetastic.utils import (Fillable, ConstructorResolvable, ParametrizedString, Widgetable,
                               ParametrizedLocator, nested_getattr, deflatten_dict,
                               DefaultFillViewStrategy, FillContext)


def do_not_read_this_widget():
    """Call inside widget's read method in case you don't want it to appear in the data."""
    raise DoNotReadThisWidget('Do not read this widget.')


def wrap_fill_method(method):
    """Generates a method that automatically coerces the first argument as Fillable."""
    @six.wraps(method)
    def wrapped(self, value, *args, **kwargs):
        return method(self, Fillable.coerce(value), *args, **kwargs)

    return wrapped


def resolve_verpicks_in_method(method):
    """Generates a method that automatically resolves VersionPick attributes"""
    @six.wraps(method)
    def wrapped(self, *args, **kwargs):
        def resolve_arg(parent, arg):
            if (isinstance(arg, ConstructorResolvable) and not (
                    method.__name__ == '__new__' or
                    isinstance(arg, ParametrizedString) or
                    hasattr(method, 'skip_resolve'))):
                # 1. ParametrizedString is also ConstructorResolvable but
                # it should be resolved later in other place
                # 2. if method has skip_resolve attr, its arguments won't be automatically resolved
                # 3. __new__ doesn't require resolve
                return arg.resolve(parent)
            else:
                return arg

        if method.__name__ == '__init__':
            # __init__ doesn't have initialized self.parent.
            # So, we need to look for parent/browser in arguments
            if args and isinstance(args[0], (Widget, Browser)):
                parent = args[0]
            elif 'parent' in kwargs and isinstance(kwargs['parent'], (Widget, Browser)):
                parent = kwargs['parent']
            else:
                raise ValueError("parent isn't passed to init")
        else:
            parent = self

        new_args = [resolve_arg(parent, arg) for arg in args]
        new_kwargs = {key: resolve_arg(parent, value) for key, value in kwargs.items()}

        return method(self, *new_args, **new_kwargs)
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
        # TODO: WE can bring it back, popping out just for compatibility sake
        self.kwargs.pop('log_on_fill_unspecified', None)

    def __get__(self, obj, type=None):
        if obj is None:  # class access
            return self

        # Cache on WidgetDescriptor
        if self not in obj._widget_cache:
            kwargs = copy(self.kwargs)
            try:
                kwargs['logger'] = create_child_logger(obj.logger, obj._desc_name_mapping[self])
            except KeyError:
                kwargs['logger'] = obj.logger
            except AttributeError:
                pass

            args, kwargs = process_parameters(obj, self.args, kwargs)
            if issubclass(self.klass, ParametrizedView):
                # Shortcut, don't cache as the ParametrizedViewRequest is not the widget yet
                return ParametrizedViewRequest(obj, self.klass, *args, **kwargs)
            else:
                o = self.klass(obj, *args, **kwargs)
                o.parent_descriptor = self
                obj._widget_cache[self] = o
        widget = obj._widget_cache[self]
        obj.child_widget_accessed(widget)
        return widget

    def __repr__(self):
        return '{}{}'.format(self.klass.__name__, call_sig(self.args, self.kwargs))


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
    def __init__(self, widget_class, use_parent=False):
        self.widget_class = widget_class
        self.use_parent = use_parent

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.widget_class.__name__)


class IncludedWidget(object):
    def __init__(self, included_id, widget_name, use_parent):
        self.included_id = included_id
        self.widget_name = widget_name
        self.use_parent = use_parent

    def __get__(self, o, t=None):
        if o is None:
            return self

        return o._get_included_widget(self.included_id, self.widget_name, self.use_parent)

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
            for widget_includer in getattr(base, '_included_widgets', ()):
                included_widgets.append(widget_includer)
                for widget_name in widget_includer.widget_class.cls_widget_names():
                    new_attrs[widget_name] = IncludedWidget(widget_includer._seq_id, widget_name,
                                                            widget_includer.use_parent)

        for key, value in six.iteritems(attrs):
            if inspect.isclass(value) and issubclass(value, View):
                new_attrs[key] = WidgetDescriptor(value)
                desc_name_mapping[new_attrs[key]] = key
            elif isinstance(value, WidgetIncluder):
                included_widgets.append(value)
                # Now generate accessors for each included widget
                for widget_name in value.widget_class.cls_widget_names():
                    new_attrs[widget_name] = IncludedWidget(value._seq_id, widget_name,
                                                            value.use_parent)
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
            elif isinstance(value, types.FunctionType):
                # VP resolution wrapper, allows to resolve VersionPicks in all widget methods
                new_attrs[key] = resolve_verpicks_in_method(value)
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
          instance in a class, it then creates a :py:class:`WidgetDescriptor` which is then invoked
          on the instance and instantiates the widget with underlying browser.
        * Implements some basic interface for all widgets.

    If you are inheriting from this class, you **MUST ALWAYS** ensure that the inherited class
    has an init that always takes the ``parent`` as the first argument. You can do that on your
    own, setting the parent as ``self.parent`` or you can do something like this:

    .. code-block:: python

        def __init__(self, parent, arg1, arg2, logger=None):
            super(MyClass, self).__init__(parent, logger=logger)
            # or if you have somehow complex inheritance ...
            Widget.__init__(self, parent, logger=logger)
    """

    #: Default value for parent_descriptor
    parent_descriptor = None

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
        self.parent = parent
        if logger is None:
            self.logger = create_child_logger(parent.logger, type(self).__name__)
        elif isinstance(logger, PrependParentsAdapter):
            # The logger is already prepared
            self.logger = logger
        else:
            # We need a PrependParentsAdapter here.
            self.logger = create_widget_logger(type(self).__name__, logger)
        self.extra = ExtraData(self)
        self._widget_cache = {}
        self._initialized_included_widgets = {}

    def __element__(self):
        """Implement the logic of querying
        :py:class:`selenium.webdriver.remote.webelement.WebElement` from Selenium.

        It uses :py:meth:`__locator__` to retrieve the locator and then it looks up the WebElement
        on the parent's browser.

        If hte ``__locator__`` isbadly implemented and returns a ``WebElement`` instance, it returns
        it directly.

        You usually want this method to be intact.
        """
        try:
            locator = self.__locator__()
        except AttributeError:
            raise AttributeError(
                '__locator__() is not defined on {} class'.format(type(self).__name__))
        else:
            if isinstance(locator, WebElement):
                self.logger.warning(
                    '__locator__ of %s class returns a WebElement!', type(self).__name__)
                return locator
            else:
                return self.parent_browser.element(locator)

    def _get_included_widget(self, includer_id, widget_name, use_parent):
        if includer_id not in self._initialized_included_widgets:
            for widget_includer in self._included_widgets:
                if widget_includer._seq_id == includer_id:
                    parent = self if use_parent else self.parent
                    self._initialized_included_widgets[widget_includer._seq_id] =\
                        widget_includer.widget_class(parent, self.logger)
                    break
            else:
                raise ValueError('Could not find includer #{}'.format(includer_id))
        return getattr(self._initialized_included_widgets[includer_id], widget_name)

    def flush_widget_cache(self):
        """Flush the widget cache recursively for the whole :py:class:`Widget` tree structure.

        Do not use this unless you see glitches and ``StaleElementReferenceException``. Well written
        widgets should not need flushing.
        """
        for widget in self._widget_cache.values():
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
                # check the values of a VersionPick object are widgetable themselves
                if all([isinstance(item, Widgetable) for item in value.child_items]):
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
    def root_browser(self):
        return self.parent.root_browser

    @property
    def parent_browser(self):
        try:
            return self.locatable_parent.browser
        except AttributeError:
            # locatable_parent == None
            return self.root_browser

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
            if hasattr(self, '__locator__'):
                # Wrap it so we have automatic parent injection
                return BrowserParentWrapper(self, self.root_browser)
            else:
                # This view has no locator, therefore just use the parent browser
                return self.root_browser
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
    def wait_displayed(self, timeout='10s', delay=0.2):
        """Wait for the element to be displayed. Uses the :py:meth:`is_displayed`

        Args:
            timeout: If you want, you can override the default timeout here
            delay: override default delay for wait_for iterations
        """
        ret, _ = wait_for(lambda: self.is_displayed, timeout=timeout, delay=delay)
        return ret

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


class ClickableMixin(object):

    @logged()
    def click(self, handle_alert=None):
        """Click this widget

        Args:
            handle_alert: Special alert handling. None - no handling, True - accept, False - dismiss
        """
        self.browser.click(self, ignore_ajax=(handle_alert is not None))
        if handle_alert is not None:
            self.browser.handle_alert(cancel=not handle_alert, wait=2.0, squash=True)
            # ignore_ajax will not execute the ensure_page_safe plugin with True
            self.browser.plugin.ensure_page_safe()


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


class WTMixin(six.with_metaclass(WidgetMetaclass, object)):
    """Base class for mixins for views.

    Lightweight class that only has the bare minimum of what is required for widgetastic operation.

    Use this if you want to create mixins for views.
    """


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
            the widget whose value will be used for comparing non-callable conditions. Supports
            going across objects using ``.``.
        ignore_bad_reference: If this is enabled, then when the widget representing the reference
            is not displayed or otherwise broken, it will then use the default view.
    """
    def __init__(self, reference=None, ignore_bad_reference=False):
        self.reference = reference
        self.registered_views = []
        self.default_view = None
        self.ignore_bad_reference = ignore_bad_reference

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
                            ref_o = nested_getattr(o, self.reference)
                            if isinstance(ref_o, Widget):
                                ref_value = ref_o.read()
                            else:
                                ref_value = ref_o
                            condition_arg_cache[self.reference] = ref_value
                        except AttributeError:
                            raise TypeError(
                                'Wrong widget name specified as reference=: {}'.format(
                                    self.reference))
                        except NoSuchElementException:
                            if self.ignore_bad_reference:
                                # reference is not displayed? We are probably aware of this so skip.
                                continue
                            else:
                                raise
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
    #: Skip this view in the element lookup hierarchy
    INDIRECT = False
    fill_strategy = None

    def __init__(self, parent, logger=None, **kwargs):
        Widget.__init__(self, parent, logger=logger)
        self.context = kwargs.pop('additional_context', {})
        self.last_fill_data = None

        if not self.fill_strategy:
            if getattr(getattr(self.parent, 'fill_strategy', None), 'respect_parent', False):
                self.fill_strategy = self.parent.fill_strategy
            else:
                self.fill_strategy = DefaultFillViewStrategy()

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
            return super(View, self).is_displayed
        except (LocatorNotImplemented, AttributeError):
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

        It will store the fill value in :py:attr:`last_fill_data`. The data will be "deflattened" to
        ensure uniformity.

        Args:
            values: A dictionary of ``widget_name: value_to_fill``.

        Returns:
            :py:class:`bool` if the fill changed any value.
        """
        changed = []
        values = deflatten_dict(values)
        self.last_fill_data = values
        changed.append(self.before_fill(values))
        # there are some views like ConditionalView which are dynamically updated
        # it is necessary to pass current view at least for
        # name -> widget resolution right before fill and for logging
        self.fill_strategy.context = FillContext(parent=self)
        changed.append(self.fill_strategy.do_fill(values))
        a_fill = self.after_fill(any(changed))
        return a_fill if isinstance(a_fill, bool) else any(changed)

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

        If it returns None, the ``was_changed`` in :py:meth:`fill` does not change. If it returns a
        boolean, then on ``True`` it modifies the ``was_changed`` to True as well.

        Args:
            values: The same values that are passed to :py:meth:`fill`
        """
        pass

    def after_fill(self, was_change):
        """A hook invoked after all the widgets were filled.

        If it returns None, the ``was_changed`` in :py:meth:`fill` does not change. If it returns a
        boolean, that boolean will be returned as ``was_changed``.

        Args:
            was_change: :py:class:`bool` signalizing whether the :py:meth:`fill` changed anything,
        """
        pass


class ParametrizedView(View):
    """View that needs parameters to be run.

    In order to use this class, you need to specify parameters in the :py:attribute:`PARAMETERS`
    attribute.

    Then a parametrized view could be defined like this:

    .. code-block:: python

        class AView(View):
            # some widgets, .... etc

            class thing(ParametrizedView):
                PARAMETERS = ('thing_name', )
                ROOT = ParametrizedLocator('.//div[./h2[normalize-space(.)={thing_name|quote}]]')

                a_widget = SomeWidget()

        view = AView(browser)

    This will not work:

    .. code-block:: python

        view.thing.a_widget  # Throws an error

    You now need to pass the required parameter as an argument to the view. Just like a method:

    .. code-block:: python

        view.a_thing(thing_name='snafu').a_widget
        # Or alternatively positionally
        view.a_thing('snafu').a_widget

    This is enough to support the ``fill` interface. If you want to ``read`` the parametrized view
    as well, you need to implement some logic which tells it what aprameters are available. That
    is achieved by implementing an ``all`` classmethod on the parametrized view:

    .. code-block:: python

        # inside class thing(ParametrizedView):
        @classmethod
        def all(cls, browser):
            elements = browser.elements('some locator')
            # You then need to scavenge the values for PARAMETERS
            # ParametrizedView expects such format of parameters:
            return [  # List of all occurences of the parametrized group
                ('foo', )  # Tuple of all parameters that are necessary to look up the given group
                ('snafu', )
            ]

    There can be any number of parameters, but bear mind that all of them are required and ``all``
    must always return the same number of parameters for each group.

    When filling, remember the keys of the fill dictionary are the parameters. If there is only one
    parameter, it can just be the parameter itself. If there are multiple parameters for the groups,
    then a tuple is expected as a key, containing all the parameter values. The values of the
    dictionary are then passed into each parametrized group to be filled as an ordinary view.
    """

    #: Tuple of parameter names that this view takes.
    PARAMETERS = ()

    @classmethod
    def all(cls, browser):
        """Method that returns tuples of parameters that correspond to PARAMETERS attribute.

        It is required for proper functionality of :py:meth:`read` so it knows the exact instances
        of the view.

        Returns:
            An iterable that contains tuples. Values in the tuples must map exactly to the keys in
            the PARAMETERS class attribute.
        """
        raise NotImplementedError('You need to implement the all() classmethod')


class ParametrizedViewRequest(object):
    """An intermediate object handling the argument retrieval and subsequent correct view
    instantiation.

    See :py:class:`ParametrizedView` for more info.
    """
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
        new_kwargs['logger'] = create_child_logger(parent_logger, current_name)
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
