import pytest

from widgetastic.widget import View
from widgetastic.widget import Widget
from widgetastic.widget import WidgetDescriptor


def test_widget_correctly_collapses_to_descriptor(browser):
    assert isinstance(Widget(), WidgetDescriptor)
    assert isinstance(Widget(browser), Widget)
    assert isinstance(Widget(parent=browser), Widget)


def test_widget_browser(browser):
    w = Widget(browser)
    assert w.browser is browser


def test_widget_broken_browser(browser):
    w = Widget(browser)
    w.parent = object()

    with pytest.raises(ValueError):
        w.browser


def test_widget_with_parent_view(browser):
    class AView(View):
        w = Widget()

    view = AView(browser)
    assert view.w.parent_view is view


def test_widget_without_parent_view(browser):
    w = Widget(browser)

    assert w.parent_view is None


def test_widget_extra_data(browser):
    class AView(View):
        widget = Widget()

    view = AView(browser)
    assert not dir(view.extra)
    browser.extra_objects["testobject"] = 2
    assert dir(view.extra) == ["testobject"]
    assert view.extra.testobject == 2

    # Test missing extra object error
    with pytest.raises(AttributeError, match="Extra object 'missing' was not found"):
        view.extra.missing


def test_included_widgets(browser):
    class MyWidget(Widget):
        def __init__(self, parent, id, logger=None):
            Widget.__init__(self, parent, logger=logger)
            self.id = id

    class MyClass1(Widget):
        ham = MyWidget("ham")

    class MyClass2(Widget):
        beef = MyWidget("beef")

    class MyClass3(Widget):
        foo = MyWidget("foo")

        included1 = Widget.include(MyClass1)

        bar = MyWidget("bar")

        included2 = Widget.include(MyClass2)

    class MyClass4(Widget):
        alice = MyWidget("alice")

        included1 = Widget.include(MyClass3)

        bob = MyWidget("bob")

    assert MyClass3.cls_widget_names() == ("foo", "ham", "bar", "beef")
    assert MyClass4.cls_widget_names() == ("alice", "foo", "ham", "bar", "beef", "bob")

    testw = MyClass4(browser)
    assert isinstance(testw.alice, MyWidget)
    assert testw.alice.id == "alice"
    assert isinstance(testw.foo, MyWidget)
    assert testw.foo.id == "foo"
    assert isinstance(testw.ham, MyWidget)
    assert testw.ham.id == "ham"
    assert isinstance(testw.bar, MyWidget)
    assert testw.bar.id == "bar"
    assert isinstance(testw.beef, MyWidget)
    assert testw.beef.id == "beef"
    assert isinstance(testw.bob, MyWidget)
    assert testw.bob.id == "bob"


def test_widget_missing_includer_error(browser):
    """Test _get_included_widget error when includer not found."""
    widget = Widget(browser)
    with pytest.raises(ValueError, match="Could not find includer #999"):
        widget._get_included_widget(999, "test", False)


def test_flush_widget_cache_with_attribute_error(browser):
    """Test flush_widget_cache exception handling."""

    class MockWidget:
        def flush_widget_cache(self):
            raise AttributeError("test error")

    widget = Widget(browser)
    widget._widget_cache["key1"] = MockWidget()
    widget._initialized_included_widgets["key2"] = MockWidget()

    # Should handle AttributeErrors gracefully
    widget.flush_widget_cache()
    assert len(widget._widget_cache) == 0
    assert len(widget._initialized_included_widgets) == 0
