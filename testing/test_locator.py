import pytest

from widgetastic.locator import (
    SmartLocator,
    LocatorStrategy,
    CSSStrategy,
    XPathStrategy,
    KwargsStrategy,
    LocatorObjectStrategy,
)


# === Core Functionality Tests ===


def test_instantiation_methods():
    """Test all valid ways to instantiate a locator."""
    # Tuple style
    assert SmartLocator("xpath", "//h1") == SmartLocator(by="xpath", locator="//h1")

    # Dictionary styles
    assert SmartLocator({"xpath": "//h1"}) == SmartLocator(by="xpath", locator="//h1")
    assert SmartLocator({"by": "css", "locator": "#foo"}) == SmartLocator(by="css", locator="#foo")

    # Keyword arguments
    assert SmartLocator(id="foo") == SmartLocator(by="id", locator="foo")
    assert SmartLocator(text="Click Me") == SmartLocator(by="text", locator="Click Me")


def test_nested_locator():
    """Test passing a SmartLocator instance creates equivalent locator."""
    loc = SmartLocator(xpath="//h1")
    loc2 = SmartLocator(loc)
    assert loc2 == loc
    assert loc2.by == "xpath"
    assert loc2.locator == "//h1"


def test_widget_locator_protocol():
    """Test objects with __locator__ method."""

    class MyWidget:
        def __init__(self, loc):
            self.loc = loc

        def __locator__(self):
            return self.loc

    # Test various return types from __locator__
    assert SmartLocator(MyWidget("#foo")) == SmartLocator(by="css", locator="#foo")
    assert SmartLocator(MyWidget({"xpath": "//h1"})) == SmartLocator(by="xpath", locator="//h1")
    assert SmartLocator(MyWidget(SmartLocator(by="id", locator="bar"))) == SmartLocator(
        by="id", locator="bar"
    )

    # Test nested widgets
    class DeepWidget:
        def __init__(self, inner):
            self.inner = inner

        def __locator__(self):
            return self.inner

    deep = DeepWidget(MyWidget(SmartLocator(text="Deep Click")))
    assert SmartLocator(deep) == SmartLocator(by="text", locator="Deep Click")


@pytest.mark.parametrize(
    ("locator_input", "expected_by", "expected_locator"),
    [
        # CSS Strategy - valid patterns
        ("div#id", "css", "div#id"),
        ("#id", "css", "#id"),
        (".class", "css", ".class"),
        ("span.class", "css", "span.class"),
        ("input#foo.bar.baz", "css", "input#foo.bar.baz"),
        # XPath Strategy - valid patterns
        ("//div", "xpath", "//div"),
        ("./div", "xpath", "./div"),
        (".//span", "xpath", ".//span"),
        ("(//a)[1]", "xpath", "(//a)[1]"),
        ("/html/body", "xpath", "/html/body"),
        # CSS fallback - strings that don't match CSS regex
        ("simple-text", "css", "simple-text"),
        ("button", "css", "button"),
        ("div span", "css", "div span"),  # spaces not in CSS regex
        ("input[type='text']", "css", "input[type='text']"),  # complex CSS
    ],
)
def test_string_detection_strategies(locator_input, expected_by, expected_locator):
    """Test automatic strategy detection for string inputs."""
    loc = SmartLocator(locator_input)
    assert loc.by == expected_by
    assert loc.locator == expected_locator


@pytest.mark.parametrize(
    ("locator_obj", "expected_string"),
    [
        # CSS - no prefix
        (SmartLocator(by="css", locator="#foo"), "#foo"),
        # Quoted engines
        (SmartLocator(by="text", locator="Submit"), 'text="Submit"'),
        (SmartLocator(by="id", locator="my-id"), 'id="my-id"'),
        (SmartLocator(by="role", locator="button"), 'role="button"'),
        (SmartLocator(by="data-testid", locator="test"), 'data-testid="test"'),
        (SmartLocator(by="placeholder", locator="Enter text"), 'placeholder="Enter text"'),
        (SmartLocator(by="title", locator="Tooltip"), 'title="Tooltip"'),
        (SmartLocator(by="name", locator="username"), 'name="username"'),
        # Non-quoted engines
        (SmartLocator(by="xpath", locator="//h1"), "xpath=//h1"),
    ],
)
def test_string_representation(locator_obj, expected_string):
    """Test __str__ method for all supported engines."""
    assert str(locator_obj) == expected_string


def test_representation_and_equality():
    """Test __repr__ and equality methods."""
    loc = SmartLocator(xpath="//h1")

    # Test __repr__
    assert repr(loc) == 'SmartLocator(by="xpath", locator="//h1")'

    # Test equality
    assert loc == SmartLocator(by="xpath", locator="//h1")
    assert loc != SmartLocator(css="//h1")
    assert loc != "//h1"  # different type


def test_locator_method():
    """Test __locator__ protocol implementation."""
    loc = SmartLocator(xpath="//h1")
    assert loc.__locator__() is loc


# === Error Handling Tests ===


@pytest.mark.parametrize(
    ("invalid_args", "invalid_kwargs", "expected_error", "error_message"),
    [
        # No arguments
        ((), {}, TypeError, None),
        # Too many positional arguments
        (("arg1", "arg2", "arg3"), {}, TypeError, "Provide a single value"),
        # Mixed args and kwargs
        (("arg1",), {"xpath": "//div"}, TypeError, "Provide a single value"),
        # Unsupported strategy
        ((), {"by": "foo", "locator": "bar"}, ValueError, "Unsupported locator strategy"),
        # Unresolvable types
        (([1, 2, 3],), {}, TypeError, "Could not resolve"),
        ((set(),), {}, TypeError, "Could not resolve"),
        ((lambda x: x,), {}, TypeError, "Could not resolve"),
        (({"key1": "val1", "key2": "val2"},), {}, TypeError, "Could not resolve"),  # multi-key dict
        (({},), {}, TypeError, "Could not resolve"),  # empty dict
        # Unsupported keyword arguments
        ((), {"unsupported": "bar"}, TypeError, "Could not resolve"),
    ],
)
def test_error_conditions(invalid_args, invalid_kwargs, expected_error, error_message):
    """Test all error conditions with appropriate messages."""
    with pytest.raises(expected_error, match=error_message or ""):
        SmartLocator(*invalid_args, **invalid_kwargs)


# === Strategy Classes Tests ===


def test_locator_strategy_base_class():
    """Test abstract base class raises NotImplementedError."""
    strategy = LocatorStrategy()
    with pytest.raises(NotImplementedError):
        strategy.create_locator("anything")


def test_css_strategy():
    """Test CSS strategy edge cases."""
    strategy = CSSStrategy()

    # Valid patterns already tested in parametrized test
    # Test invalid patterns return None
    invalid_inputs = ["just text", "//xpath", "div span", "", "123invalid", None, 123, [], {}]
    for invalid in invalid_inputs:
        assert strategy.create_locator(invalid) is None


def test_xpath_strategy():
    """Test XPath strategy edge cases."""
    strategy = XPathStrategy()

    # Valid patterns already tested in parametrized test
    # Test invalid patterns return None
    invalid_inputs = ["div", "#id", "text content", "", "   ", None, 123, [], {}]
    for invalid in invalid_inputs:
        assert strategy.create_locator(invalid) is None


def test_kwargs_strategy():
    """Test keyword arguments strategy comprehensively."""
    strategy = KwargsStrategy()

    # Test all supported engines with single-key dict format
    for engine in strategy.SUPPORTED_ENGINES:
        assert strategy.create_locator({engine: "value"}) == (engine, "value")

    # Test by/locator format
    assert strategy.create_locator({"by": "xpath", "locator": "//div"}) == ("xpath", "//div")

    # Test unsupported cases return None
    unsupported_cases = [
        {"by": "unsupported", "locator": "value"},  # unsupported engine
        {"unsupported": "value"},  # unsupported single key
        {"key1": "val1", "key2": "val2"},  # multiple keys
        "string",
        123,
        None,
        [],  # non-dict types
    ]
    for case in unsupported_cases:
        assert strategy.create_locator(case) is None


def test_locator_object_strategy():
    """Test locator object strategy."""
    strategy = LocatorObjectStrategy()
    strategy.locator_class = SmartLocator

    # Test with SmartLocator instance
    existing_locator = SmartLocator(xpath="//div")
    assert strategy.create_locator(existing_locator) == ("xpath", "//div")

    # Test with object having __locator__ method
    class MockWidget:
        def __locator__(self):
            return "#foo"

    assert strategy.create_locator(MockWidget()) == ("css", "#foo")

    # Test objects without __locator__ return None
    class PlainObject:
        pass

    non_locatable = [PlainObject(), "string", 123, None, []]
    for obj in non_locatable:
        assert strategy.create_locator(obj) is None
