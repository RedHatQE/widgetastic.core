import pytest

from widgetastic.utils import nested_getattr
from widgetastic.utils import ParametrizedLocator
from widgetastic.utils import ParametrizedString
from widgetastic.utils import partial_match
from widgetastic.utils import Fillable
from widgetastic.utils import deflatten_dict
from widgetastic.utils import crop_string_middle
from widgetastic.utils import Ignore
from widgetastic.widget import View
from widgetastic.utils import ConstructorResolvable


def test_nested_getattr_wrong_type():
    with pytest.raises(TypeError):
        nested_getattr(object(), 654)


def test_nested_getattr_empty():
    with pytest.raises(ValueError):
        nested_getattr(object(), "")


def test_nested_getattr_single_level():
    class Obj:
        x = 1

    assert nested_getattr(Obj, "x") == 1
    assert nested_getattr(Obj, ["x"]) == 1


def test_nested_getattr_multi_level():
    class Obj:
        class foo:  # noqa
            class bar:  # noqa
                lol = "heh"

    assert nested_getattr(Obj, "foo.bar.lol") == "heh"
    assert nested_getattr(Obj, ["foo", "bar", "lol"]) == "heh"


def test_partial_match_wrapping():
    value = " foobar "
    wrapped = partial_match(value)

    assert dir(wrapped) == dir(value)

    assert wrapped.item is value

    assert wrapped.strip() == value.strip()


def test_parametrized_string_param_locator(browser):
    class MyView(View):
        ROOT = ParametrizedLocator("./foo/bar")

        test_str = ParametrizedString("{@ROOT}/baz")

    view = MyView(browser)
    assert view.ROOT.by == "xpath"
    assert view.ROOT.locator == "./foo/bar"
    assert view.test_str == "./foo/bar/baz"


def test_parametrized_string_nested(browser):
    class MyView(View):
        class child_item:  # noqa
            foo = "bar"

        class owner(View):  # noqa
            p_str1 = ParametrizedString("{@parent/child_item/foo}")

    view = MyView(browser)
    assert view.owner.p_str1 == "bar"


def test_constructor_resolvable_not_implemented():
    """Test ConstructorResolvable abstract method raises NotImplementedError."""
    resolvable = ConstructorResolvable()
    with pytest.raises(NotImplementedError, match="You need to implement .resolve"):
        resolvable.resolve(None)


def test_fillable_not_implemented():
    """Test Fillable abstract method."""

    class TestFillable(Fillable):
        pass

    with pytest.raises(NotImplementedError, match="must implement .as_fill_value method"):
        TestFillable().as_fill_value()


def test_parametrized_string_error_cases(browser):
    """Test ParametrizedString error handling"""

    # Test non-view object error
    param_str = ParametrizedString("{missing_param}")
    with pytest.raises(TypeError, match="Parameter class must be defined on a view"):
        param_str.resolve(object())  # Not a view object

    # Test missing attribute error
    class TestView(View):
        test_str = ParametrizedString("{@nonexistent_attr}")

    view = TestView(browser)
    with pytest.raises(AttributeError, match="Parameter @nonexistent_attr is not present"):
        _ = view.test_str

    # Test missing context parameter
    class TestView2(View):
        test_str = ParametrizedString("{missing_param}")

    view2 = TestView2(browser)
    with pytest.raises(
        AttributeError, match="Parameter missing_param is not present in the context"
    ):
        _ = view2.test_str

    # Test unknown operation
    class TestView3(View):
        test_str = ParametrizedString("{@ROOT|unknown_op}")
        ROOT = "test"

    view3 = TestView3(browser)
    with pytest.raises(NameError, match="Unknown operation unknown_op"):
        _ = view3.test_str


def test_deflatten_dict():
    """Test deflatten_dict with edge cases."""
    # Test usecase
    result1 = deflatten_dict({"a.b": 1})
    assert result1 == {"a": {"b": 1}}

    result2 = deflatten_dict({"a.b.c.d": 1})
    assert result2 == {"a": {"b": {"c": {"d": 1}}}}

    # Test non-string keys > as it is
    result3 = deflatten_dict({123: "numeric", None: "none_key"})
    assert result3 == {123: "numeric", None: "none_key"}

    # Test tuple keys > as it is
    result4 = deflatten_dict({("a", "b"): "tuple_key"})
    assert result4 == {("a", "b"): "tuple_key"}

    # Test complex tuple key that exercises line 825
    result5 = deflatten_dict({("level1", "level2", "level3"): "deep_tuple_value"})
    assert result5 == {("level1", "level2", "level3"): "deep_tuple_value"}


def test_crop_string_middle():
    """Test crop_string_middle usage."""

    # Test string shorter than length
    assert crop_string_middle("short", 10) == "short"

    # Test custom cropper
    long_string = "a" * 20
    result = crop_string_middle(long_string, 10, "<>")
    assert "<>" in result
    assert len(result) == 11


def test_partial_match_setattr_and_repr():
    """Test partial_match __setattr__ and __repr__."""

    class TestObj:
        value = 42

    obj = TestObj()
    wrapped = partial_match(obj)

    # Test __setattr__
    wrapped.value = 100
    assert obj.value == 100

    # Test __repr__
    repr_str = repr(wrapped)
    assert "partial_match" in repr_str


def test_ignore_repr():
    """Test Ignore __repr__ method"""

    class DummyClass:
        pass

    ignore_obj = Ignore(DummyClass)
    repr_str = repr(ignore_obj)
    assert "Ignore" in repr_str
    assert "DummyClass" in repr_str


def test_parametrized_string_comprehensive(browser):
    """Test ParametrizedString nested quote handling and filters"""

    # Test filters with pipe operator
    class TestView(View):
        test_attr = "Hello World"
        param_str = ParametrizedString("{@test_attr|lower}")

    view = TestView(browser)
    assert view.param_str == "hello world"

    # Test SmartLocator handling
    from widgetastic.locator import SmartLocator

    class TestView2(View):
        smart_loc = SmartLocator("//div[@id='test']")
        param_str = ParametrizedString("{@smart_loc}")

    view2 = TestView2(browser)
    # This should extract locator string from SmartLocator
    assert "//div[@id='test']" in view2.param_str
