# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from selenium.common.exceptions import (  # NOQA
    NoSuchElementException, MoveTargetOutOfBoundsException, StaleElementReferenceException,  # NOQA
    NoAlertPresentException, UnexpectedAlertPresentException, WebDriverException)  # NOQA


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


class DynamicTableAddError(Exception):
    """Raised when an attempt to add or save a row to a `widgetastic_manageiq.DynamicTable` fails"""
    pass
