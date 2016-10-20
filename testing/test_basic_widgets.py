# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
import re

from widgetastic.widget import View, Table, Text, TextInput, Checkbox, Select
from widgetastic.utils import Fillable


def test_basic_widgets(browser):
    class TestForm(View):
        h3 = Text('.//h3')
        input1 = TextInput(name='input1')
        input2 = Checkbox(id='input2')

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


def test_table(browser):
    class TestForm(View):
        table = Table('#with-thead')

    view = TestForm(browser)
    assert view.table.headers == (None, 'Column 1', 'Column 2', 'Column 3')
    assert len(list(view.table.rows())) == 3
    assert len(list(view.table.rows(column_1='qwer'))) == 1
    assert len(list(view.table.rows(column_1__startswith='bar_'))) == 2
    assert len(list(view.table.rows(column_1__contains='_'))) == 2
    assert len(list(view.table.rows(column_1__endswith='_x'))) == 1

    assert len(list(view.table.rows(column_1__startswith='bar_', column_1__endswith='_x'))) == 1

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
        ('Column 3', 'bat_x')]

    assert view.table[0].column_2.text == 'yxcv'

    with pytest.raises(AttributeError):
        row.papalala

    with pytest.raises(TypeError):
        view.table['boom!']


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
