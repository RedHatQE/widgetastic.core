import pytest

from widgetastic.utils import Version


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("0.0.1", "1.0.0"),
        ("1", "2"),
        ("1.0-beta", "1.0"),
        ("1.0-beta", "1.0-rc"),
    ],
)
def test_compare_lt(a, b):
    assert Version(a) < b
    assert not Version(a) > b


@pytest.mark.parametrize("a", ["0.0.1", "1.2.3-beta", "3.4.5-rc-beta"])
def test_compare_eq(a):
    assert Version(a) == a


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("1.0.0", "0.0.1"),
        ("2", "1"),
        ("1.0", "1.0-beta"),
        ("1.0-rc", "1.0-beta"),
    ],
)
def test_compare_gt(a, b):
    assert Version(a) > b
    assert not Version(a) < b


def test_version_edge_cases():
    """Test Version class edge cases and error conditions."""

    with pytest.raises(ValueError, match="Version string cannot be None"):
        Version(None)

    # Test list/tuple parsing
    assert Version([1, 2, 3]).vstring == "1.2.3"
    assert Version((2, 0)).vstring == "2.0"

    # Test hash method
    v1 = Version("1.0")
    v2 = Version("1.0")
    assert hash(v1) == hash(v2)

    # Test comparison with invalid type
    v3 = Version("1.0")
    with pytest.raises((ValueError, TypeError)):
        v3 < "invalid_version_format_that_creates_string_components"

    # Test __ge__ method directly
    assert Version("2.0") >= Version("1.0")
    assert Version("1.0") >= Version("1.0")

    # Test with object that fails Version() constructor
    v = Version("1.0")

    # Create an object that will fail the Version() constructor
    class BadObject:
        def __str__(self):
            raise TypeError("Cannot convert to string")

    with pytest.raises(ValueError, match="Cannot compare Version to"):
        v < BadObject()  # This will fail in Version() constructor


def test_version_suffix_handling():
    """Test Version suffix parsing and normalization."""

    # Test suffix handling with version suffixes
    v_alpha = Version("1.0.0-alpha1")
    assert v_alpha.suffix == ["alpha1"]

    # Test normalized_suffix property
    normalized = v_alpha.normalized_suffix
    assert len(normalized) == 1
    assert (
        normalized[0][0] == 2
    )  # alpha is index 2 in SUFFIXES ("nightly", "pre", "alpha", "beta", "rc")
    assert normalized[0][1] == 1.0  # numeric part is 1


def test_version_series_and_contains():
    """Test Version series methods and __contains__."""

    # Test __contains__ with invalid version
    v1 = Version("5.5")
    assert object() not in v1

    # Test is_in_series method
    v_series = Version("5.5.1.2")
    series_check = Version("5.5")
    assert v_series.is_in_series(series_check)

    # Test with lowest/latest versions
    v_lowest = Version.lowest()
    v_latest = Version.latest()
    assert not v_lowest.is_in_series(series_check)
    assert not v_latest.is_in_series(series_check)

    # Test series method
    v_long = Version("1.2.3.4.5")
    assert v_long.series(1) == "1"
    assert v_long.series(4) == "1.2.3.4"

    # Test is_in_series with string parameter
    v = Version("1.2.3")
    assert v.is_in_series("1.2")

    # est lowest/latest equals series case
    latest = Version.latest()
    assert latest.is_in_series(latest)


def test_version_comparison_operators():
    """Test additional comparison operators."""

    v1 = Version("1.0.0")
    v2 = Version("2.0.0")

    # Test __ne__
    assert v1 != v2
    assert not (v1 == v2)

    # Test __gt__
    assert v2 > v1
    assert not (v1 > v2)


def test_version_latest_lowest_caching():
    """Test latest/lowest version caching"""

    # Test caching behavior
    latest1 = Version.latest()
    latest2 = Version.latest()
    assert latest1 is latest2

    lowest1 = Version.lowest()
    lowest2 = Version.lowest()
    assert lowest1 is lowest2
