# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""This module contains some supporting classes."""

import re
import six
import string
import time
from cached_property import cached_property
from six import wraps
from smartloc import Locator
from threading import Lock
from selenium.common.exceptions import StaleElementReferenceException

from . import xpath, log


class Widgetable(object):
    """A base class that should be a base class of anything that can be or act like a Widget."""
    #: Sequential counter that gets incremented on each Widgetable creation
    _seq_cnt = 0
    #: Lock that makes the :py:attr:`_seq_cnt` increment thread safe
    _seq_cnt_lock = Lock()

    def __new__(cls, *args, **kwargs):
        o = super(Widgetable, cls).__new__(cls)
        with Widgetable._seq_cnt_lock:
            o._seq_id = Widgetable._seq_cnt
            Widgetable._seq_cnt += 1
        return o

    @property
    def child_items(self):
        """If you implement your own class based on :py:class:`Widgetable`, you need to override
        this property.

        This property tells the widget processing system all instances of
        :py:class:`WidgetDescriptor` that this object may provide. That system then in turn makes
        sure that the appropriate entries in name/descriptor mapping are in place so when the
        descriptor gets instantiated, it can find its name in the mapping, making the instantiation
        possible.
        """
        return []


class Version(object):
    """Version class based on :py:class:`distutils.version.LooseVersion`

    Has improved handling of the suffixes and such things.
    """
    #: List of possible suffixes
    SUFFIXES = ('nightly', 'pre', 'alpha', 'beta', 'rc')
    #: An autogenereted regexp from the :py:attr:`SUFFIXES`
    SUFFIXES_STR = "|".join(r'-{}(?:\d+(?:\.\d+)?)?'.format(suff) for suff in SUFFIXES)
    #: Regular expression that parses the main components of the version (not suffixes)
    component_re = re.compile(r'(?:\s*(\d+|[a-z]+|\.|(?:{})+$))'.format(SUFFIXES_STR))
    suffix_item_re = re.compile(r'^([^0-9]+)(\d+(?:\.\d+)?)?$')

    def __init__(self, vstring):
        self.parse(vstring)

    def __hash__(self):
        return hash(self.vstring)

    def parse(self, vstring):
        if vstring is None:
            raise ValueError('Version string cannot be None')
        elif isinstance(vstring, (list, tuple)):
            vstring = ".".join(map(str, vstring))
        elif vstring:
            vstring = str(vstring).strip()
        if vstring in ('master', 'latest', 'upstream'):
            vstring = 'master'

        components = list(filter(lambda x: x and x != '.', self.component_re.findall(vstring)))
        # Check if we have a version suffix which denotes pre-release
        if components and components[-1].startswith('-'):
            self.suffix = components[-1][1:].split('-')    # Chop off the -
            components = components[:-1]
        else:
            self.suffix = None
        for i in range(len(components)):
            try:
                components[i] = int(components[i])
            except ValueError:
                pass

        self.vstring = vstring
        self.version = components

    @cached_property
    def normalized_suffix(self):
        """Turns the string suffixes to numbers. Creates a list of tuples.

        The list of tuples is consisting of 2-tuples, the first value says the position of the
        suffix in the list and the second number the numeric value of an eventual numeric suffix.

        If the numeric suffix is not present in a field, then the value is 0
        """
        numberized = []
        if self.suffix is None:
            return numberized
        for item in self.suffix:
            suff_t, suff_ver = self.suffix_item_re.match(item).groups()
            if suff_ver is None or len(suff_ver) == 0:
                suff_ver = 0.0
            else:
                suff_ver = float(suff_ver)
            suff_t = self.SUFFIXES.index(suff_t)
            numberized.append((suff_t, suff_ver))
        return numberized

    @classmethod
    def latest(cls):
        """Returns a specific ``latest`` version which always evaluates as newer."""
        try:
            return cls._latest
        except AttributeError:
            cls._latest = cls('latest')
            return cls._latest

    @classmethod
    def lowest(cls):
        """Returns a specific ``lowest`` version which always evaluates as older.

        You shall use this value in your :py:class:`VersionPick` dictionaries to match the oldest
        possible version of the product.
        """
        try:
            return cls._lowest
        except AttributeError:
            cls._lowest = cls('lowest')
            return cls._lowest

    def __str__(self):
        return self.vstring

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, repr(self.vstring))

    def __lt__(self, other):
        try:
            if not isinstance(other, Version):
                other = Version(other)
        except Exception:
            raise ValueError('Cannot compare Version to {}'.format(type(other).__name__))

        if self == other:
            return False
        elif self == self.latest() or other == self.lowest():
            return False
        elif self == self.lowest() or other == self.latest():
            return True
        else:
            # Start deciding on versions
            if self.version < other.version:
                return True
            # Use suffixes to decide
            elif self.suffix is None and other.suffix is None:
                # No suffix, the same
                return False
            elif self.suffix is None:
                # This does not have suffix but the other does so this is "newer"
                return False
            elif other.suffix is None:
                # This one does have suffix and the other does not so this one is older
                return True
            else:
                # Both have suffixes, so do some math
                return self.normalized_suffix < other.normalized_suffix

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    def __eq__(self, other):
        try:
            if not isinstance(other, type(self)):
                other = Version(other)
            return (
                self.version == other.version and self.normalized_suffix == other.normalized_suffix)
        except Exception:
            return False

    def __contains__(self, ver):
        """Enables to use ``in`` expression for :py:meth:`Version.is_in_series`.

        Example:
            ``"5.5.5.2" in Version("5.5") returns ``True``

        Args:
            ver: Version that should be checked if it is in series of this version. If
                :py:class:`str` provided, it will be converted to :py:class:`Version`.
        """
        try:
            return Version(ver).is_in_series(self)
        except Exception:
            return False

    def is_in_series(self, series):
        """This method checks whether the version belongs to another version's series.

        Eg.: ``Version("5.5.5.2").is_in_series("5.5")`` returns ``True``

        Args:
            series: Another :py:class:`Version` to check against. If string provided, will be
                converted to :py:class:`Version`
        """

        if not isinstance(series, Version):
            series = Version(series)
        if self in {self.lowest(), self.latest()}:
            if series == self:
                return True
            else:
                return False
        return series.version == self.version[:len(series.version)]

    def series(self, n=2):
        """Returns the series (first ``n`` items) of the version

        Args:
            n: How many version components to include.

        Returns:
            :py:class:`str`
        """
        return ".".join(self.vstring.split(".")[:n])


class ConstructorResolvable(object):
    """Base class for objects that should be resolvable inside constructors of Widgets etc."""

    def resolve(self, parent_object):
        raise NotImplementedError(
            'You need to implement .resolve(parent_object) on {}'.format(type(self).__name__))


class VersionPick(Widgetable, ConstructorResolvable):
    """A class that implements the version picking functionality.

    Basic usage is a descriptor in which you place instances of :py:class:`VersionPick` in a view.
    Whenever is this instance accessed from an instance, it automatically picks the correct variant
    based on product_version defined in the :py:class:`widgetastic.browser.Browser`.

    You can also use this separately using the :py:meth:`pick` method.

    Example:

    .. code-block:: python

        class MyView(View):
            something_version_dependent = VersionPick({
                '1.0.0': Foo('bar'),
                '2.5.0': Bar('baz'),
            })

    This sample will resolve the correct (Foo or Bar) kind of item and returns it.

    Args:
        version_dict: Dictionary of ``version_introduced: item``
    """

    #: This variable specifies the class that is used for version comparisons. You can replace it
    #: with your own if the new class can be used in </> comparison.
    VERSION_CLASS = Version

    def __init__(self, version_dict):
        if not version_dict:
            raise ValueError('Passed an empty version pick dictionary.')
        self.version_dict = version_dict

    def __repr__(self):
        return '{}({})'.format(type(self).__name__, repr(self.version_dict))

    @property
    def child_items(self):
        return self.version_dict.values()

    def pick(self, version):
        """Selects the appropriate value for given version.

        Args:
            version: A :py:class:`Version` or anything that :py:class:`Version` can digest.

        Returns:
            A value from the version dictionary.
        """
        # convert keys to Versions
        v_dict = {self.VERSION_CLASS(k): v for k, v in self.version_dict.items()}
        versions = v_dict.keys()
        if not isinstance(version, self.VERSION_CLASS):
            version = self.VERSION_CLASS(version)
        sorted_matching_versions = sorted([v for v in versions if v <= version], reverse=True)
        if sorted_matching_versions:
            return v_dict.get(sorted_matching_versions[0])
        else:
            raise ValueError(
                'When trying to version pick {!r} in {!r}, matching version was not found'.format(
                    version, versions))

    def __get__(self, o, type=None):
        if o is None:
            # On a class, therefore not resolving
            return self

        result = self.pick(o.browser.product_version)
        if isinstance(result, Widgetable):
            # Resolve it instead of the class
            return result.__get__(o)
        else:
            return result

    def resolve(self, parent_object):
        return self.__get__(parent_object)


class Fillable(object):
    @classmethod
    def coerce(cls, o):
        """This method serves as a processor for filling values.

        When you are filling values inside widgets and views, I bet you will quickly realize that
        filling basic values like strings or numbers is not enough. This method allows a potential
        fillable implement :py:meth:`as_fill_value` to return a basic value that represents the
        object in the UI

        Args:
            o: Object to be filled in the :py:class:`widgetastic.widget.View` or
                :py:class:`widgetastic.widget.Widget`

        Returns:
            Whatever is supposed to be filled in the widget.
        """
        if isinstance(o, cls):
            return o.as_fill_value()
        else:
            return o

    def as_fill_value(self):
        raise NotImplementedError('Descendants of Fillable must implement .as_fill_value method!')


class ParametrizedString(ConstructorResolvable):
    """Class used to generate strings based on the context passed to the view.

    Useful for parametrized views.

    They are a descriptor, so the :py:class:`ParametrizedString` instance materializes as a string
    upon accessing on an instance.

    Supported filters:

        See :py:attribute:`OPERATIONS`

    Sample strings:

    .. code-block:: python

        "foo"           # No resolution, returns a string
        "foo-{xyz}"     # if xyz=bar in the view context data, then the result is foo-bar
        "foo-{@xyz}"    # Same as the preceeding string, just the xyz is looked up as view attribute
        "//a[@id={@boo|quote}]"  # Same as preceeding, but quote the value per XPath specifications
        '//a[@id={"vm-{@boo}"|quote}]'  # Same as preceding, use double quotes to use maximum of
                                        # single level nesting if you need to use the value in
                                        # conjuntion with a constant or another value

    The last example demonstrated is a sort of workaround for the fact there is no suitable XPath
    processing and manipulating library in Python. It is not recommended to exploit that use case
    further. If you need more than what the last use case provides, you will be better off creating
    a property to generate the required string.

    You can use the functionality of :py:func:`nested_getattr` - the reference of parameters on the
    object (``@param_name``) also supports nesting, so you can access a child or parent value, like
    ``{@parent/something}``. The dots are replaced with forward slashes because python ``.format``
    does not support dots.

    Args:
        template: String template in ``.format()`` format,
    """

    OPERATIONS = {
        'quote': xpath.quote,
        'lower': lambda s: s.lower(),
        'upper': lambda s: s.upper(),
        'title': lambda s: s.title(),
    }

    def __init__(self, template):
        self.template = template
        formatter = string.Formatter()
        self.format_params = {}
        for _, param_name, _, _ in formatter.parse(self.template):
            if param_name is None:
                continue
            param = param_name.split('|', 1)
            if len(param) == 1:
                self.format_params[param_name] = (param[0], ())
            else:
                context_var_name = param[0]
                ops = param[1].split('|')
                self.format_params[param_name] = (context_var_name, tuple(ops))

    def resolve(self, view):
        """Resolve the parametrized string like on a view."""
        format_dict = {}
        for format_key, (context_name, ops) in self.format_params.items():
            if context_name.startswith('"') and context_name.endswith('"'):
                param_value = ParametrizedString(context_name[1:-1]).resolve(view)
            else:
                try:
                    if context_name.startswith('@'):
                        attr_name = context_name[1:]
                        param_value = nested_getattr(view, attr_name.split('/'))
                        if isinstance(param_value, Locator):
                            # Check if it is a locator. We want to pull the string out of it
                            param_value = param_value.locator
                    else:
                        param_value = view.context[context_name]
                except AttributeError:
                    if context_name.startswith('@'):
                        raise AttributeError(
                            'Parameter {} is not present in the object'.format(context_name))
                    else:
                        raise TypeError('Parameter class must be defined on a view!')
                except KeyError:
                    raise AttributeError(
                        'Parameter {} is not present in the context'.format(context_name))
            for op in ops:
                try:
                    op_callable = self.OPERATIONS[op]
                except KeyError:
                    raise NameError('Unknown operation {} for {}'.format(op, format_key))
                else:
                    param_value = op_callable(param_value)

            format_dict[format_key] = param_value

        return self.template.format(**format_dict)

    def __get__(self, o, t=None):
        if o is None:
            return self

        return self.resolve(o)


class ParametrizedLocator(ParametrizedString):
    """:py:class:`ParametrizedString` modified to return instances of :py:class:`smartloc.Locator`
    """
    def __get__(self, o, t=None):
        result = super(ParametrizedLocator, self).__get__(o, t)
        if isinstance(result, ParametrizedString):
            return result
        else:
            return Locator(result)


class Parameter(ParametrizedString):
    """Class used to expose a context parameter as an object attribute.

    Usage:

    .. code-block:: python

        class Foo(SomeView):
            my_arg = Parameter('my_arg')


        view = Foo(browser, additional_context={'my_arg': 1})
        assert view.my_arg == 1

    Args:
        param: Name of the param.
    """
    def __init__(self, param):
        super(Parameter, self).__init__('{' + param + '}')


def _prenormalize_text(text):
    """Makes the text lowercase and removes all characters that are not digits, alphas, or spaces"""
    # _'s represent spaces so convert those to spaces too
    return re.sub(r"[^a-z0-9 ]", "", text.strip().lower().replace('_', ' '))


def _replace_spaces_with(text, delim):
    """Contracts spaces into one character and replaces it with a custom character."""
    return re.sub(r"\s+", delim, text)


def attributize_string(text):
    """Converts a string to a lowercase string containing only letters, digits and underscores.

    Usable for eg. generating object key names.
    The underscore is always one character long if it is present.
    """
    return _replace_spaces_with(_prenormalize_text(text), '_')


def normalize_space(text):
    """Works in accordance with the XPath's normalize-space() operator.

    `Description <https://developer.mozilla.org/en-US/docs/Web/XPath/Functions/normalize-space>`_:

        *The normalize-space function strips leading and trailing white-space from a string,
        replaces sequences of whitespace characters by a single space, and returns the resulting
        string.*
    """
    return _replace_spaces_with(text.strip(), ' ')


def nested_getattr(o, steps):
    """Works exactly like :py:func:`getattr`, however it treats ``.`` as the resolution steps,
    therefore allowing you to grab an attribute across objects.

    Args:
        o: Object to get the attributes from.
        steps: A string with attribute name path separated by dots or a list.

    Returns:
        The value of required attribute.
    """
    if isinstance(steps, six.string_types):
        steps = steps.split('.')
    if not isinstance(steps, (list, tuple)):
        raise TypeError(
            'nested_getattr only accepts strings, lists, or tuples!, You passed {}'.format(
                type(steps).__name__))
    steps = [step.strip() for step in steps if step.strip()]
    if not steps:
        raise ValueError('steps are empty!')
    result = o
    for step in steps:
        result = getattr(result, step)
    return result


def deflatten_dict(d):
    """Expands nested dictionary from dot-separated string keys.

    Useful when one needs filling a nested view, this can reduce the visual nesting

    Turns this:

    .. code-block:: python

        {'a.b': 1}

    Into this:

    .. code-block:: python

        {'a': {'b': 1}}

    The conversion does not recusively follow dictionaries as values.

    Args:
        d: Dictionary

    Returns:
        A dictionary.
    """
    current_dict = {}
    for key, value in six.iteritems(d):
        if not isinstance(key, six.string_types):
            current_dict[key] = value
            continue
        local_dict = current_dict
        if isinstance(key, tuple):
            attrs = list(key)
        else:
            attrs = [x.strip() for x in key.split('.')]
        dict_lookup = attrs[:-1]
        attr_set = attrs[-1]
        for attr_name in dict_lookup:
            if attr_name not in local_dict:
                local_dict[attr_name] = {}
            local_dict = local_dict[attr_name]
        local_dict[attr_set] = value
    return current_dict


def crop_string_middle(s, length=32, cropper='...'):
    """Crops string by adding ... in the middle.

    Args:
        s: String.
        length: Length to crop to.

    Returns:
        Cropped string
    """
    if len(s) <= length:
        return s
    half = (length - len(cropper)) // 2
    return s[:half] + cropper + s[-half - 1:]


class partial_match(object):  # noqa
    """Use this to wrap values to be selected using partial matching in various objects.

    It proxies all ``get`` operations to the underlying ``item``.

    It also proxies ``dir`` so you get the exactly same result of :py:func:`dir` as if you did it
    on the wrapped object.

    """
    def __init__(self, item):
        self.item = item

    def __dir__(self):
        return dir(self.item)

    def __getattr__(self, attr):
        return getattr(self.item, attr)

    def __setattr__(self, attr, value):
        if attr == 'item':
            super(partial_match, self).__setattr__(attr, value)
        else:
            setattr(self.item, attr, value)

    def __repr__(self):
        return 'partial_match({!r})'.format(self.item)


class Ignore(object):
    """Descriptor which allows you to place Widget classes on another classes without touching.

    Usable eg. when you want to place a class as an attribute on another widgetastic class.
    Under normal circumstances, it would get instantiated. This decorator ensures the behaviour is
    ignored

    .. code-block:: python

        class SomeView(View):
            XYZ_VIEW_TYPE = Ignore(SomeOtherView)
            some_view = SomeOtherView

    This will ensure, that in this case ``XYZ_VIEW_TYPE`` won't be touched by Widgetastic, so it
    will be `SomeOtherView`` exactly. Whereas ``some_view`` will be recognized by the widget's
    metaclass and wrapped as :py:class:`widgetastic.widget.WidgetDescriptor` so it instantiates
    the view upon accessing.

    This descriptor also makes the value read-only. That should fit most of the use cases.

    Todo:
        Enable overriding the value somehow.

    Args:
        wt_class: The class to be placed on another class
    """

    def __init__(self, wt_class):
        self.wt_class = wt_class

    def __get__(self, o, t):
        return self.wt_class

    def __repr__(self):
        return 'Ignore({!r})'.format(self.wt_class)


def retry_stale_element(method):
    """ Aim of this decorator is to invoke some method one more time
       if it raised StaleElementReferenceException.

       This is necessary because there are cases when some element get updated by JS during attempt
       to work with it. There is no 100% robust solution to check that all JS are over on some page.
    """

    @wraps(method)
    def wrap(*args, **kwargs):
        attempts = 10
        for _ in range(attempts):
            try:
                return method(*args, **kwargs)
            except StaleElementReferenceException:
                time.sleep(0.5)
        else:
            raise StaleElementReferenceException("Couldn't handle it")

    return wrap


class FillContext(object):
    def __init__(self, parent, logger=None, **kwargs):
        self.parent = parent
        self.logger = logger or log.create_child_logger(getattr(self.parent, 'logger',
                                                                log.null_logger), 'fill')
        self.__dict__.update(kwargs)


class DefaultFillViewStrategy(object):
    """Used to fill view's widgets by default. It just calls fill for every passed widget

    """
    def __init__(self, respect_parent=False):
        # uses parent fill strategy if set and not overridden in current view
        self.respect_parent = respect_parent
        self._context = FillContext(parent=None)

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, context):
        self._context = context

    def fill_order(self, values):
        values = deflatten_dict(values)
        widget_names = self.context.parent.widget_names
        extra_keys = set(values.keys()) - set(widget_names)
        if extra_keys:
            self.context.logger.warning(
                'Extra values that have no corresponding fill fields passed: %s',
                ', '.join(extra_keys))
        return [(n, values[n]) for n in self.context.parent.widget_names
                if n in values and values[n] is not None]

    def do_fill(self, values):
        changes = []
        for widget_name, value in self.fill_order(values):
            widget = getattr(self.context.parent, widget_name)
            try:
                result = widget.fill(value)
                self.context.logger.debug("Filled %r to value %r with result %r",
                                          widget_name, value, result)
                changes.append(result)
            except NotImplementedError:
                self.context.logger.warning("Widget %r doesn't have fill method", widget_name)
                continue
        return any(changes)


class WaitFillViewStrategy(DefaultFillViewStrategy):
    """It is used to fill view's widgets where changes in one widget
    may cause another widget appear.

    New widgets may appear after some delay.
    So such strategy gives next widget some time to turn up.
    """
    def __init__(self, respect_parent=False, wait_widget='5s'):
        self.wait_widget = wait_widget
        super(WaitFillViewStrategy, self).__init__(respect_parent=respect_parent)

    def do_fill(self, values):
        changes = []
        for widget_name, value in self.fill_order(values):
            widget = getattr(self.context.parent, widget_name)
            try:
                widget.wait_displayed(timeout=self.wait_widget)
                result = widget.fill(value)
                self.context.logger.debug("Filled %r to value %r with result %r",
                                          widget_name, value, result)
                changes.append(result)
            except NotImplementedError:
                self.context.logger.warning("Widget %r doesn't have fill method", widget_name)
                continue
        return any(changes)
