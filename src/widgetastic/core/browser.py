# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.file_detector import LocalFileDetector, UselessFileDetector
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from smartloc import Locator
from textwrap import dedent
from wait_for import wait_for

from .exceptions import (
    NoSuchElementException, UnexpectedAlertPresentException, MoveTargetOutOfBoundsException,
    StaleElementReferenceException, NoAlertPresentException)


# TODO: Resolve this issue in smartloc
# Monkey patch By
def is_valid(cls, strategy):
    return strategy in {'xpath', 'css'}

By.is_valid = classmethod(is_valid)


class DefaultPlugin(object):
    ENSURE_PAGE_SAFE = '''\
        return {
            jquery: (typeof jQuery === "undefined") ? true : jQuery.active < 1,
            prototype: (typeof Ajax === "undefined") ? true : Ajax.activeRequestCount < 1,
            document: document.readyState == "complete"
        }
        '''

    def __init__(self, browser):
        self.browser = browser

    def ensure_page_safe(self, timeout='10s'):
        # THIS ONE SHOULD ALWAYS USE JAVASCRIPT ONLY, NO OTHER SELENIUM INTERACTION
        self.browser.dismiss_any_alerts()

        def _check():
            result = self.browser.execute_script(self.ENSURE_PAGE_SAFE)
            # TODO: Logging
            try:
                return all(result.values())
            except AttributeError:
                return True

        wait_for(_check, timeout=timeout, delay=0.2)


class Browser(object):
    """Wrapper of the selenium "browser"

    This class contains methods that wrap the default selenium functionality in a convenient way,
    mitigating known issues and generally improving the developer experience.

    Subclass it if you want to present more informations (like product version) to the widgets.
    """
    def __init__(self, selenium, plugin_class=None):
        self.selenium = selenium
        plugin_class = plugin_class or DefaultPlugin
        self.plugin = plugin_class(self)

    @property
    def browser(self):
        return self

    @property
    def product_version(self):
        raise NotImplementedError('You have to implement product_version')

    @staticmethod
    def _process_locator(locator):
        if isinstance(locator, WebElement):
            return locator
        try:
            return Locator(locator)
        except TypeError:
            if hasattr(locator, '__element__'):
                return locator.__element__()
            else:
                raise

    def elements(self, locator, parent=None, check_visibility=False):
        self.plugin.ensure_page_safe()
        locator = self._process_locator(locator)
        # Get result
        if isinstance(locator, WebElement):
            result = [locator]
        else:
            # Get the direct parent object
            if parent:
                root_element = self.elements(parent)
            else:
                root_element = self.selenium
            result = root_element.find_elements(*locator)

        if check_visibility:
            result = filter(self.is_displayed, result)

        return result

    def element(self, locator, *args, **kwargs):
        try:
            elements = self.elements(locator, *args, **kwargs)
            if len(elements) > 1:
                visible_elements = filter(self.is_displayed, elements)
                if visible_elements:
                    return visible_elements[0]
                else:
                    return elements[0]
            else:
                return elements[0]
        except IndexError:
            raise NoSuchElementException('Could not find an element {}'.format(repr(locator)))

    def perform_click(self):
        """Clicks the left mouse button at the current mouse position."""
        ActionChains(self.selenium).click().perform()

    def click(self, *args, **kwargs):
        self.move_to_element(*args, **kwargs)
        # and then click on current mouse position
        self.perform_click()
        try:
            self.plugin.ensure_page_safe()
        except UnexpectedAlertPresentException:
            pass

    def is_displayed(self, locator, *args, **kwargs):
        kwargs['check_visibility'] = False
        retry = True
        tries = 10
        while retry:
            retry = False
            try:
                return self.move_to_element(locator, *args, **kwargs).is_displayed()
            except (NoSuchElementException, MoveTargetOutOfBoundsException):
                return False
            except StaleElementReferenceException:
                if isinstance(locator, WebElement) or tries <= 0:
                    # We cannot fix this one.
                    raise
                retry = True
                tries -= 1
                time.sleep(0.1)

        # Just in case
        return False

    def move_to_element(self, locator, *args, **kwargs):
        el = self.element(locator, *args, **kwargs)
        if el.tag_name == "option":
            # Instead of option, let's move on its parent <select> if possible
            parent = self.element("..", parents=[el])
            if parent.tag_name == "select":
                self.move_to_element(parent)
                return el
        move_to = ActionChains(self.selenium).move_to_element(el)
        try:
            move_to.perform()
        except MoveTargetOutOfBoundsException:
            # ff workaround
            self.execute_script("arguments[0].scrollIntoView();", el)
            try:
                move_to.perform()
            except MoveTargetOutOfBoundsException:  # This has become desperate now.
                raise MoveTargetOutOfBoundsException(
                    "Despite all the workarounds, scrolling to `{}` was unsuccessful.".format(
                        locator))
        return el

    def execute_script(self, script, *args, **kwargs):
        return self.selenium.execute_script(dedent(script), *args, **kwargs)

    def classes(self, *args, **kwargs):
        """Return a list of classes attached to the element."""
        return set(self.execute_script(
            "return arguments[0].classList;", self.element(*args, **kwargs)))

    def tag(self, *args, **kwargs):
        return self.element(*args, **kwargs).tag_name

    def text(self, *args, **kwargs):
        return self.element(*args, **kwargs).text

    def get_attribute(self, attr, *args, **kwargs):
        return self.element(*args, **kwargs).get_attribute(attr)

    def set_attribute(self, attr, value, *args, **kwargs):
        return self.execute_script(
            "arguments[0].setAttribute(arguments[1], arguments[2]);",
            self.element(*args, **kwargs), attr, value)

    def clear(self, *args, **kwargs):
        return self.element(*args, **kwargs).clear()

    def send_keys(self, text, *args, **kwargs):
        text = text or ''
        file_intercept = False
        # If the element is input type file, we will need to use the file detector
        if self.tag(*args, **kwargs) == 'input':
            type_attr = self.get_attribute('type', *args, **kwargs)
            if type_attr and type_attr.strip() == 'file':
                file_intercept = True
        try:
            if file_intercept:
                # If we detected a file upload field, let's use the file detector.
                self.selenium.file_detector = LocalFileDetector()
            self.move_to_element(*args, **kwargs).send_keys(text)
        finally:
            # Always the UselessFileDetector for all other kinds of fields, so do not leave
            # the LocalFileDetector there.
            if file_intercept:
                self.selenium.file_detector = UselessFileDetector()

    def get_alert(self):
        return self.selenium.switch_to_alert()

    def is_alert_present(self):
        try:
            self.get_alert().text
        except NoAlertPresentException:
            return False
        else:
            return True

    def dismiss_any_alerts(self):
        """Loops until there are no further alerts present to dismiss.

        Useful for handling the cases where the alert pops up multiple times.
        """
        try:
            while self.is_alert_present():
                alert = self.get_alert()
                alert.dismiss()
        except NoAlertPresentException:  # Just in case. is_alert_present should be reliable
            pass

    def handle_alert(self, cancel=False, wait=30.0, squash=False, prompt=None, check_present=False):
        """Handles an alert popup.

        Args:
            cancel: Whether or not to cancel the alert.
                Accepts the Alert (False) by default.
            wait: Time to wait for an alert to appear.
                Default 30 seconds, can be set to 0 to disable waiting.
            squash: Whether or not to squash errors during alert handling.
                Default False
            prompt: If the alert is a prompt, specify the keys to type in here
            check_present: Does not squash
                :py:class:`selenium.common.exceptions.NoAlertPresentException`

        Returns:
            True if the alert was handled, False if exceptions were
            squashed, None if there was no alert.

        No exceptions will be raised if ``squash`` is True and ``check_present`` is False.

        Raises:
            utils.wait.TimedOutError: If the alert popup does not appear
            selenium.common.exceptions.NoAlertPresentException: If no alert is present when
                accepting or dismissing the alert.

        """
        # throws timeout exception if not found
        try:
            if wait:
                WebDriverWait(self.selenium, wait).until(expected_conditions.alert_is_present())
            popup = self.get_alert()
            if prompt is not None:
                popup.send_keys(prompt)
            popup.dismiss() if cancel else popup.accept()
            # Should any problematic "double" alerts appear here, we don't care, just blow'em away.
            self.dismiss_any_alerts()
            return True
        except NoAlertPresentException:
            if check_present:
                raise
            else:
                return None
        except Exception:
            if squash:
                return False
            else:
                raise
