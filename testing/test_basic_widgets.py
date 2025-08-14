import re

import pytest

from widgetastic.exceptions import DoNotReadThisWidget
from widgetastic.utils import Fillable
from widgetastic.utils import ParametrizedString
from widgetastic.utils import Version
from widgetastic.utils import VersionPick
from widgetastic.widget import Checkbox
from widgetastic.widget import ColourInput
from widgetastic.widget import FileInput
from widgetastic.widget import Select
from widgetastic.widget import Table
from widgetastic.widget import Text
from widgetastic.widget import TextInput
from widgetastic.widget import View
from widgetastic.widget.table import TableRow


def test_basic_widgets(browser):
    class TestForm(View):
        h3 = Text(".//h3")
        input1 = TextInput(name="input1")
        input2 = Checkbox(id="input2")
        input3 = ColourInput(id="colourinput")
        input4 = TextInput(name="input1_disabled")
        input5 = Checkbox(id="input2_disabled")
        fileinput = FileInput(id="fileinput")

    class AFillable(Fillable):
        def __init__(self, text):
            self.text = text

        def as_fill_value(self):
            return self.text

    form = TestForm(browser)
    assert isinstance(form, TestForm)
    data = form.read()
    assert data["h3"] == "test test"
    assert data["input1"] == ""
    assert not data["input2"]
    assert not form.fill({"input2": False})
    assert form.fill({"input2": True})
    assert not form.fill({"input2": True})
    assert form.input2.read()

    assert form.fill({"input1": "foo"})
    assert not form.fill({"input1": "foo"})
    assert form.fill({"input1": "foobar"})
    assert not form.fill({"input1": "foobar"})
    assert form.fill(data)

    assert form.fill({"input1": AFillable("wut")})
    assert not form.fill({"input1": AFillable("wut")})
    assert form.read()["input1"] == "wut"
    assert form.input1.fill(AFillable("a_test"))
    assert not form.input1.fill(AFillable("a_test"))
    assert form.input1.read() == "a_test"

    assert form.fill({"input3": "#00cafe"})
    assert form.input3.read() == "#00cafe"
    assert not form.fill({"input3": "#00cafe"})

    assert form.fill({"input3": "#beefed"})
    assert not form.fill({"input3": "#beefed"})

    assert form.fileinput.fill("/etc/resolv.conf")
    with pytest.raises(DoNotReadThisWidget):
        form.fileinput.read()

    assert form.input1.is_enabled
    assert not form.input4.is_enabled
    assert form.input2.is_enabled
    assert not form.input5.is_enabled


def test_nested_views_read_fill(browser):
    class TestForm(View):
        h3 = Text(".//h3")

        class Nested1(View):
            input1 = TextInput(name="input1")

            class Nested2(View):
                input2 = Checkbox(id="input2")

    form = TestForm(browser)
    assert isinstance(form, TestForm)
    data = form.read()

    assert data["h3"] == "test test"
    assert data["Nested1"]["input1"] == ""
    assert not data["Nested1"]["Nested2"]["input2"]

    assert form.fill({"Nested1": {"input1": "foobar", "Nested2": {"input2": True}}})

    assert form.Nested1.input1.read() == "foobar"
    assert form.Nested1.Nested2.input2.read()

    assert form.Nested1.Nested2.input2.hierarchy == [
        form,
        form.Nested1,
        form.Nested1.Nested2,
        form.Nested1.Nested2.input2,
    ]
    assert form.hierarchy == [form]

    assert form.Nested1.Nested2.input2.locatable_parent is None


def test_nested_views_read_fill_flat(browser):
    class TestForm(View):
        h3 = Text(".//h3")

        class Nested1(View):
            input1 = TextInput(name="input1")

            class Nested2(View):
                input2 = Checkbox(id="input2")

    form = TestForm(browser)
    assert isinstance(form, TestForm)
    data = form.read()

    assert data["h3"] == "test test"
    assert data["Nested1"]["input1"] == ""
    assert not data["Nested1"]["Nested2"]["input2"]

    assert form.fill(
        {
            "Nested1.input1": "foobar",
            "Nested1.Nested2.input2": True,
        }
    )

    assert form.Nested1.input1.read() == "foobar"
    assert form.Nested1.Nested2.input2.read()

    assert form.Nested1.Nested2.input2.hierarchy == [
        form,
        form.Nested1,
        form.Nested1.Nested2,
        form.Nested1.Nested2.input2,
    ]
    assert form.hierarchy == [form]

    assert form.Nested1.Nested2.input2.locatable_parent is None


def test_table(browser):
    class TestForm(View):
        table = Table("#with-thead")
        table1 = Table(
            "#rowcolspan_table",
            column_widgets={
                "First Name": TextInput(locator="./input"),
                "Last Name": TextInput(locator="./input"),
                "Widget": TextInput(locator="./input"),
            },
        )

    view = TestForm(browser)
    assert view.table.headers == (None, "Column 1", "Column 2", "Column 3", "Column 4")
    assert view.table1.headers == ("#", "First Name", "Last Name", "Username", "Widget")
    assert view.table1.caption == "Some caption"
    dir(view.table[0])
    assert len(list(view.table.rows())) == 3
    assert len(list(view.table1.rows())) == 8

    assert len(list(view.table.rows(column_1="qwer"))) == 1
    assert len(list(view.table1.rows(first_name="Mark"))) == 1

    assert len(list(view.table.rows(column_1__startswith="bar_"))) == 2
    assert len(list(view.table1.rows(username__startswith="@psav"))) == 2

    assert len(list(view.table.rows(column_1__contains="_"))) == 2
    assert len(list(view.table1.rows(first_name__contains="Mike"))) == 2

    assert len(list(view.table.rows(column_1__endswith="_x"))) == 1
    assert len(list(view.table1.rows(last_name__endswith="Thornton"))) == 1

    assert len(list(view.table.rows(column_1__startswith="bar_", column_1__endswith="_x"))) == 1
    assert (
        len(list(view.table1.rows(first_name__startswith="Larry", first_name__endswith="Bird")))
        == 1
    )

    assert len(list(view.table.rows(_row__attr=("data-test", "def-345")))) == 1
    assert len(list(view.table1.rows(_row__attr=("data-test", "def-345")))) == 1

    assert len(list(view.table.rows(_row__attr_startswith=("data-test", "abc")))) == 2
    assert len(list(view.table1.rows(_row__attr_startswith=("data-test", "abc")))) == 2

    assert len(list(view.table.rows(_row__attr_endswith=("data-test", "345")))) == 2
    assert len(list(view.table1.rows(_row__attr_endswith=("data-test", "345")))) == 2

    assert len(list(view.table.rows(_row__attr_contains=("data-test", "3")))) == 3
    assert len(list(view.table1.rows(_row__attr_contains=("data-test", "3")))) == 3

    assert (
        len(
            list(
                view.table.rows(
                    _row__attr_contains=("data-test", "3"),
                    _row__attr_startswith=("data-test", "abc"),
                )
            )
        )
        == 2
    )
    assert (
        len(
            list(
                view.table1.rows(
                    _row__attr_contains=("data-test", "3"),
                    _row__attr_startswith=("data-test", "abc"),
                )
            )
        )
        == 2
    )

    assert len(list(view.table.rows(_row__attr=("data-test", "abc-345"), column_1="qwer"))) == 0
    assert len(list(view.table1.rows(_row__attr=("data-test", "abc-345"), first_name="qwer"))) == 0

    with pytest.raises(ValueError):
        list(view.table.rows(_row__papalala=("foo", "bar")))

    with pytest.raises(ValueError):
        list(view.table1.rows(_row__papalala=("foo", "bar")))

    with pytest.raises(ValueError):
        list(view.table.rows(_row__attr_papalala=("foo", "bar")))

    with pytest.raises(ValueError):
        list(view.table1.rows(_row__attr_papalala=("foo", "bar")))

    with pytest.raises(ValueError):
        list(view.table.rows(_row__attr="foobar"))

    with pytest.raises(ValueError):
        list(view.table1.rows(_row__attr="foobar"))

    assert len(list(view.table.rows((0, "asdf")))) == 1
    assert len(list(view.table.rows((1, "startswith", "bar_")))) == 2
    assert len(list(view.table.rows((1, "startswith", "bar_"), column_1__endswith="_x"))) == 1

    assert len(list(view.table1.rows((0, "1")))) == 1
    assert len(list(view.table1.rows((1, "startswith", "Jacob")))) == 1
    assert len(list(view.table1.rows((1, "startswith", "Jacob"), username__endswith="at"))) == 1

    assert len(list(view.table.rows((1, re.compile(r"_x$"))))) == 1
    assert len(list(view.table.rows((1, re.compile(r"^bar_"))))) == 2
    assert len(list(view.table.rows(("column_1", re.compile(r"^bar_"))))) == 2
    assert len(list(view.table.rows(("Column 1", re.compile(r"^bar_"))))) == 2
    assert len(list(view.table.rows((0, re.compile(r"^foo_")), (3, re.compile(r"_x$"))))) == 1
    assert (
        len(
            list(
                view.table.rows(
                    (0, re.compile(r"^foo_")),
                    (1, "contains", "_"),
                    column_3__endswith="_x",
                )
            )
        )
        == 1
    )

    assert len(list(view.table1.rows((1, re.compile(r"Mark$"))))) == 1
    assert len(list(view.table1.rows((1, re.compile(r"^Jacob"))))) == 1
    assert len(list(view.table1.rows(("Last Name", re.compile(r"^Otto"))))) == 1
    assert len(list(view.table1.rows((0, re.compile(r"^2")), (3, re.compile(r"fat$"))))) == 1
    assert (
        len(
            list(
                view.table1.rows(
                    (0, re.compile(r"^4")),
                    (1, "contains", " "),
                    username__endswith="psav",
                )
            )
        )
        == 1
    )

    row = view.table.row((0, re.compile(r"^foo_")), (1, "contains", "_"), column_3__endswith="_x")
    assert row[0].text == "foo_x"

    row = view.table1.row(
        (0, re.compile(r"^5")), (1, "contains", "Shriver"), username__endswith="ver"
    )
    assert row[1].text == "Mike Shriver"

    #  attributized columns for a table with thead
    row = view.table.row(column_1="bar_x")
    assert row[0].text == "foo_x"
    assert row["Column 1"].text == "bar_x"
    assert row.column_1.text == "bar_x"

    assert row.read() == {
        0: "foo_x",
        "Column 1": "bar_x",
        "Column 2": "baz_x",
        "Column 3": "bat_x",
        "Column 4": "",
    }

    unpacking_fake_read = [(header, column.text) for header, column in row]
    assert unpacking_fake_read == [
        (None, "foo_x"),
        ("Column 1", "bar_x"),
        ("Column 2", "baz_x"),
        ("Column 3", "bat_x"),
        ("Column 4", ""),
    ]

    assert view.table[0].column_2.text == "yxcv"

    row = view.table1.row(username="@slacker")
    assert row[0].text == "3"
    assert row["First Name"].text == "Larry the Bird"
    assert row.first_name.text == "Larry the Bird"

    assert row.read() == {
        "#": "3",
        "First Name": "Larry the Bird",
        "Last Name": "Larry the Bird",
        "Username": "@slacker",
        "Widget": "widget3",
    }

    unpacking_fake_read = [(header, column.text) for header, column in row]
    assert unpacking_fake_read == [
        ("#", "3"),
        ("First Name", "Larry the Bird"),
        ("Last Name", "Larry the Bird"),
        ("Username", "@slacker"),
        ("Widget", ""),
    ]

    assert view.table1[1].last_name.text == "Thornton"

    with pytest.raises(AttributeError):
        row.papalala

    with pytest.raises(TypeError):
        view.table["boom!"]

    with pytest.raises(IndexError):
        view.table[1000]

    row = next(view.table.rows())
    assert row.column_1.text == "qwer"

    row = next(view.table1.rows())
    assert row.first_name.text == "Mark"

    assert view.table1.read() == [
        {
            "#": "1",
            "First Name": "Mark",
            "Last Name": "Otto",
            "Username": "@mdo",
            "Widget": "widget1",
        },
        {
            "#": "2",
            "First Name": "Jacob",
            "Last Name": "Thornton",
            "Username": "@fat",
            "Widget": "widget2",
        },
        {
            "#": "3",
            "First Name": "Larry the Bird",
            "Last Name": "Larry the Bird",
            "Username": "@slacker",
            "Widget": "widget3",
        },
        {
            "#": "4",
            "First Name": "Pete Savage",
            "Last Name": "",
            "Username": "@psav",
            "Widget": "widget41",
        },
        {
            "#": "4",
            "First Name": "Pete Savage",
            "Last Name": "",
            "Username": "@psav1",
            "Widget": "widget42",
        },
        {
            "#": "5",
            "First Name": "Mike Shriver",
            "Last Name": "Mike Shriver",
            "Username": "@mshriver",
            "Widget": "widget51",
        },
        {
            "#": "5",
            "First Name": "Mike Shriver",
            "Last Name": "Mike Shriver",
            "Username": "@iamhero",
            "Widget": "widget52",
        },
        {
            "#": "6",
            "First Name": "",
            "Last Name": "",
            "Username": "@blabla",
            "Widget": "widget6",
        },
    ]


def test_table_multiple_tbody(browser):
    class TBodyRow(TableRow):
        ROW = "./tr[1]"
        HIDDEN_CONTENT = "./tr[2]/td[1]"

        def __init__(self, parent, index, logger=None):
            super().__init__(parent, index, logger=logger)
            self.hidden_content = Text(parent=self, locator=self.HIDDEN_CONTENT)

        @property
        def is_displayed(self):
            return self.browser.is_displayed(self.ROW, parent=self)

    class TBodyTable(Table):
        ROWS = "./tbody"
        ROW_RESOLVER_PATH = "/table/tbody"
        ROW_AT_INDEX = "./tbody[{0}]"
        COLUMN_RESOLVER_PATH = "/tr[0]/td"
        COLUMN_AT_POSITION = "./tr[1]/td[{0}]"
        ROW_TAG = "tbody"
        Row = TBodyRow

    class TestForm(View):
        table1 = TBodyTable(
            "#multiple_tbody_table",
            column_widgets={
                "First Name": TextInput(locator="./input"),
                "Last Name": TextInput(locator="./input"),
                "Widget": TextInput(locator="./input"),
            },
        )

    view = TestForm(browser)

    assert view.table1.headers == ("#", "First Name", "Last Name", "Username", "Widget")
    assert view.table1.caption == "Some caption"
    assert len(list(view.table1.rows())) == 3

    assert len(list(view.table1.rows(first_name="Mark"))) == 1
    assert len(list(view.table1.rows(username__startswith="@slacker"))) == 1
    assert (
        len(list(view.table1.rows(first_name__startswith="Larry", first_name__endswith="Bird")))
        == 1
    )
    assert len(list(view.table1.rows(_row__attr=("data-test", "def-345")))) == 1
    assert len(list(view.table1.rows(_row__attr_startswith=("data-test", "abc")))) == 2
    assert len(list(view.table1.rows(_row__attr_endswith=("data-test", "345")))) == 2
    assert len(list(view.table1.rows(_row__attr_contains=("data-test", "3")))) == 3
    assert (
        len(
            list(
                view.table1.rows(
                    _row__attr_contains=("data-test", "3"),
                    _row__attr_startswith=("data-test", "abc"),
                )
            )
        )
        == 2
    )
    assert len(list(view.table1.rows(_row__attr=("data-test", "abc-345"), first_name="qwer"))) == 0

    with pytest.raises(ValueError):
        list(view.table1.rows(_row__papalala=("foo", "bar")))

    with pytest.raises(ValueError):
        list(view.table1.rows(_row__attr_papalala=("foo", "bar")))

    with pytest.raises(ValueError):
        list(view.table1.rows(_row__attr="foobar"))

    assert len(list(view.table1.rows((0, "1")))) == 1
    assert len(list(view.table1.rows((1, "startswith", "Jacob")))) == 1
    assert len(list(view.table1.rows((1, "startswith", "Jacob"), username__endswith="at"))) == 1

    assert len(list(view.table1.rows((1, re.compile(r"Mark$"))))) == 1
    assert len(list(view.table1.rows((1, re.compile(r"^Jacob"))))) == 1
    assert len(list(view.table1.rows(("Last Name", re.compile(r"^Otto"))))) == 1
    assert len(list(view.table1.rows((0, re.compile(r"^2")), (3, re.compile(r"fat$"))))) == 1

    row = view.table1.row(username="@slacker")
    assert row[0].text == "3"
    assert row["First Name"].text == "Larry the Bird"
    assert row.first_name.text == "Larry the Bird"

    assert row.read() == {
        "#": "3",
        "First Name": "Larry the Bird",
        "Last Name": "Larry the Bird",
        "Username": "@slacker",
        "Widget": "widget3",
    }

    unpacking_fake_read = [(header, column.text) for header, column in row]
    assert unpacking_fake_read == [
        ("#", "3"),
        ("First Name", "Larry the Bird"),
        ("Last Name", "Larry the Bird"),
        ("Username", "@slacker"),
        ("Widget", ""),
    ]

    assert view.table1[1].last_name.text == "Thornton"

    with pytest.raises(AttributeError):
        row.papalala

    with pytest.raises(TypeError):
        view.table1["boom!"]

    with pytest.raises(IndexError):
        view.table1[1000]

    row = next(view.table1.rows())
    assert row.first_name.text == "Mark"

    assert view.table1.read() == [
        {
            "#": "1",
            "First Name": "Mark",
            "Last Name": "Otto",
            "Username": "@mdo",
            "Widget": "widget1",
        },
        {
            "#": "2",
            "First Name": "Jacob",
            "Last Name": "Thornton",
            "Username": "@fat",
            "Widget": "widget2",
        },
        {
            "#": "3",
            "First Name": "Larry the Bird",
            "Last Name": "Larry the Bird",
            "Username": "@slacker",
            "Widget": "widget3",
        },
    ]

    for row in view.table1:
        assert row.is_displayed
        assert not row.hidden_content.is_displayed


def test_table_no_header(browser):
    class TestForm(View):
        nohead_table = Table("#without_thead")

    view = TestForm(browser)
    # attributized columns for a table withOUT thead
    row = view.nohead_table.row(event="Some Event")
    assert row[0].text == "27.02.2017, 12:19:30"
    assert row["Event"].text == "Some Event"
    assert row.event.text == "Some Event"

    assert row.read() == {"Date": "27.02.2017, 12:19:30", "Event": "Some Event"}
    # headers are read correctly when those aren't in thead
    assert len(view.nohead_table.headers) == 2

    row = next(view.nohead_table.rows())
    assert row.event.text == "Some Event"


def test_table_negative_row_index(browser):
    class TestForm(View):
        table = Table("#with-thead")

    view = TestForm(browser)
    assert view.table[-1].read() == {
        0: "foo_y",
        "Column 1": "bar_y",
        "Column 2": "baz_y",
        "Column 3": "bat_y",
        "Column 4": "",
    }
    assert view.table[-2].read() == {
        0: "foo_x",
        "Column 1": "bar_x",
        "Column 2": "baz_x",
        "Column 3": "bat_x",
        "Column 4": "",
    }
    assert view.table[-3].read() == {
        0: "asdf",
        "Column 1": "qwer",
        "Column 2": "yxcv",
        "Column 3": "uiop",
        "Column 4": "",
    }
    assert view.table[0].read() == {
        0: "asdf",
        "Column 1": "qwer",
        "Column 2": "yxcv",
        "Column 3": "uiop",
        "Column 4": "",
    }

    with pytest.raises(IndexError):
        view.table[-4].read()


def test_table_with_widgets(browser):
    class TestForm(View):
        table = Table(
            "#withwidgets",
            column_widgets={
                "Column 2": TextInput(locator="./input"),
                "Column 3": VersionPick(
                    {Version.lowest(): TextInput(locator="./input"), "2.0": None}
                ),
            },
        )

    view = TestForm(browser)

    class TestForm1(View):
        table1 = Table(
            "#rowcolspan_table",
            column_widgets={
                "First Name": TextInput(locator="./input"),
                "Last Name": TextInput(locator="./input"),
                "Widget": TextInput(locator="./input"),
            },
        )

    view1 = TestForm1(browser)

    assert view.read() == {
        "table": [
            {0: "foo", "Column 2": "", "Column 3": "foo col 3"},
            {0: "bar", "Column 2": "bar col 2", "Column 3": ""},
        ]
    }
    assert view.fill({"table": [{"Column 2": "foobaaar"}]})
    assert not view.fill({"table": [{"Column 2": "foobaaar"}]})
    assert view.read() == {
        "table": [
            {0: "foo", "Column 2": "foobaaar", "Column 3": "foo col 3"},
            {0: "bar", "Column 2": "bar col 2", "Column 3": ""},
        ]
    }

    assert view.fill({"table": [{}, {"Column 3": "yolo"}]})
    assert view.read() == {
        "table": [
            {0: "foo", "Column 2": "foobaaar", "Column 3": "foo col 3"},
            {0: "bar", "Column 2": "bar col 2", "Column 3": "yolo"},
        ]
    }

    assert view1.table1[7]["First Name"].fill("some value")
    assert view1.table1[7]["First Name"].read() == "some value"

    assert view1.table1[7]["Last Name"].fill("new value")
    assert view1.table1[7]["Last Name"].read() == "new value"

    old_state = view1.table1.read()
    ending = " updated"
    for row in view1.table1.rows():
        cell = row["Widget"]
        value = cell.read()
        row["Widget"].fill(str(value) + ending)
    assert old_state != view1.table1.read()

    for row in view1.table1.rows():
        cell = row["Widget"]
        value = cell.read()
        row["Widget"].fill(str(value)[: -len(ending)])
    assert old_state == view1.table1.read()

    with pytest.raises(TypeError):
        # There is nothing to be filled
        view.fill({"table": [{0: "explode"}]})

    with pytest.raises(TypeError):
        # No assoc_column
        view.fill({"table": {0: {"Column 2": "lalala"}}})

    with pytest.raises(ValueError):
        # No assoc_column - no implicit column name for filling
        view.fill({"table": [{}, ""]})


def test_table_with_widgets_and_assoc_column(browser):
    class TestForm(View):
        table = Table(
            "#withwidgets",
            column_widgets={
                "Column 2": TextInput(locator="./input"),
                "Column 3": TextInput(locator="./input"),
            },
            assoc_column=0,
        )

    view = TestForm(browser)

    assert view.read() == {
        "table": {
            "foo": {"Column 2": "", "Column 3": "foo col 3"},
            "bar": {"Column 2": "bar col 2", "Column 3": ""},
        }
    }
    assert view.fill({"table": {"foo": {"Column 2": "foobaaar"}}})
    assert not view.fill({"table": {"foo": {"Column 2": "foobaaar"}}})
    assert view.read() == {
        "table": {
            "foo": {"Column 2": "foobaaar", "Column 3": "foo col 3"},
            "bar": {"Column 2": "bar col 2", "Column 3": ""},
        }
    }

    assert view.fill({"table": {"bar": {"Column 3": "yolo"}}})
    assert view.read() == {
        "table": {
            "foo": {"Column 2": "foobaaar", "Column 3": "foo col 3"},
            "bar": {"Column 2": "bar col 2", "Column 3": "yolo"},
        }
    }

    assert view.table["bar"]["Column 2"].read() == "bar col 2"


def test_table_row_ignore_bottom(browser):
    class TestForm(View):
        table = Table(
            "#withwidgets",
            column_widgets={
                "Column 2": TextInput(locator="./input"),
                "Column 3": TextInput(locator="./input"),
            },
            rows_ignore_bottom=1,
        )

    view = TestForm(browser)

    assert view.read() == {"table": [{0: "foo", "Column 2": "", "Column 3": "foo col 3"}]}


def test_table_row_ignore_top(browser):
    class TestForm(View):
        table = Table(
            "#withwidgets",
            column_widgets={
                "Column 2": TextInput(locator="./input"),
                "Column 3": TextInput(locator="./input"),
            },
            rows_ignore_top=1,
        )

    view = TestForm(browser)

    assert view.read() == {"table": [{0: "bar", "Column 2": "bar col 2", "Column 3": ""}]}


def test_table_row_ignore_bottom_and_top(browser):
    class TestForm(View):
        table = Table(
            "#withwidgets",
            column_widgets={
                "Column 2": TextInput(locator="./input"),
                "Column 3": TextInput(locator="./input"),
            },
            rows_ignore_bottom=1,
            rows_ignore_top=1,
        )

    view = TestForm(browser)

    assert view.read() == {"table": []}


def test_table_dynamic_add_not_assoc(browser):
    class MyTable(Table):
        def row_add(self):
            # using root_browser as ROOT will be table locator and this is outof dom.
            el = self.root_browser.element('//button[@id="dynamicadd"]')
            self.browser.click(el)
            return -1

    class MyView(View):
        table = MyTable(
            "#dynamic",
            column_widgets={
                "First Name": TextInput(locator="./input"),
                "Last Name": TextInput(locator="./input"),
            },
        )

    view = MyView(browser)
    assert view.table.read() == []
    assert view.table.fill([{"First Name": "John", "Last Name": "Doe"}])
    assert view.table.read() == [{"ID": "1.", "First Name": "John", "Last Name": "Doe"}]
    assert not view.table.fill([{"First Name": "John", "Last Name": "Doe"}])
    assert not view.table.fill(view.table.read())
    changes = view.table.read()
    changes[0]["First Name"] = "Jane"
    assert view.table.fill(changes)
    del changes[0]["First Name"]
    changes[0][1] = "John"
    assert view.table.fill(changes)
    assert view.table.read() == [{"ID": "1.", "First Name": "John", "Last Name": "Doe"}]

    # Now the error test!
    changes[0]["ID"] = "blabber!"
    with pytest.raises(TypeError):
        view.table.fill(changes)


def test_table_dynamic_add_assoc(browser):
    class MyTable(Table):
        def row_add(self):
            # using root_browser as ROOT will be table locator and this is outof dom.
            self.root_browser.click('//button[@id="dynamicadd"]')
            return -1  # testing negative index when we expect row to be added to end of table

    class MyView(View):
        table = MyTable(
            "#dynamic",
            column_widgets={
                "First Name": TextInput(locator="./input"),
                "Last Name": TextInput(locator="./input"),
            },
            assoc_column="First Name",
        )

    view = MyView(browser)
    assert view.table.read() == {}
    assert view.table.row_count == 0
    assert view.table.fill({"John": {"Last Name": "Doe"}})
    assert view.table.row_count == 1
    assert view.table.read() == {"John": {"Last Name": "Doe", "ID": "1."}}
    assert view.table.row_count == 1
    assert view.table.fill({"John": {"Last Name": "Doh"}})
    assert view.table.row_count == 1
    assert view.table.read() == {"John": {"Last Name": "Doh", "ID": "1."}}
    assert view.table.fill({"Pepa": {"Last Name": "Z Depa"}})
    assert view.table.row_count == 2
    assert view.table.read() == {
        "John": {"Last Name": "Doh", "ID": "1."},
        "Pepa": {"Last Name": "Z Depa", "ID": "2."},
    }
    assert not view.table.fill(view.table.read())
    assert not view.fill(view.read())


def test_simple_select(browser):
    class TestForm(View):
        select = Select(name="testselect1")

    view = TestForm(browser)

    assert not view.select.is_multiple
    assert not view.select.classes
    assert view.select.all_options == [("Foo", "foo"), ("Bar", "bar")]

    assert len(view.select.all_selected_options) == 1

    assert view.select.first_selected_option in view.select.all_selected_options
    assert view.select.first_selected_option == "Foo"

    with pytest.raises(NotImplementedError):
        view.select.deselect_all()

    assert view.select.get_value_by_text("Foo") == "foo"

    view.select.select_by_value("bar")
    assert view.select.first_selected_option == "Bar"

    with pytest.raises(ValueError):
        view.select.select_by_value("bar", "foo")

    view.select.select_by_visible_text("Foo")
    assert view.select.first_selected_option == "Foo"

    view.select.select_by_visible_text("Bar")
    assert view.select.first_selected_option == "Bar"

    with pytest.raises(ValueError):
        view.select.select_by_visible_text("Bar", "Foo")

    view.select.fill("Foo")
    assert view.select.read() == "Foo"

    view.select.fill(["Bar"])
    assert view.select.read() == "Bar"

    view.select.fill(("by_value", "foo"))
    assert view.select.read() == "Foo"

    view.select.fill(("by_value", "bar"))
    assert view.select.read() == "Bar"

    with pytest.raises(ValueError):
        view.select.fill(("foo", "bar"))

    with pytest.raises(ValueError):
        view.select.fill((123, "bad modifier"))

    with pytest.raises(ValueError):
        view.select.fill(("a", "long", "tuple"))

    with pytest.raises(ValueError):
        view.select.fill(("a short tuple",))


def test_multi_select(browser):
    class TestForm(View):
        select = Select(name="testselect2")

    view = TestForm(browser)

    assert view.select.is_multiple
    assert view.select.classes == {"xfoo", "xbar"}
    assert view.select.all_options == [("Foo", "foo"), ("Bar", "bar"), ("Baz", "baz")]

    view.select.select_by_visible_text("Foo", "Bar")
    assert view.select.all_selected_options == ["Foo", "Bar"]

    view.select.deselect_all()
    assert not view.select.all_selected_options

    view.select.select_by_value("foo", "bar")
    assert view.select.all_selected_values == ["foo", "bar"]

    view.select.deselect_all()
    assert not view.select.all_selected_options

    assert view.select.read() == []
    assert not view.select.fill(None)
    assert view.select.fill("Foo")
    assert view.select.read() == ["Foo"]
    assert view.select.fill(["Foo", "Bar"])
    assert view.select.read() == ["Foo", "Bar"]
    assert not view.select.fill(["Foo", "Bar"])

    assert view.select.fill(("by_value", "baz"))
    assert view.select.read() == ["Baz"]

    assert view.select.fill(["Foo", ("by_value", "bar")])
    assert view.select.read() == ["Foo", "Bar"]


def test_parametrized_locator(browser):
    class TestForm(View):
        my_value = 3
        header = Text(ParametrizedString(".//h{header}"))
        header_cls = Text(ParametrizedString(".//h{@my_value}"))
        input = TextInput(name=ParametrizedString("input{input}"))

    good = TestForm(browser, additional_context={"header": 3, "input": 1})
    assert good.header.text == "test test"
    assert good.header_cls.text == "test test"
    good.input.fill("")
    assert good.input.read() == ""
    assert good.input.fill("foo")
    assert good.input.read() == "foo"

    bad = TestForm(browser)
    # This uses value defined on class so it should work
    assert good.header_cls.text == "test test"
    with pytest.raises(AttributeError):
        bad.header.text

    with pytest.raises(AttributeError):
        bad.input.read()


@pytest.mark.parametrize("style", ["callable", "clickable", "string"])
def test_fill_with(browser, style):
    class TestForm(View):
        i1 = TextInput(name="fill_with_1")
        i2 = TextInput(name="fill_with_2")
        i3 = TextInput(name="fill_with_3")

        b1 = Text('//button[@id="fill_with_button_1"]')
        b2 = Text('//button[@id="fill_with_button_2"]')

    view = TestForm(browser)
    if style == "callable":
        assert view.fill_with({"i1": "foo"}, on_change=view.b1.click, no_change=view.b2.click)
        assert view.read()["i1"] == "foo"
        assert "clicked" in browser.classes(view.b1)
        assert "clicked" not in browser.classes(view.b2)
        # Reset classes
        browser.set_attribute("class", "", view.b1)
        browser.set_attribute("class", "", view.b2)

        assert not view.fill_with({"i1": "foo"}, on_change=view.b1.click, no_change=view.b2.click)
        assert view.read()["i1"] == "foo"
        assert "clicked" not in browser.classes(view.b1)
        assert "clicked" in browser.classes(view.b2)
    elif style == "clickable":
        assert view.fill_with({"i1": "foo"}, on_change=view.b1, no_change=view.b2)
        assert view.read()["i1"] == "foo"
        assert "clicked" in browser.classes(view.b1)
        assert "clicked" not in browser.classes(view.b2)
        # Reset classes
        browser.set_attribute("class", "", view.b1)
        browser.set_attribute("class", "", view.b2)

        assert not view.fill_with({"i1": "foo"}, on_change=view.b1, no_change=view.b2)
        assert view.i1.value == "foo"
        assert "clicked" not in browser.classes(view.b1)
        assert "clicked" in browser.classes(view.b2)
    elif style == "string":
        assert view.fill_with({"i1": "foo"}, on_change="b1", no_change="b2")
        assert view.read()["i1"] == "foo"
        assert "clicked" in browser.classes(view.b1)
        assert "clicked" not in browser.classes(view.b2)
        # Reset classes
        browser.set_attribute("class", "", view.b1)
        browser.set_attribute("class", "", view.b2)

        assert not view.fill_with({"i1": "foo"}, on_change="b1", no_change="b2")
        assert view.read()["i1"] == "foo"
        assert "clicked" not in browser.classes(view.b1)
        assert "clicked" in browser.classes(view.b2)
    else:
        pytest.fail(f"bad param {style}")


def test_with_including(browser):
    class TestForm1(View):
        h3 = Text(".//h3")

    class TestForm2(View):
        caption = View.include(TestForm1)
        input1 = TextInput(name="input1")
        input2 = Checkbox(id="input2")

    class TestForm3(View):
        fileinput = FileInput(id="fileinput")
        inputs = View.include(TestForm2)

    class TestForm4(TestForm3):
        title = Text(locator="//h1")

    class TestForm5(View):
        fileinput = FileInput(id="fileinput")
        inputs = View.include(TestForm2, use_parent=True)

    class TestForm6(TestForm5):
        input6 = TextInput(id="input")

    class AFillable(Fillable):
        def __init__(self, text):
            self.text = text

        def as_fill_value(self):
            return self.text

    form = TestForm4(browser)
    # This repeats test_basic_widgets
    assert isinstance(form, TestForm4)
    data = form.read()
    assert data["h3"] == "test test"
    assert data["input1"] == ""
    assert not data["input2"]
    assert not form.fill({"input2": False})
    assert form.fill({"input2": True})
    assert not form.fill({"input2": True})
    assert form.input2.read()

    assert form.fill({"input1": "foo"})
    assert not form.fill({"input1": "foo"})
    assert form.fill({"input1": "foobar"})
    assert not form.fill({"input1": "foobar"})
    assert form.fill(data)

    assert form.fill({"input1": AFillable("wut")})
    assert not form.fill({"input1": AFillable("wut")})
    assert form.read()["input1"] == "wut"
    assert form.input1.fill(AFillable("a_test"))
    assert not form.input1.fill(AFillable("a_test"))
    assert form.input1.read() == "a_test"
    assert form.title.text == "Hello"
    assert isinstance(form.input1.parent.parent, type(browser))

    form2 = TestForm6(browser)
    assert isinstance(form2.input1.parent.parent, TestForm6)

    form2.fill({"input6": "some input"})
    assert form2.input6.read() == "some input"
    form2.fill({"fileinput": "/etc/resolv.conf"})
    assert form2.fill({"input1": "typed into input 1"})
    assert form2.input1.read() == "typed into input 1"
    assert form2.h3.read() == "test test"

    assert form.fileinput.fill("/etc/resolv.conf")
    with pytest.raises(DoNotReadThisWidget):
        form.fileinput.read()
