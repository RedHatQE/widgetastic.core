# -*- coding: utf-8 -*-
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import WebDriverException


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
