import pytest

from widgetastic.xpath import normalize_space
from widgetastic.xpath import quote


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("<>", '"<>"'),
        ("&", '"&"'),
        ("\"'", '"&quot;\'"'),
    ],
)
def test_xpath_quote(a, b):
    assert quote(a) == b


def test_normalize_space():
    assert normalize_space("  a   as  asd  asdd\tdasd\t\t\tasd   ") == "a as asd asdd dasd asd"
