from selenium.common.exceptions import ElementNotInteractableException
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import InvalidElementStateException


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
    "ElementNotInteractableException",
    "InvalidElementStateException",
    "MoveTargetOutOfBoundsException",
    "NoAlertPresentException",
    "NoSuchElementException",
    "StaleElementReferenceException",
    "UnexpectedAlertPresentException",
    "WebDriverException",
    "WidgetasticException",
    "WidgetOperationFailed",
    "DoNotReadThisWidget",
    "RowNotFound",
]
