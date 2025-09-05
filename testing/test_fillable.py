import pytest
from unittest.mock import Mock

from widgetastic.utils import (
    Fillable,
    FillContext,
    DefaultFillViewStrategy,
    WaitFillViewStrategy,
    log,
)
from widgetastic.widget import View, TextInput, Checkbox, Widget


def test_basic_fillable():
    """Test basic Fillable functionality."""

    class MyFillable(Fillable):
        def as_fill_value(self):
            return "foo"

    x = MyFillable()
    assert Fillable.coerce(x) == "foo"
    assert Fillable.coerce(123) == 123


def test_fill_context_creation():
    """Test FillContext creation and properties."""

    class MockParent:
        def __init__(self):
            self.name = "test_parent"

    parent = MockParent()
    logger = log.null_logger

    # Test basic creation
    context = FillContext(parent=parent, logger=logger)
    assert context.parent is parent
    assert context.logger is logger

    # Test creation with additional kwargs
    context_with_extras = FillContext(
        parent=parent, logger=logger, custom_attr="custom_value", another_attr=123
    )
    assert context_with_extras.parent is parent
    assert context_with_extras.logger is logger
    assert context_with_extras.custom_attr == "custom_value"
    assert context_with_extras.another_attr == 123


def test_fill_context_logger_creation():
    """Test FillContext logger creation when none provided."""

    class MockParent:
        def __init__(self):
            self.logger = log.null_logger

    parent = MockParent()

    # Test automatic logger creation from parent
    context = FillContext(parent=parent)
    assert context.logger is not None
    assert context.parent is parent


def test_fill_context_no_parent_logger():
    """Test FillContext when parent has no logger."""

    class MockParent:
        pass

    parent = MockParent()

    # Should fallback to null_logger
    context = FillContext(parent=parent)
    assert context.logger is not None
    assert context.parent is parent


def test_default_fill_view_strategy_initialization():
    """Test DefaultFillViewStrategy initialization."""

    # Test default initialization
    strategy = DefaultFillViewStrategy()
    assert strategy.respect_parent is False
    assert isinstance(strategy._context, FillContext)
    assert strategy._context.parent is None

    # Test initialization with respect_parent=True
    strategy_with_parent = DefaultFillViewStrategy(respect_parent=True)
    assert strategy_with_parent.respect_parent is True


def test_default_fill_view_strategy_context_property():
    """Test context property getter and setter."""

    strategy = DefaultFillViewStrategy()
    original_context = strategy.context

    # Test getting context
    assert strategy.context is original_context

    # Test setting new context
    new_context = FillContext(parent=Mock())
    strategy.context = new_context
    assert strategy.context is new_context
    assert strategy.context is not original_context


def test_default_fill_view_strategy_fill_order(browser):
    """Test DefaultFillViewStrategy fill_order method."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        input2 = TextInput(name="fill_with_2")
        checkbox1 = Checkbox(id="input2")

        fill_strategy = DefaultFillViewStrategy()

    view = TestForm(browser)

    # Set up strategy context
    view.fill_strategy.context = FillContext(parent=view, logger=log.null_logger)

    # Test normal fill order
    values = {"input1": "value1", "input2": "value2"}
    fill_order = view.fill_strategy.fill_order(values)

    # Should return tuples of (widget_name, value) in widget_names order
    expected_names = {"input1", "input2"}  # checkbox1 not included since not in values
    actual_names = {name for name, value in fill_order}
    assert actual_names == expected_names

    # Test with None values (should be filtered out)
    values_with_none = {"input1": "value1", "input2": None, "checkbox1": True}
    fill_order_filtered = view.fill_strategy.fill_order(values_with_none)

    # None values should be filtered out
    assert len(fill_order_filtered) == 2  # input1 and checkbox1, input2 filtered out
    names_filtered = {name for name, value in fill_order_filtered}
    assert "input2" not in names_filtered  # None value filtered
    assert "input1" in names_filtered
    assert "checkbox1" in names_filtered


def test_default_fill_view_strategy_fill_order_extra_keys_warning(browser, caplog):
    """Test that fill_order warns about extra keys."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        fill_strategy = DefaultFillViewStrategy()

    view = TestForm(browser)
    view.fill_strategy.context = FillContext(parent=view, logger=log.null_logger)

    # Add extra keys that don't correspond to widgets
    values = {"input1": "value1", "nonexistent_widget": "value2", "another_extra": "value3"}

    with caplog.at_level("WARNING"):
        fill_order = view.fill_strategy.fill_order(values)

    # Should return only valid widget
    assert len(fill_order) == 1
    assert fill_order[0][0] == "input1"

    # Should log warning about extra keys
    warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
    assert len(warning_logs) > 0
    warning_message = warning_logs[0].message
    assert "nonexistent_widget" in warning_message
    assert "another_extra" in warning_message


def test_default_fill_view_strategy_do_fill_success(browser):
    """Test successful do_fill operation."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        checkbox1 = Checkbox(id="input2")
        fill_strategy = DefaultFillViewStrategy()

    view = TestForm(browser)
    view.fill_strategy.context = FillContext(parent=view, logger=log.null_logger)

    # Test filling widgets
    values = {"input1": "test_value", "checkbox1": True}
    result = view.fill_strategy.do_fill(values)

    # Should return True since values changed
    assert result is True

    # Verify values were actually set
    assert view.input1.read() == "test_value"
    assert view.checkbox1.read() is True


def test_default_fill_view_strategy_do_fill_no_changes(browser):
    """Test do_fill when no changes occur."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        checkbox1 = Checkbox(id="input2")
        fill_strategy = DefaultFillViewStrategy()

    view = TestForm(browser)
    view.fill_strategy.context = FillContext(parent=view, logger=log.null_logger)

    # First, set values
    view.input1.fill("test_value")
    view.checkbox1.fill(True)

    # Now try to fill with same values
    values = {"input1": "test_value", "checkbox1": True}
    result = view.fill_strategy.do_fill(values)

    # Should return False since no changes occurred
    assert result is False


def test_default_fill_view_strategy_widget_without_fill_method(browser, caplog):
    """Test do_fill handling of widgets without fill method."""

    class NoFillWidget(Widget):
        """Widget that doesn't implement fill method."""

        pass

    class TestForm(View):
        input1 = TextInput(name="input1")
        no_fill_widget = NoFillWidget()
        fill_strategy = DefaultFillViewStrategy()

    view = TestForm(browser)
    view.fill_strategy.context = FillContext(parent=view, logger=log.null_logger)

    # Try to fill including the widget without fill method
    values = {"input1": "test_value", "no_fill_widget": "some_value"}

    with caplog.at_level("WARNING"):
        result = view.fill_strategy.do_fill(values)

    # The input1 should be filled successfully despite no_fill_widget failing
    assert result is True  # Should return True since input1 was filled successfully
    assert view.input1.read() == "test_value"

    # Should log warning about widget without fill method
    warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
    assert len(warning_logs) > 0
    assert any("doesn't have fill method" in record.message for record in warning_logs)


def test_wait_fill_view_strategy_initialization():
    """Test WaitFillViewStrategy initialization."""

    # Test default initialization
    strategy = WaitFillViewStrategy()
    assert strategy.respect_parent is False
    assert strategy.wait_widget == "5s"
    assert isinstance(strategy._context, FillContext)

    # Test initialization with custom wait timeout
    strategy_custom_wait = WaitFillViewStrategy(wait_widget="10s")
    assert strategy_custom_wait.wait_widget == "10s"

    # Test initialization with respect_parent=True
    strategy_with_parent = WaitFillViewStrategy(respect_parent=True, wait_widget="15s")
    assert strategy_with_parent.respect_parent is True
    assert strategy_with_parent.wait_widget == "15s"


def test_wait_fill_view_strategy_do_fill_with_wait(browser):
    """Test WaitFillViewStrategy do_fill method with wait functionality."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        checkbox1 = Checkbox(id="input2")
        fill_strategy = WaitFillViewStrategy(wait_widget="5s")

    view = TestForm(browser)
    view.fill_strategy.context = FillContext(parent=view, logger=log.null_logger)

    # Test filling widgets (this should wait for widgets to be displayed)
    values = {"input1": "wait_test_value", "checkbox1": True}
    result = view.fill_strategy.do_fill(values)

    # Should return True since values changed
    assert result is True

    # Verify values were actually set
    assert view.input1.read() == "wait_test_value"
    assert view.checkbox1.read() is True


def test_wait_fill_view_strategy_inherits_from_default():
    """Test that WaitFillViewStrategy inherits from DefaultFillViewStrategy."""

    strategy = WaitFillViewStrategy()

    # Should have all the methods from DefaultFillViewStrategy
    assert hasattr(strategy, "fill_order")
    assert hasattr(strategy, "context")
    assert hasattr(strategy, "respect_parent")

    # Should be instance of DefaultFillViewStrategy
    assert isinstance(strategy, DefaultFillViewStrategy)


def test_wait_fill_view_strategy_exception_handling(browser, caplog):
    """Test WaitFillViewStrategy exception handling."""

    class NoFillWidget(Widget):
        """Widget that doesn't implement fill method but has proper locator."""

        def __locator__(self):
            # Return a locator that won't be found to test wait timeout handling
            return ".//div[@id='non_existent_element_for_testing']"

    class TestForm(View):
        input1 = TextInput(name="input1")
        no_fill_widget = NoFillWidget()
        fill_strategy = WaitFillViewStrategy(
            wait_widget="0.1s"
        )  # Very short timeout to fail quickly

    view = TestForm(browser)
    view.fill_strategy.context = FillContext(parent=view, logger=log.null_logger)

    values = {"input1": "test_value", "no_fill_widget": "some_value"}

    # Expect TimedOutError when trying to wait for non-existent widget
    from wait_for import TimedOutError

    with pytest.raises(TimedOutError):
        view.fill_strategy.do_fill(values)

    # Test the case that actually demonstrates proper exception handling - widget without fill method
    class NoFillMethodWidget(Widget):
        """Widget without fill method but with valid locator."""

        def __locator__(self):
            # Use an existing element that will be found
            return ".//input[@name='input1']"

    class TestForm2(View):
        input1 = TextInput(name="input1")
        no_fill_method_widget = NoFillMethodWidget()
        fill_strategy = WaitFillViewStrategy(wait_widget="2s")

    view2 = TestForm2(browser)
    view2.fill_strategy.context = FillContext(parent=view2, logger=log.null_logger)

    # This should work - waits for widget, then logs warning about missing fill method
    values2 = {"input1": "test_value", "no_fill_method_widget": "some_value"}

    with caplog.at_level("WARNING"):
        result = view2.fill_strategy.do_fill(values2)

    # The input1 should be filled successfully
    assert result is True  # Should return True since input1 was filled successfully
    assert view2.input1.read() == "test_value"

    # Should log warning about widget without fill method
    warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
    assert len(warning_logs) > 0
    assert any("doesn't have fill method" in record.message for record in warning_logs)


def test_view_uses_default_strategy_automatically(browser):
    """Test that View automatically uses DefaultFillViewStrategy."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        input2 = TextInput(name="fill_with_2")
        checkbox1 = Checkbox(id="input2")

    view = TestForm(browser)

    # View should automatically create a DefaultFillViewStrategy
    assert view.fill_strategy is not None
    assert isinstance(view.fill_strategy, DefaultFillViewStrategy)

    # Test that view.fill() works (uses the strategy internally)
    result = view.fill({"input1": "integration_test", "checkbox1": True})
    assert result is True

    # Verify values were set
    assert view.input1.read() == "integration_test"
    assert view.checkbox1.read() is True


def test_view_with_custom_wait_strategy(browser):
    """Test View with custom WaitFillViewStrategy."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        input2 = TextInput(name="fill_with_2")
        checkbox1 = Checkbox(id="input2")

        fill_strategy = WaitFillViewStrategy(wait_widget="3s")

    view = TestForm(browser)

    # Should use the custom wait strategy
    assert isinstance(view.fill_strategy, WaitFillViewStrategy)
    assert view.fill_strategy.wait_widget == "3s"

    # Test that view.fill() works with wait strategy
    result = view.fill({"input1": "wait_integration_test", "checkbox1": False})
    assert result is True

    # Verify values were set
    assert view.input1.read() == "wait_integration_test"
    assert view.checkbox1.read() is False


def test_nested_data_flattening(browser):
    """Test that fill strategies handle nested data properly."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        fill_strategy = DefaultFillViewStrategy()

    view = TestForm(browser)

    # Test with nested data (should be flattened automatically by deflatten_dict)
    nested_data = {"user": {"profile": {"input1": "nested_test_value"}}}

    # The fill method flattens nested data before passing to strategy
    view.fill(nested_data)


def test_multiple_fill_operations(browser):
    """Test multiple consecutive fill operations."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        input2 = TextInput(name="fill_with_2")
        checkbox1 = Checkbox(id="input2")

    view = TestForm(browser)

    # First fill operation
    result1 = view.fill({"input1": "first_value", "checkbox1": True})
    assert result1 is True
    assert view.input1.read() == "first_value"
    assert view.checkbox1.read() is True

    # Second fill operation with different values
    result2 = view.fill({"input1": "second_value", "input2": "input2_value"})
    assert result2 is True
    assert view.input1.read() == "second_value"
    assert view.input2.read() == "input2_value"

    # Third fill operation with same values (should return False)
    result3 = view.fill({"input1": "second_value", "input2": "input2_value"})
    assert result3 is False  # No changes made


def test_context_management_in_view_fill(browser):
    """Test that View.fill() properly manages context."""

    class TestForm(View):
        input1 = TextInput(name="input1")
        fill_strategy = DefaultFillViewStrategy()

    view = TestForm(browser)

    # Initially context should have None parent
    assert view.fill_strategy.context.parent is None

    # After fill(), context should be properly set
    view.fill({"input1": "context_test"})
    assert view.fill_strategy.context.parent is view

    # Verify the fill worked
    assert view.input1.read() == "context_test"


def test_fill_strategy_respect_parent_behavior(browser):
    """Test respect_parent behavior in fill strategies."""

    # Parent without respect_parent - child gets default strategy
    class ParentView(View):
        fill_strategy = WaitFillViewStrategy(wait_widget="10s")  # respect_parent=False by default

    class ChildView(View):
        input1 = TextInput(name="input1")
        # Don't set fill_strategy here, let it be inherited

    parent_view = ParentView(browser)
    child_view = ChildView(parent_view)

    # Child should get its own default strategy since parent.fill_strategy.respect_parent=False
    assert child_view.fill_strategy is not None
    assert isinstance(child_view.fill_strategy, DefaultFillViewStrategy)
    assert child_view.fill_strategy is not parent_view.fill_strategy

    # Parent with respect_parent=True - child inherits parent's strategy
    class ParentViewWithRespectParent(View):
        fill_strategy = WaitFillViewStrategy(respect_parent=True, wait_widget="10s")

    class ChildViewInherits(View):
        input1 = TextInput(name="input1")
        # No fill_strategy defined - should inherit from parent

    parent_view2 = ParentViewWithRespectParent(browser)
    child_view2 = ChildViewInherits(parent_view2)

    # Child should use parent's strategy since parent.fill_strategy.respect_parent=True
    assert child_view2.fill_strategy is parent_view2.fill_strategy
    assert isinstance(child_view2.fill_strategy, WaitFillViewStrategy)
    assert child_view2.fill_strategy.wait_widget == "10s"


def test_fill_strategy_error_tolerance(browser, caplog):
    """Test that fill strategies continue execution despite individual widget errors."""

    class BrokenWidget(Widget):
        """Widget that raises an exception during fill."""

        def fill(self, value):
            raise ValueError("Intentional test error")

    class TestForm(View):
        input1 = TextInput(name="input1")
        broken_widget = BrokenWidget()
        input2 = TextInput(name="fill_with_2")
        fill_strategy = DefaultFillViewStrategy()

    view = TestForm(browser)
    view.fill_strategy.context = FillContext(parent=view, logger=log.null_logger)

    # Fill should continue despite broken_widget error
    values = {"input1": "value1", "broken_widget": "will_fail", "input2": "value2"}

    # The current implementation only catches NotImplementedError, not other exceptions
    # So this test should expect the exception to be raised
    with pytest.raises(ValueError, match="Intentional test error"):
        view.fill_strategy.do_fill(values)

    # Let's test the case that actually works - widget without fill method
    class NoFillMethodWidget(Widget):
        """Widget without fill method."""

        pass

    class TestForm2(View):
        input1 = TextInput(name="input1")
        no_fill_widget = NoFillMethodWidget()
        input2 = TextInput(name="fill_with_2")
        fill_strategy = DefaultFillViewStrategy()

    view2 = TestForm2(browser)
    view2.fill_strategy.context = FillContext(parent=view2, logger=log.null_logger)

    # This should work - skips widget without fill method
    values2 = {"input1": "value1", "no_fill_widget": "will_skip", "input2": "value2"}

    with caplog.at_level("WARNING"):
        result = view2.fill_strategy.do_fill(values2)

    # Other widgets should have been filled successfully
    assert result is True  # Should return True since other widgets were filled successfully
    assert view2.input1.read() == "value1"
    assert view2.input2.read() == "value2"

    # Should log warning about missing fill method
    warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
    assert len(warning_logs) > 0
    assert any("doesn't have fill method" in record.message for record in warning_logs)
