from selenium.common.exceptions import (
    ElementNotInteractableException,
    MoveTargetOutOfBoundsException,
    NoAlertPresentException,
    NoSuchElementException,
    StaleElementReferenceException,
    UnexpectedAlertPresentException,
    WebDriverException,
)


class WidgetasticException(Exception):
    pass


class LocatorNotImplemented(NotImplementedError, WidgetasticException):
    pass


class WidgetOperationFailed(WidgetasticException):
    pass


class DoNotReadThisWidget(WidgetasticException):
    pass


class RowNotFound(IndexError, WidgetasticException):
    pass


__all__ = [
    "DoNotReadThisWidget",
    "ElementNotInteractableException",
    "MoveTargetOutOfBoundsException",
    "NoAlertPresentException",
    "NoSuchElementException",
    "RowNotFound",
    "StaleElementReferenceException",
    "UnexpectedAlertPresentException",
    "WebDriverException",
    "WidgetOperationFailed",
    "WidgetasticException",
]
