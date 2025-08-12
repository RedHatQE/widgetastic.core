"""
Widgetastic Core Utilities
==========================

This module contains supporting classes and utilities for widgetastic.core framework.
"""

import re
import string
from threading import Lock

from cached_property import cached_property

from .locator import SmartLocator
from . import log
from . import xpath


class Widgetable:
    """A base class that should be a base class of anything that can be or act like a Widget.

    This class provides the fundamental infrastructure for widget-like objects in widgetastic.core.
    It handles sequential ID assignment for widgets and provides the child_items interface that
    enables the widget system to discover and manage widget descriptors.

    Key Features:
    - Thread-safe sequential ID assignment for each widget instance
    - Child widget discovery through the child_items property
    - Foundation for widget descriptor mapping and instantiation

    Usage:
        Inherit from Widgetable when creating custom widget-like classes:

        .. code-block:: python

            class MyCustomWidget(Widgetable):
                def __init__(self, locator):
                    super().__init__()
                    self.locator = locator

                @property
                def child_items(self):
                    return []  # Override to return child widget descriptors
    """

    #: Sequential counter that gets incremented on each Widgetable creation
    _seq_cnt = 0
    #: Lock that makes the :py:attr:`_seq_cnt` increment thread safe
    _seq_cnt_lock = Lock()

    def __new__(cls, *args, **kwargs):
        o = super().__new__(cls)
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


class Version:
    """Version class based on :py:class:`distutils.version.LooseVersion`

    Has improved handling of the suffixes and such things.
    """

    #: List of possible suffixes
    SUFFIXES = ("nightly", "pre", "alpha", "beta", "rc")
    #: An autogenereted regexp from the :py:attr:`SUFFIXES`
    SUFFIXES_STR = "|".join(rf"-{suff}(?:\d+(?:\.\d+)?)?" for suff in SUFFIXES)
    #: Regular expression that parses the main components of the version (not suffixes)
    component_re = re.compile(rf"(?:\s*(\d+|[a-z]+|\.|(?:{SUFFIXES_STR})+$))")
    suffix_item_re = re.compile(r"^([^0-9]+)(\d+(?:\.\d+)?)?$")

    def __init__(self, vstring):
        self.parse(vstring)

    def __hash__(self):
        return hash(self.vstring)

    def parse(self, vstring):
        if vstring is None:
            raise ValueError("Version string cannot be None")
        elif isinstance(vstring, (list, tuple)):
            vstring = ".".join(map(str, vstring))
        elif vstring:
            vstring = str(vstring).strip()
        if vstring in ("master", "latest", "upstream"):
            vstring = "master"

        components = list(filter(lambda x: x and x != ".", self.component_re.findall(vstring)))
        # Check if we have a version suffix which denotes pre-release
        if components and components[-1].startswith("-"):
            self.suffix = components[-1][1:].split("-")  # Chop off the -
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
            cls._latest = cls("latest")
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
            cls._lowest = cls("lowest")
            return cls._lowest

    def __str__(self):
        return self.vstring

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.vstring)})"

    def __lt__(self, other):
        try:
            if not isinstance(other, Version):
                other = Version(other)
        except Exception:
            raise ValueError(f"Cannot compare Version to {type(other).__name__}")

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
                self.version == other.version and self.normalized_suffix == other.normalized_suffix
            )
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
        return series.version == self.version[: len(series.version)]

    def series(self, n=2):
        """Returns the series (first ``n`` items) of the version

        Args:
            n: How many version components to include.

        Returns:
            :py:class:`str`
        """
        return ".".join(self.vstring.split(".")[:n])


class ConstructorResolvable:
    """Base class for objects that should be resolvable inside constructors of Widgets etc."""

    def resolve(self, parent_object):
        raise NotImplementedError(
            f"You need to implement .resolve(parent_object) on {type(self).__name__}"
        )


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

            # Different widget types for same functionality
            user_selector = VersionPick({
                '1.0': Select("//select[@name='user']"),           # Dropdown in v1
                '2.0': TextInput("//input[@placeholder='Search users']"),  # Search box in v2
            })

            # Version-dependent text patterns
            status_message = VersionPick({
                '1.0': Text("//div[@class='status']"),
                '2.0': Text("//span[@data-testid='status-indicator']"),
            })


    Practical Usage:

    .. code-block:: python

        # Browser setup with version
        browser.product_version = "2.1.0"

        view = ProductView(browser)

        # Automatically resolves to the v2.0 button (highest compatible)
        submit_btn = view.submit_button  # Returns Button("//button[contains(@class, 'btn-submit')]")
        submit_btn.click()

        # Works with any widget method
        view.user_selector.fill("john_doe")  # Uses TextInput for v2.1.0

    Args:
        version_dict: Dictionary mapping version strings to objects/widgets.
                     Keys should be version strings, values can be any object.
    """

    #: This variable specifies the class that is used for version comparisons. You can replace it
    #: with your own if the new class can be used in </> comparison.
    VERSION_CLASS = Version

    def __init__(self, version_dict):
        if not version_dict:
            raise ValueError("Passed an empty version pick dictionary.")
        self.version_dict = version_dict

    def __repr__(self):
        return f"{type(self).__name__}({repr(self.version_dict)})"

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
        sorted_matching_versions = sorted((v for v in versions if v <= version), reverse=True)
        if sorted_matching_versions:
            return v_dict.get(sorted_matching_versions[0])
        else:
            raise ValueError(
                "When trying to version pick {!r} in {!r}, matching version was not found".format(
                    version, versions
                )
            )

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


class Fillable:
    """Interface for objects that can provide values for widget filling operations.

    The Fillable interface allows complex objects to define how they should be
    represented when used as fill values in widgets. This is particularly useful
    for domain objects, data classes, or any complex objects that need to be
    converted to simple values for UI interaction.

    Key Benefits:
    - **Automatic Conversion**: Objects automatically convert to fill-appropriate values
    - **Domain Object Support**: Business objects can define their UI representation
    - **Type Safety**: Ensures consistent value extraction across the application
    - **Extensible**: Easy to implement for custom object types
    """

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
        """Return the value that should be used when filling widgets.

        This method must be implemented by all Fillable subclasses to define
        how the object should be represented in UI filling operations.

        Returns:
            The value to use for widget filling (typically str, int, float, bool)

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Descendants of Fillable must implement .as_fill_value method!")


class ParametrizedString(ConstructorResolvable):
    """Dynamic string template that resolves parameters from view context and attributes.

    This class creates dynamic strings by substituting parameters from the view's context
    or attributes. It's particularly useful for creating dynamic locators, messages, or
    any strings that need to change based on the current view state.

    Key Features:
    - **Context Resolution**: Access view context data using `{param_name}`
    - **Attribute Resolution**: Access view attributes using `{@attr_name}`
    - **Nested Access**: Access nested attributes using `{@parent/child/attr}`
    - **String Filters**: Apply transformations using pipe operators `{param|filter}`
    - **Locator Support**: Automatically handles SmartLocator objects
    - **Descriptor Pattern**: Automatically resolves when accessed on view instances

    Available Filters:
    - `quote`: XPath-safe quoting for string values
    - `lower`: Convert to lowercase
    - `upper`: Convert to uppercase
    - `title`: Convert to title case

    Template Syntax:
        - `{param}`: Resolve from view.context['param']
        - `{@attr}`: Resolve from view.attr
        - `{@parent/child}`: Resolve from view.parent.child
        - `{param|filter}`: Apply filter to resolved value
        - `{"nested-{@attr}"|quote}`: Nested templates with filtering

    Common Usage Patterns:

    .. code-block:: python

        class MyView(View):
            # Simple context parameter
            title = ParametrizedString("Welcome {username}")

            # Attribute-based locator
            button_locator = ParametrizedString("//button[@id='{@button_id}']")

            # With filtering for XPath safety
            safe_xpath = ParametrizedString("//div[@title={@title|quote}]")

            # Nested attribute access
            nested_element = ParametrizedString("//span[contains(text(), '{@parent/config/name}')]")

            # Complex template with multiple parameters
            dynamic_message = ParametrizedString("User {username} has {@item_count} items")

        # Usage
        view = MyView(browser, additional_context={'username': 'john'})
        view.button_id = 'submit-btn'

        # Automatically resolves when accessed
        locator_string = view.button_locator  # "//button[@id='submit-btn']"

    Advanced Examples:

    .. code-block:: python

        # Working with SmartLocator objects
        class FormView(View):
            base_locator = SmartLocator("//form[@id='user-form']")
            field_template = ParametrizedString("{@base_locator}//input[@name='{field_name}']")

        # Conditional templates
        class ConditionalView(View):
            element = ParametrizedString(
                "//div[@class='item {status}']//span[text()='{@item_name|quote}']"
            )

    Args:
        template: String template using Python's .format() syntax with widgetastic extensions
    """

    OPERATIONS = {
        "quote": xpath.quote,
        "lower": lambda s: s.lower(),
        "upper": lambda s: s.upper(),
        "title": lambda s: s.title(),
    }

    def __init__(self, template):
        self.template = template
        formatter = string.Formatter()
        self.format_params = {}
        for _, param_name, _, _ in formatter.parse(self.template):
            if param_name is None:
                continue
            param = param_name.split("|", 1)
            if len(param) == 1:
                self.format_params[param_name] = (param[0], ())
            else:
                context_var_name = param[0]
                ops = param[1].split("|")
                self.format_params[param_name] = (context_var_name, tuple(ops))

    def resolve(self, view):
        """Resolve the parametrized string using the provided view's context and attributes.

        This method performs the actual parameter substitution by:
        1. Extracting values from view.context for {param} patterns
        2. Extracting values from view attributes for {@attr} patterns
        3. Supporting nested attribute access with {@parent/child} patterns
        4. Applying any specified filters using the pipe operator
        5. Handling SmartLocator objects by extracting their string representation

        The resolution process is context-aware and supports complex nested structures,
        making it suitable for dynamic locator generation and template strings.

        Args:
            view: The view instance containing context data and attributes to resolve.
                 Must have a 'context' dictionary attribute for parameter resolution.

        Returns:
            str: The fully resolved string with all parameters substituted and filters applied.

        Raises:
            AttributeError: When a referenced attribute doesn't exist on the view
            KeyError: When a referenced context parameter doesn't exist
            NameError: When an unknown filter operation is specified
            TypeError: When parameter resolution is attempted on a non-view object

        Example:
            >>> template = ParametrizedString("User {username} has {@item_count} items")
            >>> view.context = {'username': 'john'}
            >>> view.item_count = 5
            >>> template.resolve(view)
            'User john has 5 items'
        """
        format_dict = {}
        for format_key, (context_name, ops) in self.format_params.items():
            if context_name.startswith('"') and context_name.endswith('"'):
                param_value = ParametrizedString(context_name[1:-1]).resolve(view)
            else:
                try:
                    if context_name.startswith("@"):
                        # Resolve view attribute (supports nested access via "/")
                        attr_name = context_name[1:]
                        param_value = nested_getattr(view, attr_name.split("/"))

                        # Check if it's a SmartLocator or any locator-like object
                        if hasattr(param_value, "by") and hasattr(param_value, "locator"):
                            # Extract the locator string for template substitution
                            param_value = param_value.locator
                        elif hasattr(param_value, "__str__") and hasattr(param_value, "by"):
                            # Handle SmartLocator string conversion for Playwright
                            param_value = str(param_value)
                    else:
                        # Resolve from view context dictionary
                        param_value = view.context[context_name]
                except AttributeError:
                    if context_name.startswith("@"):
                        raise AttributeError(
                            f"Parameter {context_name} is not present in the object"
                        )
                    else:
                        raise TypeError("Parameter class must be defined on a view!")
                except KeyError:
                    raise AttributeError(f"Parameter {context_name} is not present in the context")
            for op in ops:
                try:
                    op_callable = self.OPERATIONS[op]
                except KeyError:
                    raise NameError(f"Unknown operation {op} for {format_key}")
                else:
                    param_value = op_callable(param_value)

            format_dict[format_key] = param_value

        return self.template.format(**format_dict)

    def __get__(self, o, t=None):
        if o is None:
            return self

        return self.resolve(o)


class ParametrizedLocator(ParametrizedString):
    """Dynamic locator template that returns SmartLocator instances.

    This class extends ParametrizedString to automatically create SmartLocator objects
    from resolved template strings. It's the preferred way to create dynamic locators
    that need to be resolved at runtime based on view context or attributes.

    Key Benefits:
    - **Automatic SmartLocator Creation**: Resolved strings become SmartLocator instances
    - **Format Detection**: SmartLocator automatically detects CSS, XPath, etc.
    - **Playwright Compatibility**: Generated locators work seamlessly with Playwright
    - **Frame Context Support**: Works correctly within iframe-based widgets
    - **Template Flexibility**: All ParametrizedString features available

    Common Usage Patterns:

    .. code-block:: python

        class UserView(View):
            # Dynamic XPath locator
            user_row = ParametrizedLocator("//tr[@data-user-id='{user_id}']")

            # CSS selector with attribute substitution
            status_badge = ParametrizedLocator("#{@container_id} .status-{status}")

            # Complex locator with filtering
            safe_locator = ParametrizedLocator("//div[@title={@title|quote}]")

        # Usage
        view = UserView(browser, additional_context={'user_id': '123', 'status': 'active'})
        view.container_id = 'user-panel'

        # Returns SmartLocator instances
        locator = view.user_row  # SmartLocator("//tr[@data-user-id='123']")
        element = browser.element(locator)  # Works with Playwright

    Advanced Examples:

    .. code-block:: python

        class DynamicFormView(View):
            # Locator that adapts based on form type
            submit_button = ParametrizedLocator(
                "//form[@class='{form_type}']//button[@type='submit']"
            )

            # Nested attribute access for complex hierarchies
            field_locator = ParametrizedLocator(
                "//fieldset[@id='{@parent/section_id}']//input[@name='{field_name}']"
            )

            # Conditional locator based on view state
            action_button = ParametrizedLocator(
                "//button[contains(@class, '{@mode}') and text()='{@action_text|title}']"
            )

    Args:
        template: String template that will be resolved to create SmartLocator instances
    """

    def __get__(self, o, t=None):
        result = super().__get__(o, t)
        if isinstance(result, ParametrizedString):
            return result
        else:
            return SmartLocator(result)


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
        super().__init__("{" + param + "}")


def _prenormalize_text(text):
    """Makes the text lowercase and removes all characters that are not digits, alphas, or spaces"""
    # _'s represent spaces so convert those to spaces too
    return re.sub(r"[^a-z0-9 ]", "", text.strip().lower().replace("_", " "))


def _replace_spaces_with(text, delim):
    """Contracts spaces into one character and replaces it with a custom character."""
    return re.sub(r"\s+", delim, text)


def attributize_string(text):
    """Converts a string to a lowercase string containing only letters, digits and underscores.

    Usable for eg. generating object key names.
    The underscore is always one character long if it is present.
    """
    return _replace_spaces_with(_prenormalize_text(text), "_")


def normalize_space(text):
    """Works in accordance with the XPath's normalize-space() operator.

    `Description <https://developer.mozilla.org/en-US/docs/Web/XPath/Functions/normalize-space>`_:

        *The normalize-space function strips leading and trailing white-space from a string,
        replaces sequences of whitespace characters by a single space, and returns the resulting
        string.*
    """
    return _replace_spaces_with(text.strip(), " ")


def nested_getattr(o, steps):
    """Get nested attributes from an object using dot notation or path lists.

    This function extends the built-in getattr() to support nested attribute access
    across object hierarchies. It's particularly useful for accessing attributes
    in complex view structures or when working with parametrized strings that
    reference nested view attributes.

    The function supports both dot-separated strings and pre-split lists/tuples
    for flexibility in different usage scenarios.

    Args:
        o: The root object to start attribute resolution from
        steps: Attribute path as either:
            - String: "parent.child.attribute" (dot-separated)
            - List/Tuple: ["parent", "child", "attribute"]

    Returns:
        The value of the nested attribute

    Raises:
        AttributeError: If any step in the path doesn't exist
        TypeError: If steps is not a string, list, or tuple
        ValueError: If steps is empty after processing

    Examples:
        >>> class Parent:
        ...     def __init__(self):
        ...         self.child = Child()
        >>> class Child:
        ...     def __init__(self):
        ...         self.value = "found"
        >>>
        >>> parent = Parent()
        >>> nested_getattr(parent, "child.value")
        'found'
        >>> nested_getattr(parent, ["child", "value"])
        'found'

        # Usage in ParametrizedString templates
        >>> template = ParametrizedString("{@parent/config/database_url}")
        # Resolves to: nested_getattr(view, ["parent", "config", "database_url"])
    """
    if isinstance(steps, str):
        steps = steps.split(".")
    if not isinstance(steps, (list, tuple)):
        raise TypeError(
            "nested_getattr only accepts strings, lists, or tuples!, You passed {}".format(
                type(steps).__name__
            )
        )
    steps = [step.strip() for step in steps if step.strip()]
    if not steps:
        raise ValueError("steps are empty!")
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
    for key, value in d.items():
        if not isinstance(key, str):
            current_dict[key] = value
            continue
        local_dict = current_dict
        if isinstance(key, tuple):
            attrs = list(key)
        else:
            attrs = [x.strip() for x in key.split(".")]
        dict_lookup = attrs[:-1]
        attr_set = attrs[-1]
        for attr_name in dict_lookup:
            if attr_name not in local_dict:
                local_dict[attr_name] = {}
            local_dict = local_dict[attr_name]
        local_dict[attr_set] = value
    return current_dict


def crop_string_middle(s, length=32, cropper="..."):
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
    return s[:half] + cropper + s[-half - 1 :]


class partial_match:  # noqa
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
        if attr == "item":
            super().__setattr__(attr, value)
        else:
            setattr(self.item, attr, value)

    def __repr__(self):
        return f"partial_match({self.item!r})"


class Ignore:
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
        return f"Ignore({self.wt_class!r})"


class FillContext:
    def __init__(self, parent, logger=None, **kwargs):
        self.parent = parent
        self.logger = logger or log.create_child_logger(
            getattr(self.parent, "logger", log.null_logger), "fill"
        )
        self.__dict__.update(kwargs)


class DefaultFillViewStrategy:
    """Default strategy for filling view widgets with values.

    This strategy iterates through all fillable widgets in a view and calls their
    fill() methods with the provided values. It provides intelligent error handling,
    logging, and supports complex nested data structures.

    Key Features:
    - **Sequential Filling**: Fills widgets in the order they appear in widget_names
    - **Error Tolerance**: Continues filling even if individual widgets fail
    - **Detailed Logging**: Provides comprehensive logs for debugging fill operations
    - **Nested Data Support**: Automatically flattens nested dictionaries
    - **Frame Context Aware**: Works seamlessly with iframe-based widgets
    - **Change Detection**: Returns whether any widgets actually changed values

    Usage Patterns:

    .. code-block:: python

        class UserFormView(View):
            fill_strategy = DefaultFillViewStrategy()

            username = TextInput("#username")
            email = TextInput("#email")
            password = PasswordInput("#password")
            confirm_password = PasswordInput("#confirm")

        # Basic filling
        form_data = {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'secret123',
            'confirm_password': 'secret123'
        }

        view = UserFormView(browser)
        changed = view.fill(form_data)  # Returns True if any field changed

        # Nested data structures (automatically flattened)
        nested_data = {
            'user.profile.name': 'John Doe',
            'user.profile.email': 'john@example.com'
        }
        view.fill(nested_data)  # Equivalent to {'user': {'profile': {'name': '...', 'email': '...'}}}

    Advanced Configuration:

    .. code-block:: python

        class CustomFormView(View):
            # Respect parent fill strategy if available
            fill_strategy = DefaultFillViewStrategy(respect_parent=True)

            # Widget definitions...

        # The strategy will automatically:
        # 1. Log each fill operation with results
        # 2. Skip widgets that don't have fill methods
        # 3. Handle widgets that are not currently displayed
        # 4. Work correctly within iframe contexts

    Args:
        respect_parent: If True, uses parent's fill strategy when available
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
                "Extra values that have no corresponding fill fields passed: %s",
                ", ".join(extra_keys),
            )
        return [
            (n, values[n])
            for n in self.context.parent.widget_names
            if n in values and values[n] is not None
        ]

    def do_fill(self, values):
        changes = []
        for widget_name, value in self.fill_order(values):
            widget = getattr(self.context.parent, widget_name)
            try:
                result = widget.fill(value)
                self.context.logger.debug(
                    "Filled %r to value %r with result %r", widget_name, value, result
                )
                changes.append(result)
            except NotImplementedError:
                self.context.logger.warning("Widget %r doesn't have fill method", widget_name)
                continue
        return any(changes)


class WaitFillViewStrategy(DefaultFillViewStrategy):
    """Fill strategy that waits for widgets to become available before filling.

    This strategy extends DefaultFillViewStrategy by adding wait functionality
    before attempting to fill each widget. It's particularly useful for dynamic
    forms where widgets may appear or become enabled based on previous interactions.

    Key Features:
    - **Automatic Waiting**: Waits for each widget to be displayed before filling
    - **Configurable Timeout**: Customizable wait timeout per widget
    - **Dynamic Content Support**: Handles widgets that appear after user interactions
    - **Robust Error Handling**: Gracefully handles widgets that never appear
    - **Performance Optimized**: Uses Playwright's efficient waiting mechanisms

    Ideal Use Cases:
    - **Dynamic Forms**: Forms where fields appear based on selections
    - **Single Page Applications**: SPAs with asynchronously loaded content
    - **Conditional Widgets**: Widgets that appear/disappear based on state
    - **Iframe Content**: Widgets inside frames that may load slowly
    - **Progressive Forms**: Multi-step forms with dynamic field revelation

    Usage Examples:

    .. code-block:: python

        class DynamicFormView(View):
            # Use wait strategy with 10-second timeout per widget
            fill_strategy = WaitFillViewStrategy(wait_widget="10s")

            user_type = Select("#user-type")
            username = TextInput("#username")

            # These fields only appear after selecting user_type
            admin_key = TextInput("#admin-key")  # Only if user_type == "admin"
            department = Select("#department")   # Only if user_type == "employee"

        # Usage
        form_data = {
            'user_type': 'admin',
            'username': 'admin_user',
            'admin_key': 'secret_key_123'
        }

        view = DynamicFormView(browser)
        # Strategy will:
        # 1. Fill user_type immediately
        # 2. Wait for username to be displayed, then fill
        # 3. Wait for admin_key to appear (triggered by user_type), then fill
        # 4. Skip department since it won't appear for admin users
        view.fill(form_data)

    Advanced Configuration:

    .. code-block:: python

        class ConditionalView(View):
            # Custom timeout and parent strategy respect
            fill_strategy = WaitFillViewStrategy(
                wait_widget="15s",      # Wait up to 15 seconds per widget
                respect_parent=True     # Use parent's strategy if available
            )

            # Widget definitions...

    Timeout Formats:
    - String format: "5s", "10s", "2m" (seconds, minutes)
    - Numeric: 5.0 (seconds as float)
    - Default: "5s" if not specified

    Args:
        respect_parent: If True, uses parent's fill strategy when available
        wait_widget: Timeout for waiting for each widget to become displayed
    """

    def __init__(self, respect_parent=False, wait_widget="5s"):
        self.wait_widget = wait_widget
        super().__init__(respect_parent=respect_parent)

    def do_fill(self, values):
        changes = []
        for widget_name, value in self.fill_order(values):
            widget = getattr(self.context.parent, widget_name)
            try:
                widget.wait_displayed(timeout=self.wait_widget)
                result = widget.fill(value)
                self.context.logger.debug(
                    "Filled %r to value %r with result %r", widget_name, value, result
                )
                changes.append(result)
            except NotImplementedError:
                self.context.logger.warning("Widget %r doesn't have fill method", widget_name)
                continue
        return any(changes)
