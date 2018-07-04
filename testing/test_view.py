# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from widgetastic.exceptions import NoSuchElementException
from widgetastic.utils import ParametrizedLocator, ParametrizedString, Parameter, Ignore
from widgetastic.widget import (
    ParametrizedView, ParametrizedViewRequest, Text, View, Widget, do_not_read_this_widget,
    Checkbox, Select, ConditionalSwitchableView, WidgetDescriptor, TextInput, FileInput, WTMixin)


def test_can_create_view(browser):
    class MyView(View):
        pass

    MyView(browser)


def test_view_browser(browser):
    class MyView(View):
        pass

    view = MyView(browser)
    assert view.browser is browser


def test_view_root_locator(browser):
    class MyView(View):
        ROOT = '#foo'

    view = MyView(browser)
    assert view.__locator__() == ('css selector', '#foo')


def test_view_widget_names(browser):
    class MyView(View):
        w1 = Widget()
        w2 = Widget()

    assert MyView(browser).widget_names == ('w1', 'w2')


def test_view_no_subviews(browser):
    class MyView(View):
        pass

    assert not MyView(browser).sub_widgets
    assert not MyView(browser).cached_sub_widgets


def test_view_with_subviews(browser):
    class MyView(View):
        w = Widget()

        class AnotherView(View):
            another_widget = Widget()

        class Foo(View):
            bar = Widget()

    view = MyView(browser)
    assert not view.cached_sub_widgets
    assert isinstance(view.w, Widget)
    assert view.cached_sub_widgets == [view.w]
    assert isinstance(view.AnotherView, View)
    assert set(view.cached_sub_widgets) == {view.AnotherView, view.w}
    assert isinstance(view.Foo, View)
    assert set(view.cached_sub_widgets) == {view.AnotherView, view.Foo, view.w}
    assert isinstance(view.AnotherView.another_widget, Widget)
    assert isinstance(view.Foo.bar, Widget)
    assert {type(v).__name__ for v in view.sub_widgets} == {'AnotherView', 'Foo', 'Widget'}


def test_view_fill(browser):
    class TestForm(View):
        h3 = Text('.//h3', log_on_fill_unspecified=False)
        input1 = TextInput(name='input1')
        input2 = Checkbox(id='input2')
        fileinput = FileInput(id='fileinput')

    view = TestForm(browser)
    assert view.fill({'input1': 'hello world man'})


def test_view_fill_before_fill(browser):
    class TestForm(View):
        input1 = TextInput(name='input1')

        def before_fill(self, values):
            return True

    view = TestForm(browser)
    assert view.fill({'input1': 'hello world man'})
    assert view.fill({'input1': 'hello world man'})


def test_view_fill_after_fill(browser):
    class TestForm(View):
        input1 = TextInput(name='input1')

        def after_fill(self, was_change):
            return was_change or True

    view = TestForm(browser)
    assert view.fill({'input1': 'hello world man'})
    assert view.fill({'input1': 'hello world man'})


def test_view_is_displayed_without_root_locator(browser):
    class MyView(View):
        pass

    assert MyView(browser).is_displayed


def test_view_is_displayed_with_root_locator(browser):
    class MyView(View):
        ROOT = '#hello'

    assert MyView(browser).is_displayed


def test_view_is_not_displayed_with_root_locator(browser):
    class MyView(View):
        ROOT = '#thisdoesnotexist'

    view = MyView(browser)
    assert not view.is_displayed


def test_inherited_view(browser):
    class AView1(View):
        widget1 = Widget()

    class AView2(AView1):
        widget2 = Widget()

    view = AView2(browser)
    assert view.widget1.parent_view is view


def test_mixin_view(browser):
    class SomeMixin(WTMixin):
        a_mixin_widget = Widget()

    class AView1(View):
        widget1 = Widget()

    class AView2(AView1, SomeMixin):
        widget2 = Widget()

    view = AView2(browser)
    assert view.widget_names == ('a_mixin_widget', 'widget1', 'widget2')
    view.a_mixin_widget


def test_do_not_read_widget(browser):
    class AWidget1(Widget):
        def read(self):
            return 1

    class AWidget2(Widget):
        def read(self):
            do_not_read_this_widget()

    class AView(View):
        w1 = AWidget1()
        w2 = AWidget2()

    view = AView(browser)
    data = view.read()
    assert 'w2' not in data


def test_view_parameter(browser):
    class MyView(View):
        my_param = Parameter('foo')

    assert MyView(browser, additional_context={'foo': 'bar'}).my_param == 'bar'

    with pytest.raises(AttributeError):
        MyView(browser).my_param


def test_view_parametrized_string(browser):
    class MyView(View):
        my_param = ParametrizedString('{foo} {foo|quote}')
        # This test is now disabled as it fails on py3, nothing yet uses this functionality
        # nested_thing = ParametrizedString('foo {"id-{foo}"|quote}')

    assert MyView(browser, additional_context={'foo': 'bar'}).my_param == 'bar "bar"'
    # assert MyView(browser, additional_context={'foo': 'bar'}).nested_thing == 'foo "id-bar"'


def test_parametrized_view(browser):
    class MyView(View):
        class table_row(ParametrizedView):
            PARAMETERS = ('rowid', )
            ROOT = ParametrizedLocator('.//tr[@data-test={rowid|quote}]')

            col1 = Text('./td[2]')
            checkbox = Checkbox(locator=ParametrizedString('.//td/input[@id={rowid|quote}]'))

            @classmethod
            def all(cls, browser):
                result = []
                for e in browser.elements('.//table[@id="with-thead"]//tr[td]'):
                    result.append((browser.get_attribute('data-test', e), ))
                return result

    view = MyView(browser)
    assert isinstance(view.table_row, ParametrizedViewRequest)
    assert view.table_row('abc-123').col1.text == 'qwer'
    assert view.table_row(rowid='abc-345').col1.text == 'bar_x'

    with pytest.raises(TypeError):
        view.table_row()

    with pytest.raises(TypeError):
        view.table_row('foo', 'bar')

    with pytest.raises(TypeError):
        view.table_row(foo='bar')

    view.fill({'table_row': {
        'abc-123': {'checkbox': True},
        ('abc-345', ): {'checkbox': False},
        ('def-345', ): {'checkbox': True},
    }})

    assert view.read() == {
        'table_row': {
            'abc-123': {'col1': 'qwer', 'checkbox': True},
            'abc-345': {'col1': 'bar_x', 'checkbox': False},
            'def-345': {'col1': 'bar_y', 'checkbox': True}}}

    assert view.fill({'table_row': {
        'abc-123': {'checkbox': False},
        ('abc-345', ): {'checkbox': False},
        ('def-345', ): {'checkbox': False},
    }})

    assert view.read() == {
        'table_row': {
            'abc-123': {'col1': 'qwer', 'checkbox': False},
            'abc-345': {'col1': 'bar_x', 'checkbox': False},
            'def-345': {'col1': 'bar_y', 'checkbox': False}}}

    assert not view.fill({'table_row': {
        'abc-123': {'checkbox': False},
        ('abc-345', ): {'checkbox': False},
        ('def-345', ): {'checkbox': False},
    }})

    # list-like access
    assert view.table_row[0].col1.text == 'qwer'
    cx, cy = view.table_row[1:3]
    assert cx.col1.text == 'bar_x'
    assert cy.col1.text == 'bar_y'

    cx, cy = view.table_row[0:3:2]
    assert cx.col1.text == 'qwer'
    assert cy.col1.text == 'bar_y'

    for i, row in enumerate(view.table_row):
        if i == 0:
            assert row.col1.text == 'qwer'
        elif i == 1:
            assert row.col1.text == 'bar_x'
        elif i == 2:
            assert row.col1.text == 'bar_y'
        else:
            pytest.fail('iterated longer than expected')

    assert len(view.table_row) == 3


def test_parametrized_view_read_without_all(browser):
    class MyView(View):
        class table_row(ParametrizedView):
            PARAMETERS = ('rowid', )
            ROOT = ParametrizedLocator('.//tr[@data-test={rowid|quote}]')

            col1 = Text('./td[2]')

    view = MyView(browser)
    assert list(view.read().keys()) == []


def test_view_parent_smart_works(browser):
    """This test ensures that when the functionality of a view is extended, the element lookup
    correctly handles the difference between ROOT and other locators."""
    class MyView(View):
        ROOT = '#proper'

        class AnotherView(View):
            ROOT = './div[@class="c1"]/span'

            def get_text(self):
                return self.browser.text(self)

    view = MyView(browser)

    assert view.AnotherView.get_text() == 'C1'


def test_cache(browser):
    class MyView(View):
        w = Widget()
        x = Widget()

        class nested1(View):
            w = Widget()
            x = Widget()

            class nested2(View):
                class nested3(View):
                    w = Widget()

    view = MyView(browser)
    assert len(view._widget_cache.keys()) == 0
    assert len(view.nested1._widget_cache.keys()) == 0
    assert len(view.nested1.nested2._widget_cache.keys()) == 0
    assert len(view.nested1.nested2.nested3._widget_cache.keys()) == 0

    view.w
    assert set(view._widget_cache.keys()) == {getattr(MyView, 'w'), getattr(MyView, 'nested1')}
    view.flush_widget_cache()
    assert len(view._widget_cache.keys()) == 0


def test_view_iteration(browser):
    """Test whether the widget cache does not get widgets when only views touched."""
    class MyView(View):
        w = Widget()
        x = Widget()

        @View.nested
        class y(View):
            pass

        class z(View):
            pass

    view = MyView(browser)
    assert len(view._widget_cache.keys()) == 0
    assert len(view.sub_widgets) == 4
    assert set(view._widget_cache.keys()) == {MyView.y, MyView.z, MyView.w, MyView.x}


def test_indirect_positive(browser):
    class MyView(View):
        ROOT = '//badger'
        INDIRECT = True

        class nested(View):
            ROOT = '#bogus'

            t = Text('.lookmeup')

    view = MyView(browser)
    assert not view.is_displayed
    assert view.nested.is_displayed
    assert view.nested.t.text == 'BAD'


def test_indirect_negative(browser):
    class MyView(View):
        ROOT = '//badger'
        INDIRECT = False

        class nested(View):
            ROOT = '#bogus'

            t = Text('.lookmeup')

    view = MyView(browser)
    assert not view.is_displayed
    assert not view.nested.is_displayed


def test_switchable_view_with_reference_only(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        the_switchable_view = ConditionalSwitchableView(reference='the_reference')

        @the_switchable_view.register('foo')
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

        @the_switchable_view.register('bar')
        class BarView(View):
            widget = Text('//h3[@id="switchabletesting-2"]')

    view = MyView(browser)
    view.the_reference.fill('foo')
    assert view.the_switchable_view.widget.read() == 'footest'
    view.the_reference.fill('bar')
    assert view.the_switchable_view.widget.read() == 'bartest'


def test_switchable_view_with_nonwidget_reference_only(browser):
    class MyView(View):
        the_reference = 'bar'

        the_switchable_view = ConditionalSwitchableView(reference='the_reference')

        @the_switchable_view.register('foo')
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

        @the_switchable_view.register('bar')
        class BarView(View):
            widget = Text('//h3[@id="switchabletesting-2"]')

    view = MyView(browser)
    assert view.the_switchable_view.widget.read() == 'bartest'


def test_switchable_view_with_bad_reference(browser):
    class MyView(View):
        the_reference = Select(id='ewaopaopsdkgnjdsopjf')

        the_switchable_view = ConditionalSwitchableView(
            reference='the_reference', ignore_bad_reference=True)

        @the_switchable_view.register('foo')
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

        @the_switchable_view.register('bar', default=True)
        class BarView(View):
            widget = Text('//h3[@id="switchabletesting-2"]')

    view = MyView(browser)
    assert view.the_switchable_view.widget.read() == 'bartest'


def test_switchable_view_with_bad_reference_negative(browser):
    class MyView(View):
        the_reference = Select(id='ewaopaopsdkgnjdsopjf')

        the_switchable_view = ConditionalSwitchableView(reference='the_reference')

        @the_switchable_view.register('foo')
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

        @the_switchable_view.register('bar', default=True)
        class BarView(View):
            widget = Text('//h3[@id="switchabletesting-2"]')

    view = MyView(browser)

    with pytest.raises(NoSuchElementException):
        view.the_switchable_view.widget.read()


def test_switchable_view_with_nested_reference(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        class nest1(View):  # noqa
            class nest2(View):  # noqa
                the_switchable_view = ConditionalSwitchableView(
                    reference='parent.parent.the_reference')

                @the_switchable_view.register('foo')
                class FooView(View):
                    widget = Text('//h3[@id="switchabletesting-1"]')

                @the_switchable_view.register('bar')
                class BarView(View):
                    widget = Text('//h3[@id="switchabletesting-2"]')

    view = MyView(browser)
    view.the_reference.fill('foo')
    assert view.nest1.nest2.the_switchable_view.widget.read() == 'footest'
    view.the_reference.fill('bar')
    assert view.nest1.nest2.the_switchable_view.widget.read() == 'bartest'


def test_switchable_view_with_reference_only_and_widgetdescriptors(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        the_switchable_widget = ConditionalSwitchableView(reference='the_reference')

        the_switchable_widget.register('foo', widget=Text('//h3[@id="switchabletesting-1"]'))
        the_switchable_widget.register('bar', widget=Text('//h3[@id="switchabletesting-2"]'))

    view = MyView(browser)
    view.the_reference.fill('foo')
    assert view.the_switchable_widget.read() == 'footest'
    view.the_reference.fill('bar')
    assert view.the_switchable_widget.read() == 'bartest'


def test_switchable_view_with_callables(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        the_switchable_view = ConditionalSwitchableView()

        @the_switchable_view.register(lambda the_reference: the_reference == 'foo')
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

        @the_switchable_view.register(lambda the_reference: the_reference == 'bar')
        class BarView(View):
            widget = Text('//h3[@id="switchabletesting-2"]')

    view = MyView(browser)
    view.the_reference.fill('foo')
    assert view.the_switchable_view.widget.read() == 'footest'
    view.the_reference.fill('bar')
    assert view.the_switchable_view.widget.read() == 'bartest'


def test_switchable_view_with_default(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        the_switchable_view = ConditionalSwitchableView()

        @the_switchable_view.register(lambda the_reference: the_reference == 'foo', default=True)
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

    view = MyView(browser)
    view.the_reference.fill('bar')
    assert view.the_reference.read() == 'bar'
    # The bar is not handled but it should get to the default view anyway
    assert view.the_switchable_view.widget.read() == 'footest'


def test_switchable_view_without_default_and_unhandled_value(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        the_switchable_view = ConditionalSwitchableView()

        @the_switchable_view.register(lambda the_reference: the_reference == 'foo')
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

    view = MyView(browser)
    view.the_reference.fill('bar')
    assert view.the_reference.read() == 'bar'
    with pytest.raises(ValueError):
        assert view.the_switchable_view.widget.read() == 'footest'


def test_switchable_view_multiple_default_error():
    view = ConditionalSwitchableView()

    @view.register('foo', default=True)
    class SomeView(View):
        pass

    with pytest.raises(TypeError):
        @view.register('foo', default=True)
        class SomeAnotherView(View):
            pass


def test_switchable_view_string_without_reference(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        the_switchable_view = ConditionalSwitchableView()

        @the_switchable_view.register('foo')
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

    view = MyView(browser)
    with pytest.raises(TypeError):
        view.the_switchable_view


def test_switchable_view_string_bad_reference(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        the_switchable_view = ConditionalSwitchableView(reference='lalapapa')

        @the_switchable_view.register('foo')
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

    view = MyView(browser)
    with pytest.raises(TypeError):
        view.the_switchable_view


def test_switchable_view_string_nonsimple_lambda(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        the_switchable_view = ConditionalSwitchableView()

        @the_switchable_view.register(lambda *args: None)
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

    view = MyView(browser)
    with pytest.raises(TypeError):
        view.the_switchable_view


def test_switchable_view_string_lambda_bad_argument_widget(browser):
    class MyView(View):
        the_reference = Select(id='switchabletesting-select')

        the_switchable_view = ConditionalSwitchableView()

        @the_switchable_view.register(lambda foobar: None)
        class FooView(View):
            widget = Text('//h3[@id="switchabletesting-1"]')

    view = MyView(browser)
    with pytest.raises(TypeError):
        view.the_switchable_view


def test_ignore_decorator(browser):
    class MyViewToNotNest(View):
        foo = Widget()

    class MyView(View):
        bar = Widget()
        baz = Ignore(MyViewToNotNest)
        inga = MyViewToNotNest
        bat = Widget()

    assert MyView.baz is MyViewToNotNest
    assert MyView.inga is not MyViewToNotNest
    assert isinstance(MyView.inga, WidgetDescriptor)
    assert MyView.inga.klass is MyViewToNotNest
    view = MyView(browser)
    assert view.baz is MyViewToNotNest
    assert MyView.inga is not MyViewToNotNest
    assert 'baz' not in view.widget_names
    assert 'inga' in view.widget_names
    assert isinstance(view.inga, MyViewToNotNest)
