"""
Widgetastic Core Exceptions
===========================
"""


class WidgetasticException(Exception):
    """A base exception for the widgetastic framework."""


class LocatorNotImplemented(NotImplementedError, WidgetasticException):
    """Raised when a widget does not have a locator defined."""


class WidgetOperationFailed(WidgetasticException):
    """Raised when an action on a widget does not result in the expected outcome."""


class DoNotReadThisWidget(WidgetasticException):
    """
    An exception that can be raised from a widget's read() method to signal
    that it should not be included in the results of a view.read().
    """


class RowNotFound(IndexError, WidgetasticException):
    """Raised when a table row cannot be found."""


class NoSuchElementException(WidgetasticException):
    """Raised when an element cannot be found."""


class NoAlertPresentException(WidgetasticException):
    """Raised when an action is attempted on an alert that is not present."""


class FrameNotFoundError(WidgetasticException):
    """Raised when trying to access elements in a nonexistent iframe or frame context."""


__all__ = [
    "DoNotReadThisWidget",
    "FrameNotFoundError",
    "LocatorNotImplemented",
    "NoAlertPresentException",
    "NoSuchElementException",
    "RowNotFound",
    "WidgetOperationFailed",
    "WidgetasticException",
]
