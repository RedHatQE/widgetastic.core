# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from selenium.common.exceptions import (  # NOQA
    NoSuchElementException, MoveTargetOutOfBoundsException, StaleElementReferenceException,  # NOQA
    NoAlertPresentException, UnexpectedAlertPresentException)  # NOQA


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


class WidgetNotFound(WidgetasticException):
    """Raised when a widget was not found"""
    def __init__(self, widget, original_exception, widget_path):
        self.widget = widget
        self.original_exception = original_exception
        self.widget_path = widget_path

    def get_message(self):
        return 'Widget {} not found'.format('/'.join(self.widget_path))

    def __str__(self):
        return self.get_message()
