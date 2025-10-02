"""
Widgetastic Core Exceptions
===========================
"""


class WidgetasticException(Exception):
    """A base exception for the widgetastic framework."""

    pass


class LocatorNotImplemented(NotImplementedError, WidgetasticException):
    """Raised when a widget does not have a locator defined."""

    pass


class WidgetOperationFailed(WidgetasticException):
    """Raised when an action on a widget does not result in the expected outcome."""

    pass


class DoNotReadThisWidget(WidgetasticException):
    """
    An exception that can be raised from a widget's read() method to signal
    that it should not be included in the results of a view.read().
    """

    pass


class RowNotFound(IndexError, WidgetasticException):
    """Raised when a table row cannot be found."""

    pass


class NoSuchElementException(WidgetasticException):
    """Raised when an element cannot be found."""

    pass


class NoAlertPresentException(WidgetasticException):
    """Raised when an action is attempted on an alert that is not present."""

    pass


class FrameNotFoundError(WidgetasticException):
    """Raised when trying to access elements in a nonexistent iframe or frame context."""

    pass


__all__ = [
    "WidgetasticException",
    "LocatorNotImplemented",
    "WidgetOperationFailed",
    "DoNotReadThisWidget",
    "RowNotFound",
    "NoSuchElementException",
    "NoAlertPresentException",
    "FrameNotFoundError",
]
