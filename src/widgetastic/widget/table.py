"""This module contains the base classes that are used to implement the more specific behaviour."""
import itertools
import re
from collections import defaultdict
from collections import deque
from copy import copy
from operator import attrgetter

from anytree import AsciiStyle
from anytree import ChildResolverError
from anytree import Node
from anytree import RenderTree
from anytree import Resolver
from anytree import ResolverError
from cached_property import cached_property

from .base import ClickableMixin
from .base import Widget
from .base import Widgetable
from .base import WidgetDescriptor
from widgetastic.browser import Browser
from widgetastic.exceptions import RowNotFound
from widgetastic.log import create_child_logger
from widgetastic.log import create_item_logger
from widgetastic.utils import attributize_string
from widgetastic.utils import ConstructorResolvable
from widgetastic.utils import ParametrizedLocator
from widgetastic.xpath import quote

# Python 3.7 formalised the RE pattern type, so let's use that if we can
try:
    Pattern = re.Pattern  # type: ignore
except AttributeError:
    Pattern = re._pattern_type  # type: ignore


def resolve_table_widget(parent, wcls):
    """
    Used for applying a parent to a WidgetDescriptor passed in at Table init time.

    This turns the WidgetDescriptor into a completed Widget, tied to the
    appropriate parent.

    For example, if you pass in 'column_widgets' to a table like so:
    {'columnA': MyWidget(somearg1, somearg2)}

    Then upon calling the TableColumn '.widget' function, this function will resolve
    the "MyWidget" WidgetDescriptor into a "MyWidget" Widget with parent set to the TableColumn.
    """
    if not isinstance(parent, (Browser, Widget)):
        raise TypeError("'parent' must be an instance of widgetastic.Widget or widgetastic.Browser")

    # Verpick, ...
    if isinstance(wcls, ConstructorResolvable):
        return wcls.resolve(parent)

    # We cannot use WidgetDescriptor's facility for instantiation as it does caching and all
    # that stuff
    args = ()
    kwargs = {}

    if isinstance(wcls, WidgetDescriptor):
        args = wcls.args
        kwargs.update(wcls.kwargs)
        wcls = wcls.klass
    if "logger" not in kwargs:
        kwargs["logger"] = create_child_logger(parent.logger, wcls.__name__)
    return wcls(parent, *args, **kwargs)


class TableColumn(Widget, ClickableMixin):
    """Represents a cell in the row."""

    def __init__(self, parent, position, absolute_position=None, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.position = position  # relative position
        self.absolute_position = absolute_position  # absolute position according to row/colspan

    def __locator__(self):
        return self.parent.table.COLUMN_AT_POSITION.format(self.position + 1)

    def __repr__(self):
        return f"{type(self).__name__}({self.parent!r}, {self.position!r})"

    @property
    def column_name(self):
        """If there is a name associated with this column, return it. Otherwise returns None."""
        try:
            if self.absolute_position and self.absolute_position != self.position:
                position = self.absolute_position
            else:
                position = self.position
            return self.row.position_to_column_name(position)
        except KeyError:
            return None

    @cached_property
    def widget(self):
        """Returns the associated widget if defined. If there is none defined, returns None."""
        if self.absolute_position and self.absolute_position != self.position:
            position = self.absolute_position
        else:
            position = self.position

        if self.column_name is None:
            if position not in self.table.column_widgets:
                return None
            wcls = self.table.column_widgets[position]
        else:
            if self.column_name not in self.table.column_widgets:
                return None
            wcls = self.table.column_widgets[self.column_name]
        return resolve_table_widget(self, wcls)

    @property
    def text(self):
        return self.browser.text(self)

    @property
    def row(self):
        return self.parent

    @property
    def table(self):
        return self.row.table

    def read(self):
        """Reads the content of the cell. If widget is present and visible, it is read, otherwise
        the text of the cell is returned.
        """
        if self.widget is not None and self.widget.is_displayed:
            return self.widget.read()
        else:
            return self.text

    def fill(self, value):
        """Fills the cell with the value if the widget is present. If not, raises a TypeError."""
        if self.widget is not None:
            return self.widget.fill(value)
        else:
            if self.text == str(value):
                self.logger.debug(
                    "Not filling %d because it already has value %r even though there is no widget",
                    self.column_name or self.position,
                    value,
                )
                return False
            else:
                raise TypeError(
                    (
                        "Cannot fill column {}, no widget and the value differs "
                        "(wanted to fill {!r} but there is {!r}"
                    ).format(self.column_name or self.position, value, self.text)
                )


class TableReference(Widgetable):
    """Represents rowspan/colspan column.
    It has a reference to real objects and re-directs all method calls to real object.
    """

    def __init__(self, parent, reference):
        self.parent = parent
        self.refers_to = reference

    def __getattr__(self, attr):
        try:
            return getattr(self.refers_to, attr)
        except AttributeError:
            raise AttributeError(f"no {attr} attribute in class {type(self.refers_to)}")

    def __repr__(self):
        return f"{type(self).__name__}({self.refers_to!r})"


class TableRow(Widget, ClickableMixin):
    """Represents a row in the table.

    If subclassing and also changing the Column class, do not forget to set the Column to the new
    class.

    Args:
        index: Position of the row in the table.
    """

    Column = TableColumn

    def __init__(self, parent, index, logger=None):
        Widget.__init__(self, parent, logger=logger)
        self.index = index + 1 if parent._is_header_in_body else index

    @property
    def table(self):
        return self.parent

    def __repr__(self):
        return f"{type(self).__name__}({self.parent!r}, {self.index!r})"

    def __locator__(self):
        return self.parent.ROW_AT_INDEX.format(self.index + 1)

    def position_to_column_name(self, position):
        """Maps the position index into the column name (pretty)"""
        return self.table.index_header_mapping[position]

    def __getitem__(self, item):
        if isinstance(item, str):
            index = self.table.header_index_mapping[self.table.ensure_normal(item)]
        elif isinstance(item, int):
            index = item
        else:
            raise TypeError("row[] accepts only integers and strings")

        if self.table.table_tree:
            # We could find either a TableColumn or a TableReference node at this position...
            cols = self.table.resolver.glob(
                self.table.table_tree,
                "{}[{}]{}[{}]".format(
                    self.table.ROW_RESOLVER_PATH, self.index, self.table.COLUMN_RESOLVER_PATH, index
                ),
                handle_resolver_error=True,
            )
            if not cols:
                raise IndexError(
                    "Row {} has no TableColumn or TableReference node at position {}".format(
                        repr(self), index
                    )
                )
            return cols[0].obj

        else:
            return self.table._create_column(
                self, index, logger=create_item_logger(self.logger, item)
            )

    def __getattr__(self, attr):
        try:
            return self[self.table.ensure_normal(attr)]
        except KeyError:
            raise AttributeError(f"Cannot find column {attr} in the table")

    def __dir__(self):
        parent_dir = dir(super())
        parent_dir.extend(self.table.attributized_headers.keys())
        return sorted(parent_dir)

    def __iter__(self):
        for i, header in enumerate(self.table.headers):
            yield header, self[i]

    def read(self):
        """Read the row - the result is a dictionary"""
        result = {}
        for i, (header, cell) in enumerate(self):
            result[header or i] = cell.read()
        return result

    def fill(self, value):
        """Row filling.

        Accepts either a dictionary or an iterable that can be zipped with headers to create a dict.
        """
        if isinstance(value, (list, tuple)):
            # make it a dict
            value = dict(zip(self.table.headers, value))
        elif not isinstance(value, dict):
            if self.table.assoc_column_position is None:
                raise ValueError(
                    "For filling rows with single value you need to specify assoc_column"
                )
            value = {self.table.assoc_column_position: value}

        changed = False
        for key, value in value.items():
            if value is None:
                self.logger.info("Skipping fill of %r because the value is None", key)
                continue
            else:
                self.logger.info("Filling column %r", key)

            # if the row widgets aren't visible the row needs to be clicked to edit
            if hasattr(self.parent, "action_row") and getattr(self[key], "widget", False):
                if not self[key].widget.is_displayed:
                    self.click()
            if self[key].fill(value):
                changed = True
        return changed


class Table(Widget):
    """Basic table-handling class.

    Usage is as follows assuming the table is instantiated as ``view.table``:

    .. code-block:: python

        # List the headers
        view.table.headers  # => (None, 'something', ...)
        # Access rows by their position
        view.table[0] # => gives you the first row
        # Or you can iterate through rows simply
        for row in view.table:
            do_something()
        # You can filter rows
        # The column names are "attributized"
        view.table.rows(column_name='asdf') # All rows where asdf is in "Column Name"
        # And with Django fashion:
        view.table.rows(column_name__contains='asdf')
        view.table.rows(column_name__startswith='asdf')
        view.table.rows(column_name__endswith='asdf')
        # You can put multiple filters together.
        # And you can of course query a single row
        row = view.table.row(column_name='asdf')
        # You can also look the rows up by their indices
        rows = view.table.rows((0, 'asdf'))  # First column has asdf exactly
        rows = view.table.rows((1, 'contains', 'asdf'))  # Second column contains asdf
        # The partial search methods are the same like for keywords.
        # You can add multiple tuple queries and also combine them with keyword search
        # You are also able to filter based on some row-based filters
        # Yield only those rows who have data-foo=bar in their tr:
        view.table.rows(_row__attr=('data-foo', 'bar'))
        # You can do it similarly for the other operations
        view.table.rows(_row__attr_startswith=('data-foo', 'bar'))
        view.table.rows(_row__attr_endswith=('data-foo', 'bar'))
        view.table.rows(_row__attr_contains=('data-foo', 'bar'))
        # First item in the tuple is the attribute name, second the operand of the operation.
        # It is perfectly possibly to combine these queries with other kinds

        # When you have a row, you can do these things.
        row[0]  # => gives you the first column cell in the row
        row['Column Name'] # => Gives you the column that is named "Column Name". Non-attributized
        row.column_name # => Gives you the column whose attributized name is "column_name"

        # Basic row column can give you text
        assert row.column_name.text == 'some text'
        # Or you can click at it
        assert row.column_name.click()

        # Table cells can contain widgets or whole groups of widgets:
        Table(locator, column_widgets={column_name_or_index: widget_class_or_definition, ...})
        # The on TableColumn instances you can access .widget
        # This is also taken into account with reading or filling
        # For filling such table, fill takes a list, one entry per row, goes from start
        table.fill([{'Column1': 'value1'}, ...])

        # You can also designate one column as "special" associative column using assoc_column
        # You can specify it with column name
        Table(locator, column_widgets={...}, assoc_column='Display Name')
        # Or by the column index
        Table(locator, column_widgets={...}, assoc_column=0)
        # When you use assoc_column, you can use dictionary instead of the list, which means that
        # you can pick the rows to fill by the value in given column.
        # The same example as previous article
        table.fill({'foo': {'Column1': 'value1'}})  # Given that the assoc_column column has 'foo'
                                                    # on that line

    If you subclass :py:class:`Table`, :py:class:`TableRow`, or :py:class:`TableColumn`, do not
    forget to update the :py:attr:`Table.Row` and :py:attr:`TableRow.Column` in order for the
    the Table to use the correct class. You can also adjust the class variable constants to change
    the way :py:class:`Table` looks for rows. For example, you could use the following to create
    a table class that builds rows based on each 'tbody' tag within the table, with each
    row being a custom defined class.

    .. code-block:: python

        class MyCustomTable(Table):
            ROWS = './tbody'
            ROW_RESOLVER_PATH = '/table/tbody'
            ROW_AT_INDEX = './tbody[{0}]'
            COLUMN_RESOLVER_PATH = '/tr[0]/td'
            COLUMN_AT_POSITION = '/tr[1]/td[{0}]'
            ROW_TAG = 'tbody'
            Row = MyCustomTableRowClass

    Args:
        locator: A locator to the table ``<table>`` tag.
        column_widgets: A mapping to widgets that are present in cells. Keys signify column name,
            value is the widget definition.
        assoc_column: Index or name of the column used for associative filling.
        rows_ignore_top: Number of rows to ignore from top when reading/filling.
        rows_ignore_bottom: Number of rows to ignore from bottom when reading/filling.
        top_ignore_fill: Whether to also strip these top rows for fill.
        bottom_ignore_fill: Whether to also strip these top rows for fill.
    """

    ROWS = "./tbody/tr[./td]|./tr[not(./th) and ./td]"

    # Resolve path is used for self.resolver for anytree node lookups
    # where position starts at '0' for elements in the node tree
    ROW_RESOLVER_PATH = "/table/tbody/tr"
    COLUMN_RESOLVER_PATH = "/td"

    # These path vars are used for selenium browser.element lookups,
    # where position starts at '1' for elements
    COLUMN_AT_POSITION = "./td[{0}]"
    ROW_AT_INDEX = "./tbody/tr[{0}]|./tr[not(./th)][{0}]"

    # These tags are not added as Node objects to the table tree when
    # _process_table is called.
    IGNORE_TAGS = ["caption", "thead", "tfoot", "colgroup"]

    ROW_TAG = "tr"
    COLUMN_TAG = "td"
    HEADER_IN_ROWS = "./tbody/tr[1]/th"
    HEADERS = "./thead/tr/th|./tr/th|./thead/tr/td" + "|" + HEADER_IN_ROWS

    ROOT = ParametrizedLocator("{@locator}")

    Row = TableRow

    _CACHED_PROPERTIES = [
        "headers",
        "attributized_headers",
        "header_index_mapping",
        "index_header_mapping",
        "assoc_column_position",
    ]

    def __init__(
        self,
        parent,
        locator,
        column_widgets=None,
        assoc_column=None,
        rows_ignore_top=None,
        rows_ignore_bottom=None,
        top_ignore_fill=False,
        bottom_ignore_fill=False,
        logger=None,
    ):
        Widget.__init__(self, parent, logger=logger)
        self.locator = locator
        self.column_widgets = column_widgets or {}
        self.assoc_column = assoc_column
        self.rows_ignore_top = rows_ignore_top
        self.rows_ignore_bottom = rows_ignore_bottom
        self.top_ignore_fill = top_ignore_fill
        self.bottom_ignore_fill = bottom_ignore_fill
        self.element_id = None
        self._table_tree = None

    def _get_table_tree(self):
        current_element_id = self.browser.element(self).id
        if not self._table_tree or current_element_id != self.element_id:
            # no table tree processed yet, or the table at this locator has changed
            self.element_id = current_element_id
            self._table_tree = self._process_table()
            self._recalc_column_positions(self._table_tree)
        return self._table_tree

    @property
    def table_tree(self):
        if self.has_rowcolspan:
            return self._get_table_tree()

    @table_tree.deleter
    def table_tree(self):
        self._table_tree = None

    @cached_property
    def resolver(self):
        return TableResolver()

    @cached_property
    def caption(self):
        try:
            return self.browser.elements("./caption")[0].text
        except IndexError:
            return None

    def __repr__(self):
        return (
            "{}({!r}, column_widgets={!r}, assoc_column={!r}, rows_ignore_top={!r}, "
            "rows_ignore_bottom={!r})"
        ).format(
            type(self).__name__,
            self.locator,
            self.column_widgets,
            self.assoc_column,
            self.rows_ignore_top,
            self.rows_ignore_bottom,
        )

    def _process_negative_index(self, nindex):
        """The semantics is pretty much the same like for ordinary list.

        There's some funky off-by-1 math here because the index is 1-based and we're replicating
        list negative index access

        Args:
            nindex: negative index
        """
        max_index = self.row_count
        if (-nindex) > max_index:
            raise IndexError(f"Negative index {nindex} wanted but we only have {max_index} rows")
        return max_index + nindex

    def clear_cache(self):
        """Clear all cached properties."""
        for item in self._CACHED_PROPERTIES:
            try:
                delattr(self, item)
            except AttributeError:
                pass
        del self.table_tree

    @cached_property
    def headers(self):
        result = []
        for header in self.browser.elements(self.HEADERS, parent=self):
            result.append(self.browser.text(header).strip() or None)

        without_none = [x for x in result if x is not None]

        if len(without_none) != len(set(without_none)):
            self.logger.warning(
                "Detected duplicate headers in %r. Correct functionality is not guaranteed",
                without_none,
            )

        return tuple(result)

    def ensure_normal(self, name):
        """When you pass string in, it ensures it comes out as non-attributized string."""
        return self.attributized_headers.get(name, name)

    @cached_property
    def attributized_headers(self):
        """Contains mapping between attributized headers and pretty headers"""
        return {attributize_string(h): h for h in self.headers if h is not None}

    @cached_property
    def header_index_mapping(self):
        """Contains mapping between header name (pretty) and position index."""
        return {h: i for i, h in enumerate(self.headers) if h is not None}

    @cached_property
    def index_header_mapping(self):
        """Contains mapping between hposition index and header name (pretty)."""
        return {i: h for h, i in self.header_index_mapping.items()}

    @cached_property
    def assoc_column_position(self):
        """Returns the position of the column specified as associative. If not specified, None
        returned.
        """
        if self.assoc_column is None:
            return None
        elif isinstance(self.assoc_column, int):
            return self.assoc_column
        elif isinstance(self.assoc_column, str):
            if self.assoc_column in self.attributized_headers:
                header = self.attributized_headers[self.assoc_column]
            elif self.assoc_column in self.headers:
                header = self.assoc_column
            else:
                raise ValueError(f"Could not find the assoc_value={self.assoc_column!r} in headers")
            return self.header_index_mapping[header]
        else:
            raise TypeError(
                f"Wrong type passed for assoc_column= : {type(self.assoc_column).__name__}"
            )

    def _create_row(self, parent, index, logger=None):
        """Override these if you wish to change row behavior in a child class."""
        return self.Row(parent, index, logger)

    def _create_column(self, parent, position, absolute_position=None, logger=None):
        """Override this if you wish to change column behavior in a child class."""
        return self.Row.Column(parent, position, absolute_position, logger)

    def __getitem__(self, item):
        if isinstance(item, str):
            if self.assoc_column is None:
                raise TypeError("You cannot use string indices when no assoc_column specified!")
            try:
                row = self.row((self.assoc_column, item))
            except RowNotFound:
                raise KeyError(
                    "Row {!r} not found in table by associative column {!r}".format(
                        item, self.assoc_column
                    )
                )
            at_index = row.index
        elif isinstance(item, int):
            at_index = item
            if at_index >= self.row_count:
                raise IndexError(
                    "Integer row index {} is greater than max index {}".format(
                        at_index, self.row_count - 1
                    )
                )
        else:
            raise TypeError("Table [] accepts only strings or integers.")
        if at_index < 0:
            # To mimic the list handling
            at_index = self._process_negative_index(at_index)

        if self.table_tree:
            nodes = self.resolver.glob(self.table_tree, self.ROW_RESOLVER_PATH)
            at_index = at_index + 1 if self._is_header_in_body else at_index
            try:
                return next(n.obj for n in nodes if n.position == at_index)
            except StopIteration:
                raise RowNotFound(f"Row not found by index {at_index} via {item}")
        else:
            return self._create_row(self, at_index, logger=create_item_logger(self.logger, item))

    def row(self, *extra_filters, **filters):
        try:
            return next(self.rows(*extra_filters, **filters))
        except StopIteration:
            raise RowNotFound(f"Row not found when using filters {extra_filters!r}/{filters!r}")

    def __iter__(self):
        return self.rows()

    def _get_number_preceeding_rows(self, row_el):
        """This is a sort of trick that helps us remove stale element errors.

        We know that correct tables only have ``<tr>`` elements next to each other. We do not want
        to pass around webelements because they can get stale. Therefore this trick will give us the
        number of elements that precede this element, effectively giving us the index of the row.

        How simple.
        """
        return self.browser.execute_script(
            """
            var p = []; var e = arguments[0];
            while (e.previousElementSibling)
                p.push(e = e.previousElementSibling);
            return p.length;
            """,
            row_el,
            silent=True,
        )

    def map_column(self, column):
        """Return column position. Can accept int, normal name, attributized name."""
        if isinstance(column, int):
            return column
        else:
            try:
                return self.header_index_mapping[self.attributized_headers[column]]
            except KeyError:
                try:
                    return self.header_index_mapping[column]
                except KeyError:
                    raise NameError(f"Could not find column {column!r} in the table")

    @cached_property
    def _is_header_in_body(self):
        """Checks whether the header is erroneously specified in the body of table."""
        header_rows = len(self.browser.elements(self.HEADER_IN_ROWS, parent=self))
        return header_rows > 0

    def rows(self, *extra_filters, **filters):
        if not (filters or extra_filters):
            return self._all_rows()
        else:
            return self._filtered_rows(*extra_filters, **filters)

    def _all_rows(self):
        # passing index to TableRow, should not be <1
        # +1 offset on end because xpath index vs 0-based range()
        if self.table_tree:
            for node in self.resolver.glob(self.table_tree, self.ROW_RESOLVER_PATH):
                yield node.obj
        else:
            for row_pos in range(self.row_count):
                yield self._create_row(
                    self, row_pos, logger=create_item_logger(self.logger, row_pos)
                )

    def _process_filters(self, *extra_filters, **filters):
        # Pre-process the filters
        processed_filters = defaultdict(list)
        regexp_filters = []
        row_filters = []
        for filter_column, filter_value in filters.items():
            if filter_column.startswith("_row__"):
                row_filters.append((filter_column.split("__", 1)[-1], filter_value))
                continue
            if "__" in filter_column:
                column, method = filter_column.rsplit("__", 1)
            else:
                column = filter_column
                method = None
                # Check if this is a regular expression object
                if isinstance(filter_value, Pattern):
                    regexp_filters.append((self.map_column(column), filter_value))
                    continue

            processed_filters[self.map_column(column)].append((method, filter_value))

        for argfilter in extra_filters:
            if not isinstance(argfilter, (tuple, list)):
                raise TypeError("Wrong type passed into tuplefilters (expected tuple or list)")
            if len(argfilter) == 2:
                # Column / string match
                column, value = argfilter
                method = None
                # Check if this is a regular expression object
                if isinstance(value, Pattern):
                    regexp_filters.append((self.map_column(column), value))
                    continue
            elif len(argfilter) == 3:
                # Column / method / string match
                column, method, value = argfilter
            else:
                raise ValueError(
                    "tuple filters can only be (column, string) or (column, method, string)"
                )

            processed_filters[self.map_column(column)].append((method, value))

        return processed_filters, regexp_filters, row_filters

    def _build_query(self, processed_filters, row_filters):
        # Build the query
        query_parts = []
        for column_index, matchers in processed_filters.items():
            col_query_parts = []
            for method, value in matchers:
                if method is None:
                    # equals
                    q = f"normalize-space(.)=normalize-space({quote(value)})"
                elif method == "contains":
                    # in
                    q = f"contains(normalize-space(.), normalize-space({quote(value)}))"
                elif method == "startswith":
                    # starts with
                    q = ("starts-with(normalize-space(.), " "normalize-space({}))").format(
                        quote(value)
                    )
                elif method == "endswith":
                    # ends with
                    # This needs to be faked since selenium does not support this feature.
                    q = (
                        "substring(normalize-space(.), "
                        "string-length(normalize-space(.)) - "
                        "string-length({0}) + 1)={0}"
                    ).format(f"normalize-space({quote(value)})")
                else:
                    raise ValueError(f"Unknown method {method}")
                col_query_parts.append(q)

            query_parts.append(
                "{}[{}]".format(
                    self.COLUMN_AT_POSITION.format(column_index + 1), " and ".join(col_query_parts)
                )
            )

        # Row query
        row_parts = []
        for row_action, row_value in row_filters:
            row_action = row_action.lower()
            if row_action.startswith("attr"):
                try:
                    attr_name, attr_value = row_value
                except ValueError:
                    msg = "When passing _row__{}= into the row filter, you must pass it a 2-tuple"
                    raise ValueError(msg.format(row_action))
                if row_action == "attr_startswith":
                    row_parts.append(f"starts-with(@{attr_name}, {quote(attr_value)})")
                elif row_action == "attr":
                    row_parts.append(f"@{attr_name}={quote(attr_value)}")
                elif row_action == "attr_endswith":
                    row_parts.append(
                        (
                            "substring(@{attr}, "
                            "string-length(@{attr}) - string-length({value}) + 1)={value}"
                        ).format(
                            attr=attr_name,
                            value=f"normalize-space({quote(attr_value)})",
                        )
                    )
                elif row_action == "attr_contains":
                    row_parts.append(f"contains(@{attr_name}, {quote(attr_value)})")
                else:
                    raise ValueError(f"Unsupported action {row_action}")
            else:
                raise ValueError(f"Unsupported action {row_action}")

        if query_parts and row_parts:
            query = "({})[{}][{}]".format(
                self.ROW_AT_INDEX.format("*"), " and ".join(row_parts), " and ".join(query_parts)
            )
        elif query_parts:
            query = "({})[{}]".format(self.ROW_AT_INDEX.format("*"), " and ".join(query_parts))
        elif row_parts:
            query = "({})[{}]".format(self.ROW_AT_INDEX.format("*"), " and ".join(row_parts))
        else:
            # When using ONLY regexps, we might see no query_parts, therefore default query
            query = self.ROW_AT_INDEX.format("*")

        return query

    def _filter_rows_by_query(self, query):
        # Preload the rows to prevent stale element exceptions
        rows = []
        for row_element in self.browser.elements(query, parent=self):
            row_pos = self._get_number_preceeding_rows(row_element)
            # get_number_preceeding_rows is javascript driven, and does not account for thead
            # When it counts rows, if the header is in the body of the table, then our index is
            # incorrect and has to be decreased
            # If the header is not in the body of the table, number of preceeding rows is 0-based
            # what is correct
            rows.append(
                self._create_row(
                    self,
                    row_pos - 1 if self._is_header_in_body else row_pos,
                    logger=create_item_logger(self.logger, row_pos),
                )
            )
        return rows

    def _apply_row_filter(self, rows, row_filters):
        if row_filters:
            remaining_rows = []
            for row in rows:
                for row_action, row_value in row_filters:
                    row_action = row_action.lower()
                    if row_action.startswith("attr"):
                        try:
                            attr_name, attr_value = row_value
                            got_value = self.browser.element(row).get_attribute(attr_name) or ""
                        except ValueError:
                            msg = (
                                "When passing _row__{}= into the row filter, "
                                "you must pass it a 2-tuple"
                            )
                            raise ValueError(msg.format(row_action))
                        if row_action == "attr_startswith":
                            if not got_value.startswith(attr_value):
                                break
                        elif row_action == "attr":
                            if got_value != attr_value:
                                break
                        elif row_action == "attr_endswith":
                            if not got_value.endswith(attr_value):
                                break
                        elif row_action == "attr_contains":
                            if attr_value not in got_value:
                                break
                        else:
                            raise ValueError(f"Unsupported action {row_action}")
                    else:
                        raise ValueError(f"Unsupported action {row_action}")
                else:
                    remaining_rows.append(row)
            return remaining_rows
        else:
            return rows

    def _apply_processed_filters(self, rows, processed_filters):
        if processed_filters:
            remaining_rows = []
            for row in rows:
                next_row = False
                for column_index, matchers in processed_filters.items():
                    column = row[column_index]
                    for method, value in matchers:
                        if method is None:
                            # equals
                            if column.text != value:
                                next_row = True
                                break
                        elif method == "contains":
                            # in
                            if value not in column.text:
                                next_row = True
                                break
                        elif method == "startswith":
                            # starts with
                            if not column.text.startswith(value):
                                next_row = True
                                break
                        elif method == "endswith":
                            # ends with
                            if not column.text.endswith(value):
                                next_row = True
                                break
                        else:
                            raise ValueError(f"Unknown method {method}")
                    if next_row:
                        break
                else:
                    remaining_rows.append(row)
            return remaining_rows
        else:
            return rows

    def _filtered_rows(self, *extra_filters, **filters):
        processed_filters, regexp_filters, row_filters = self._process_filters(
            *extra_filters, **filters
        )
        if not self.table_tree:
            query = self._build_query(processed_filters, row_filters)
            rows = self._filter_rows_by_query(query)
        else:
            rows = self._apply_row_filter(list(self._all_rows()), row_filters)
            rows = self._apply_processed_filters(rows, processed_filters)

        for row in rows:
            if regexp_filters:
                for regexp_column, regexp_filter in regexp_filters:
                    if regexp_filter.search(row[regexp_column].text) is None:
                        break
                else:
                    yield row
            else:
                yield row

    def row_by_cell_or_widget_value(self, column, value):
        """Row queries do not work with embedded widgets. Therefore you can use this method.

        Args:
            column: Position or name fo the column where you are looking the value for.
            value: The value looked for

        Returns:
            :py:class:`TableRow` instance

        Raises:
            :py:class:`RowNotFound`
        """
        try:
            return self.row((column, value))
        except RowNotFound:
            for row in self.rows():
                if row[column].widget is None:
                    continue
                # Column has a widget
                if not row[column].widget.is_displayed:
                    continue
                # Column widget is displayed...
                if row[column].widget.read() == value:
                    return row  # found matching widget value
                # But the value didn't match, keep looping
                else:
                    continue
            else:
                raise RowNotFound(f"Row not found by {column!r}/{value!r}")

    def read(self):
        """Reads the table. Returns a list, every item in the list is contents read from the row."""
        rows = list(self)
        # Cut the unwanted rows if necessary
        if self.rows_ignore_top is not None:
            rows = rows[self.rows_ignore_top :]
        if self.rows_ignore_bottom is not None and self.rows_ignore_bottom > 0:
            rows = rows[: -self.rows_ignore_bottom]
        if self.assoc_column_position is None:
            return [row.read() for row in rows]
        else:
            result = {}
            for row in rows:
                row_read = row.read()
                try:
                    key = row_read.pop(self.header_index_mapping[self.assoc_column_position])
                except KeyError:
                    try:
                        key = row_read.pop(self.assoc_column_position)
                    except KeyError:
                        try:
                            key = row_read.pop(self.assoc_column)
                        except KeyError:
                            raise ValueError(
                                "The assoc_column={!r} could not be retrieved".format(
                                    self.assoc_column
                                )
                            )
                if key in result:
                    raise ValueError(f"Duplicate value for {key}={result[key]!r}")
                result[key] = row_read
            return result

    def fill(self, value):
        """Fills the table, accepts list which is dispatched to respective rows."""
        if isinstance(value, dict):
            if self.assoc_column_position is None:
                raise TypeError("In order to support dict you need to specify assoc_column")
            changed = False
            for key, fill_value in value.items():
                try:
                    row = self.row_by_cell_or_widget_value(self.assoc_column_position, key)
                except RowNotFound:
                    row = self[self.row_add()]
                    fill_value = copy(fill_value)
                    fill_value[self.assoc_column_position] = key
                if row.fill(fill_value):
                    self.row_save(row=row.index)
                    changed = True
            return changed
        else:
            if not isinstance(value, (list, tuple)):
                value = [value]
            total_values = len(value)
            rows = list(self)
            # Adapt the behaviour similar to read
            if self.top_ignore_fill and self.rows_ignore_top is not None:
                rows = rows[self.rows_ignore_top :]
            if (
                self.bottom_ignore_fill
                and self.rows_ignore_bottom is not None
                and self.rows_ignore_bottom > 0
            ):
                rows = rows[: -self.rows_ignore_bottom]
            row_count = len(rows)
            present_row_values = value[:row_count]
            if total_values > row_count:
                extra_row_values = value[row_count:]
            else:
                extra_row_values = []
            changed = any(row.fill(value) for row, value in zip(rows, present_row_values))
            for extra_value in extra_row_values:
                if self[self.row_add()].fill(extra_value):
                    changed = True
            return changed

    @property
    def row_count(self):
        """Returns how many rows are currently in the table."""
        return len(self.browser.elements(self.ROWS, parent=self))

    def row_add(self):
        """To be implemented if the table has dynamic rows.

        This method is called when adding a new row is necessary.

        Default implementation shouts :py:class:`NotImplementedError`.

        Returns:
            An index (position) of the new row. ``None`` in case of error.
        """
        raise NotImplementedError(
            "You need to implement the row_add in order to use dynamic adding"
        )

    def row_save(self, row=None):
        """To be implemented if the table has dynamic rows.

        Used when the table needs confirming saving of each row.

        Default implementation just writes a debug message that it is not used.
        """
        self.logger.debug("Row saving not used.")

    @property
    def has_rowcolspan(self):
        """Checks whether table has rowspan/colspan attributes"""
        return bool(self.browser.elements("./tbody//td[@rowspan or @colspan]", parent=self))

    def _filter_child(self, child):
        return child.tag_name not in self.IGNORE_TAGS

    def _process_table(self):
        queue = deque()
        tree = Node(name=self.browser.tag(self), obj=self, position=0)
        queue.append(tree)

        while len(queue) > 0:
            node = queue.popleft()
            # visit node
            children = self.browser.elements("./*[descendant-or-self::node()]", parent=node.obj)

            for position, child in enumerate(filter(self._filter_child, children)):
                cur_tag = child.tag_name

                if cur_tag == self.ROW_TAG:
                    # todo: add logger
                    cur_obj = self._create_row(
                        parent=self._get_ancestor_node_obj(node), index=position
                    )
                    cur_node = Node(name=cur_tag, parent=node, obj=cur_obj, position=position)
                    queue.append(cur_node)

                elif cur_tag == self.COLUMN_TAG:
                    cur_position = self._get_position_respecting_spans(node)
                    cur_obj = self._create_column(
                        parent=self._get_ancestor_node_obj(node),
                        position=cur_position,
                        absolute_position=cur_position,
                    )
                    Node(name=cur_tag, parent=node, obj=cur_obj, position=cur_position)

                    rowsteps = range(1, int(child.get_attribute("rowspan") or 0))
                    colsteps = range(1, int(child.get_attribute("colspan") or 0))
                    coordinates = set(itertools.zip_longest(colsteps, rowsteps, fillvalue=0))

                    # when there are both rowspan and colspan set, we need to generate additional
                    # cell references
                    additional_coordinates = set()
                    for col, row in coordinates:
                        if col > 0 and row > 0:
                            for new_coord in itertools.product(range(col + 1), range(row + 1)):
                                if new_coord == (0, 0):
                                    continue
                                additional_coordinates.add(new_coord)

                    coordinates = coordinates | additional_coordinates

                    for col_step, row_step in coordinates:
                        if row_step >= 1:
                            ref_parent = self._get_sibling_node(node, steps=row_step)
                        else:
                            ref_parent = node
                        ref_obj = TableReference(parent=ref_parent, reference=cur_obj)
                        ref_position = cur_position if col_step == 0 else cur_position + col_step
                        Node(name=cur_tag, parent=ref_parent, obj=ref_obj, position=ref_position)

                else:
                    cur_node = Node(name=cur_tag, parent=node, obj=child, position=position)
                    queue.append(cur_node)
        return tree

    def _recalc_column_positions(self, tree):
        for row in self.resolver.glob(tree, self.ROW_RESOLVER_PATH):
            modifier = 0
            # Look for column nodes
            cols = self.resolver.glob(row, f"./{self.COLUMN_RESOLVER_PATH}")
            for col in sorted(cols, key=attrgetter("position")):
                if getattr(col.obj, "refers_to", None):
                    modifier -= 1
                    continue
                col.obj.position += modifier

    def print_tree(self):
        """Prints table as it is stored in tree. Relevant for rowspan/colspan only"""
        if self.table_tree:
            for pre, _, node in RenderTree(self.table_tree, style=AsciiStyle()):
                print(pre, node.name, node.position, node.obj)

    @staticmethod
    def _get_ancestor_node_obj(node):
        cur_node = node
        while True:
            if not cur_node.parent or isinstance(cur_node.obj, Widget):
                # root node orone of table nodes
                return cur_node.obj
            else:
                # some non widgetastic node
                cur_node = cur_node.parent
                continue

    @staticmethod
    def _get_sibling_node(node, steps=1):
        parent_pos = next(i for i, c in enumerate(node.parent.children) if node is c)
        next_node_pos = parent_pos + steps
        return node.parent.children[next_node_pos]

    @staticmethod
    def _get_position_respecting_spans(node):
        # looking for reference objects among columns
        spans = [c for c in node.children if getattr(c.obj, "refers_to", None)]
        # checking whether we have gaps in column positions
        gaps = {c for c in range(len(node.children))} - {c.position for c in node.children}
        return min(gaps) if spans and gaps else len(node.children)


class TableResolver(Resolver):
    """
    anytree's Resolver has very limited support of xpath.
    This class slightly improves that by adding ability to specify node index number.
    It will be removed when xpath support is enhanced in anytree
    """

    index_regexp = re.compile(r"(.*?)\[(\d+)\]$")

    def get(self, node, path):
        node, parts = self._Resolver__start(node, path)
        for part in parts:
            if part == "..":
                node = node.parent
            elif part in ("", "."):
                pass
            elif self.index_regexp.match(part):
                node = self._get_node_by_index(node, part)
            else:
                node = self._Resolver__get(node, part)
        return node

    def glob(self, node, path, handle_resolver_error=False):
        node, parts = self._Resolver__start(node, path)
        try:
            return self.__glob(node, parts)
        except ResolverError:
            if handle_resolver_error:
                return []
            else:
                raise

    def __glob(self, node, parts):
        nodes = []
        if not parts:
            return [node]
        name = parts[0]
        remainder = parts[1:]
        # handle relative
        if name == "..":
            nodes += self.__glob(node.parent, remainder)
        elif name in ("", "."):
            nodes += self.__glob(node, remainder)
        elif self.index_regexp.match(name):
            nodes += self.__glob(self._get_node_by_index(node, name), remainder)
        else:
            matches = self.__find(node, name, remainder)
            if not matches and not self.is_wildcard(name):
                raise ChildResolverError(node, name, self.pathattr)
            nodes += matches
        return nodes

    def _get_node_by_index(self, node, part):
        part, position = self.index_regexp.match(part).groups()

        matching_nodes = self._Resolver__find(node, part, None)
        for node_at_pos in filter(lambda n: n.position == int(position), matching_nodes):
            return node_at_pos
        else:
            names = [
                f"{repr(getattr(c, self.pathattr, None))}[{c.position}]" for c in node.children
            ]
            raise ResolverError(
                node,
                part,
                "{} has no child '{}' with position={}. Children are: {}".format(
                    repr(node), part, position, ", ".join(names)
                ),
            )

    def __find(self, node, pat, remainder):
        matches = []
        for child in node.children:
            name = getattr(child, self.pathattr, None)
            try:
                if self._Resolver__match(name, pat):
                    if remainder:
                        matches += self.__glob(child, remainder)
                    else:
                        matches.append(child)
            except ResolverError as exc:
                if not self.is_wildcard(pat):
                    raise exc
        return matches
