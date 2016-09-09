# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from widgetastic.widget import View, Text, TextInput, Checkbox


def test_basic_widgets(browser):
    class TestForm(View):
        h3 = Text('.//h3')
        input1 = TextInput(name='input1')
        input2 = Checkbox(id='input2')

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
