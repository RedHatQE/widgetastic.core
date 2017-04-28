# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
import re

from widgetastic.exceptions import DoNotReadThisWidget
from widgetastic.widget import View, Table, Text, TextInput, FileInput, Checkbox, Select
from widgetastic.utils import Fillable, ParametrizedString


def test_basic_widgets(browser):
    class TestForm(View):
        h3 = Text('.//h3')
        input1 = TextInput(name='input1')
        input2 = Checkbox(id='input2')
        fileinput = FileInput(id='fileinput')

    class AFillable(Fillable):
        def __init__(self, text):
            self.text = text

        def as_fill_value(self):
            return self.text

    form = TestForm(browser)
    assert isinstance(form, TestForm)
    data = form.read()
    assert data['h3'] == 'test test'
    assert data['input1'] == ''
    assert not data['input2']
    assert not form.fill({'input2': False})
    assert form.fill({'input2': True})
    assert not form.fill({'input2': True})
    assert form.input2.read()

    assert form.fill({'input1': 'foo'})
    assert not form.fill({'input1': 'foo'})
    assert form.fill({'input1': 'foobar'})
    assert not form.fill({'input1': 'foobar'})
    assert form.fill(data)

    assert form.fill({'input1': AFillable('wut')})
    assert not form.fill({'input1': AFillable('wut')})
    assert form.read()['input1'] == 'wut'
    assert form.input1.fill(AFillable('a_test'))
    assert not form.input1.fill(AFillable('a_test'))
    assert form.input1.read() == 'a_test'

    assert form.fileinput.fill('foo')
    with pytest.raises(DoNotReadThisWidget):
        form.fileinput.read()


def test_nested_views_read_fill(browser):
    class TestForm(View):
        h3 = Text('.//h3')

        class Nested1(View):
            input1 = TextInput(name='input1')

            class Nested2(View):
                input2 = Checkbox(id='input2')

    form = TestForm(browser)
    assert isinstance(form, TestForm)
    data = form.read()

    assert data['h3'] == 'test test'
    assert data['Nested1']['input1'] == ''
    assert not data['Nested1']['Nested2']['input2']

    assert form.fill({
        'Nested1': {
            'input1': 'foobar',
            'Nested2': {
                'input2': True
            }
        }
    })

    assert form.Nested1.input1.read() == 'foobar'
    assert form.Nested1.Nested2.input2.read()

    assert form.Nested1.Nested2.input2.hierarchy == [
        form, form.Nested1, form.Nested1.Nested2, form.Nested1.Nested2.input2]
    assert form.hierarchy == [form]

    assert form.Nested1.Nested2.input2.locatable_parent is None


def test_table(browser):
    class TestForm(View):
        table = Table('#with-thead')
        other_table = Table('#untypical_header')

    view = TestForm(browser)
    assert view.table.headers == (None, 'Column 1', 'Column 2', 'Column 3', 'Column 4')
    assert len(list(view.table.rows())) == 3
    assert len(list(view.table.rows(column_1='qwer'))) == 1
    assert len(list(view.table.rows(column_1__startswith='bar_'))) == 2
    assert len(list(view.table.rows(column_1__contains='_'))) == 2
    assert len(list(view.table.rows(column_1__endswith='_x'))) == 1

    assert len(list(view.table.rows(column_1__startswith='bar_', column_1__endswith='_x'))) == 1

    assert len(list(view.table.rows(_row__attr=('data-test', 'def-345')))) == 1
    assert len(list(view.table.rows(_row__attr_startswith=('data-test', 'abc')))) == 2
    assert len(list(view.table.rows(_row__attr_endswith=('data-test', '345')))) == 2
    assert len(list(view.table.rows(_row__attr_contains=('data-test', '3')))) == 3
    assert len(list(view.table.rows(
        _row__attr_contains=('data-test', '3'), _row__attr_startswith=('data-test', 'abc')))) == 2

    assert len(list(view.table.rows(_row__attr=('data-test', 'abc-345'), column_1='qwer'))) == 0

    with pytest.raises(ValueError):
        list(view.table.rows(_row__papalala=('foo', 'bar')))

    with pytest.raises(ValueError):
        list(view.table.rows(_row__attr_papalala=('foo', 'bar')))

    with pytest.raises(ValueError):
        list(view.table.rows(_row__attr='foobar'))

    assert len(list(view.table.rows((0, 'asdf')))) == 1
    assert len(list(view.table.rows((1, 'startswith', 'bar_')))) == 2
    assert len(list(view.table.rows((1, 'startswith', 'bar_'), column_1__endswith='_x'))) == 1

    assert len(list(view.table.rows((1, re.compile(r'_x$'))))) == 1
    assert len(list(view.table.rows((1, re.compile(r'^bar_'))))) == 2
    assert len(list(view.table.rows(('column_1', re.compile(r'^bar_'))))) == 2
    assert len(list(view.table.rows(('Column 1', re.compile(r'^bar_'))))) == 2
    assert len(list(view.table.rows((0, re.compile(r'^foo_')), (3, re.compile(r'_x$'))))) == 1
    assert len(list(view.table.rows(
        (0, re.compile(r'^foo_')),
        (1, 'contains', '_'),
        column_3__endswith='_x'))) == 1

    row = view.table.row(
        (0, re.compile(r'^foo_')),
        (1, 'contains', '_'),
        column_3__endswith='_x')
    assert row[0].text == 'foo_x'

    row = view.table.row(column_1='bar_x')
    assert row[0].text == 'foo_x'
    assert row['Column 1'].text == 'bar_x'
    assert row.column_1.text == 'bar_x'

    assert [(header, column.text) for header, column in row] == [
        (None, 'foo_x'),
        ('Column 1', 'bar_x'),
        ('Column 2', 'baz_x'),
        ('Column 3', 'bat_x'),
        ('Column 4', '')]

    assert view.table[0].column_2.text == 'yxcv'

    with pytest.raises(AttributeError):
        row.papalala

    with pytest.raises(TypeError):
        view.table['boom!']

    # headers are read correctly when those aren't in thead
    assert len(view.other_table.headers) == 2

    row = next(view.other_table.rows())
    assert row.event.text == 'Some Event'


def test_table_with_widgets(browser):
    class TestForm(View):
        table = Table('#withwidgets', column_widgets={
            'Column 2': TextInput(locator='./input'),
            'Column 3': TextInput(locator='./input')})

    view = TestForm(browser)

    assert view.read() == {
        'table': [
            {0: 'foo', 'Column 2': '', 'Column 3': 'foo col 3'},
            {0: 'bar', 'Column 2': 'bar col 2', 'Column 3': ''}
        ]}
    assert view.fill({'table': [{'Column 2': 'foobaaar'}]})
    assert not view.fill({'table': [{'Column 2': 'foobaaar'}]})
    assert view.read() == {
        'table': [
            {0: 'foo', 'Column 2': 'foobaaar', 'Column 3': 'foo col 3'},
            {0: 'bar', 'Column 2': 'bar col 2', 'Column 3': ''}
        ]}

    assert view.fill({'table': [{}, {'Column 3': 'yolo'}]})
    assert view.read() == {
        'table': [
            {0: 'foo', 'Column 2': 'foobaaar', 'Column 3': 'foo col 3'},
            {0: 'bar', 'Column 2': 'bar col 2', 'Column 3': 'yolo'}
        ]}

    with pytest.raises(TypeError):
        # There is nothing to be filled
        view.fill({'table': [{0: 'explode'}]})

    with pytest.raises(TypeError):
        # No assoc_column
        view.fill({'table': {0: {'Column 2': 'lalala'}}})

    with pytest.raises(ValueError):
        # No assoc_column - no implicit column name for filling
        view.fill({'table': [{}, '']})


def test_table_with_widgets_and_assoc_column(browser):
    class TestForm(View):
        table = Table('#withwidgets', column_widgets={
            'Column 2': TextInput(locator='./input'),
            'Column 3': TextInput(locator='./input')},
            assoc_column=0)

    view = TestForm(browser)

    assert view.read() == {
        'table': {
            'foo': {'Column 2': '', 'Column 3': 'foo col 3'},
            'bar': {'Column 2': 'bar col 2', 'Column 3': ''}
        }}
    assert view.fill({'table': {'foo': {'Column 2': 'foobaaar'}}})
    assert not view.fill({'table': {'foo': {'Column 2': 'foobaaar'}}})
    assert view.read() == {
        'table': {
            'foo': {'Column 2': 'foobaaar', 'Column 3': 'foo col 3'},
            'bar': {'Column 2': 'bar col 2', 'Column 3': ''}
        }}

    assert view.fill({'table': {'bar': {'Column 3': 'yolo'}}})
    assert view.read() == {
        'table': {
            'foo': {'Column 2': 'foobaaar', 'Column 3': 'foo col 3'},
            'bar': {'Column 2': 'bar col 2', 'Column 3': 'yolo'}
        }}


def test_simple_select(browser):
    class TestForm(View):
        select = Select(name='testselect1')

    view = TestForm(browser)

    assert not view.select.is_multiple
    assert not view.select.classes
    assert view.select.all_options == [('Foo', 'foo'), ('Bar', 'bar')]

    assert len(view.select.all_selected_options) == 1

    assert view.select.first_selected_option in view.select.all_selected_options
    assert view.select.first_selected_option == 'Foo'

    with pytest.raises(NotImplementedError):
        view.select.deselect_all()

    assert view.select.get_value_by_text('Foo') == 'foo'

    view.select.select_by_value('bar')
    assert view.select.first_selected_option == 'Bar'

    with pytest.raises(ValueError):
        view.select.select_by_value('bar', 'foo')

    view.select.select_by_visible_text('Foo')
    assert view.select.first_selected_option == 'Foo'

    view.select.select_by_visible_text('Bar')
    assert view.select.first_selected_option == 'Bar'

    with pytest.raises(ValueError):
        view.select.select_by_visible_text('Bar', 'Foo')

    view.select.fill('Foo')
    assert view.select.read() == 'Foo'

    view.select.fill(['Bar'])
    assert view.select.read() == 'Bar'

    view.select.fill(('by_value', 'foo'))
    assert view.select.read() == 'Foo'

    view.select.fill(('by_value', 'bar'))
    assert view.select.read() == 'Bar'

    with pytest.raises(ValueError):
        view.select.fill(('foo', 'bar'))

    with pytest.raises(ValueError):
        view.select.fill((123, 'bad modifier'))

    with pytest.raises(ValueError):
        view.select.fill(('a', 'long', 'tuple'))

    with pytest.raises(ValueError):
        view.select.fill(('a short tuple', ))


def test_multi_select(browser):
    class TestForm(View):
        select = Select(name='testselect2')

    view = TestForm(browser)

    assert view.select.is_multiple
    assert view.select.classes == {'xfoo', 'xbar'}
    assert view.select.all_options == [('Foo', 'foo'), ('Bar', 'bar'), ('Baz', 'baz')]

    view.select.select_by_visible_text('Foo', 'Bar')
    assert view.select.all_selected_options == ['Foo', 'Bar']

    view.select.deselect_all()
    assert not view.select.all_selected_options

    view.select.select_by_value('foo', 'bar')
    assert view.select.all_selected_values == ['foo', 'bar']

    view.select.deselect_all()
    assert not view.select.all_selected_options

    assert view.select.read() == []
    assert not view.select.fill(None)
    assert view.select.fill('Foo')
    assert view.select.read() == ['Foo']
    assert view.select.fill(['Foo', 'Bar'])
    assert view.select.read() == ['Foo', 'Bar']
    assert not view.select.fill(['Foo', 'Bar'])

    assert view.select.fill(('by_value', 'baz'))
    assert view.select.read() == ['Baz']

    assert view.select.fill(['Foo', ('by_value', 'bar')])
    assert view.select.read() == ['Foo', 'Bar']


def test_parametrized_locator(browser):
    class TestForm(View):
        my_value = 3
        header = Text(ParametrizedString('.//h{header}'))
        header_cls = Text(ParametrizedString('.//h{@my_value}'))
        input = TextInput(name=ParametrizedString('input{input}'))

    good = TestForm(browser, additional_context={'header': 3, 'input': 1})
    assert good.header.text == 'test test'
    assert good.header_cls.text == 'test test'
    good.input.fill('')
    assert good.input.read() == ''
    assert good.input.fill('foo')
    assert good.input.read() == 'foo'

    bad = TestForm(browser)
    # This uses value defined on class so it should work
    assert good.header_cls.text == 'test test'
    with pytest.raises(AttributeError):
        bad.header.text

    with pytest.raises(AttributeError):
        bad.input.read()


@pytest.mark.parametrize('style', ['callable', 'clickable', 'string'])
def test_fill_with(browser, style):
    class TestForm(View):
        i1 = TextInput(name='fill_with_1')
        i2 = TextInput(name='fill_with_2')
        i3 = TextInput(name='fill_with_3')

        b1 = Text('//button[@id="fill_with_button_1"]')
        b2 = Text('//button[@id="fill_with_button_2"]')

    view = TestForm(browser)
    if style == 'callable':
        assert view.fill_with(
            {'i1': 'foo'},
            on_change=view.b1.click,
            no_change=view.b2.click)
        assert view.read()['i1'] == 'foo'
        assert 'clicked' in browser.classes(view.b1)
        assert 'clicked' not in browser.classes(view.b2)
        # Reset classes
        browser.set_attribute('class', '', view.b1)
        browser.set_attribute('class', '', view.b2)

        assert not view.fill_with(
            {'i1': 'foo'},
            on_change=view.b1.click,
            no_change=view.b2.click)
        assert view.read()['i1'] == 'foo'
        assert 'clicked' not in browser.classes(view.b1)
        assert 'clicked' in browser.classes(view.b2)
    elif style == 'clickable':
        assert view.fill_with(
            {'i1': 'foo'},
            on_change=view.b1,
            no_change=view.b2)
        assert view.read()['i1'] == 'foo'
        assert 'clicked' in browser.classes(view.b1)
        assert 'clicked' not in browser.classes(view.b2)
        # Reset classes
        browser.set_attribute('class', '', view.b1)
        browser.set_attribute('class', '', view.b2)

        assert not view.fill_with(
            {'i1': 'foo'},
            on_change=view.b1,
            no_change=view.b2)
        assert view.i1.value == 'foo'
        assert 'clicked' not in browser.classes(view.b1)
        assert 'clicked' in browser.classes(view.b2)
    elif style == 'string':
        assert view.fill_with(
            {'i1': 'foo'},
            on_change='b1',
            no_change='b2')
        assert view.read()['i1'] == 'foo'
        assert 'clicked' in browser.classes(view.b1)
        assert 'clicked' not in browser.classes(view.b2)
        # Reset classes
        browser.set_attribute('class', '', view.b1)
        browser.set_attribute('class', '', view.b2)

        assert not view.fill_with(
            {'i1': 'foo'},
            on_change='b1',
            no_change='b2')
        assert view.read()['i1'] == 'foo'
        assert 'clicked' not in browser.classes(view.b1)
        assert 'clicked' in browser.classes(view.b2)
    else:
        pytest.fail('bad param {}'.format(style))


def test_with_including(browser):
    class TestForm1(View):
        h3 = Text('.//h3')

    class TestForm2(View):
        caption = View.include(TestForm1)
        input1 = TextInput(name='input1')
        input2 = Checkbox(id='input2')

    class TestForm3(View):
        fileinput = FileInput(id='fileinput')
        inputs = View.include(TestForm2)

    class AFillable(Fillable):
        def __init__(self, text):
            self.text = text

        def as_fill_value(self):
            return self.text

    form = TestForm3(browser)
    # This repeats test_basic_widgets
    assert isinstance(form, TestForm3)
    data = form.read()
    assert data['h3'] == 'test test'
    assert data['input1'] == ''
    assert not data['input2']
    assert not form.fill({'input2': False})
    assert form.fill({'input2': True})
    assert not form.fill({'input2': True})
    assert form.input2.read()

    assert form.fill({'input1': 'foo'})
    assert not form.fill({'input1': 'foo'})
    assert form.fill({'input1': 'foobar'})
    assert not form.fill({'input1': 'foobar'})
    assert form.fill(data)

    assert form.fill({'input1': AFillable('wut')})
    assert not form.fill({'input1': AFillable('wut')})
    assert form.read()['input1'] == 'wut'
    assert form.input1.fill(AFillable('a_test'))
    assert not form.input1.fill(AFillable('a_test'))
    assert form.input1.read() == 'a_test'

    assert form.fileinput.fill('foo')
    with pytest.raises(DoNotReadThisWidget):
        form.fileinput.read()
