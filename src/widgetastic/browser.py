# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import six
import time

from cached_property import cached_property
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
    StaleElementReferenceException, NoAlertPresentException, LocatorNotImplemented)
from .log import create_widget_logger, null_logger
from .xpath import normalize_space


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

    @cached_property
    def logger(self):
        """Logger with prepended plugin name."""
        return create_widget_logger(type(self).__name__, self.browser.logger)

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

    def after_click(self, element):
        """Invoked after clicking on an element."""
        pass

    def before_click(self, element):
        """Invoked before clicking on an element."""
        pass

    def after_keyboard_input(self, element, keyboard_input):
        """Invoked after sending keys into an element.

        Args:
            keyboard_input: String if any text typed in, None if the element is cleared.
        """
        pass

    def before_keyboard_input(self, element, keyboard_input):
        """Invoked after sending keys into an element.

        Args:
            keyboard_input: String if any text typed in, None if the element is cleared.
        """
        pass


class Browser(object):
    """Wrapper of the selenium "browser"

    This class contains methods that wrap the Standard Selenium functionality in a convenient way,
    mitigating known issues and generally improving the developer experience.

    If you want to present more informations (like :py:meth:`product_version` for
    :py:class:`widgetastic.utils.VersionPick`) to the widgets, subclass this class.

    Many of these "hacks" were developed in period between 2013-2016 in ManageIQ QE functional test
    suite and are used to date. Those that were generic enough were pulled in here.

    This wrapper is opinionated in some aspects, tries to get out of your way. For example, if you
    use :py:meth:`element`, and there are two elements of which first is invisible and the second
    is visible, normal selenium would just return the first one, but this wrapper assumes you want
    the visible one in case there is more than one element that resolves from given locator.

    Standard Selenium cannot read text that is located under some other element or invisible in some
    cases. This wrapper assumes that if you cannot scroll the element or you get no text, it shall
    try getting it via JavaScript, which works always.

    This wrapper also ensures the text that is returned is normalized. When working with this
    wrapper and using XPath to match text, never use ``.="foo"`` or ``text()="foo"`` but rather use
    something like this: ``normalize-space(.)="foo"``.

    Standard Selenium has a special method that clicks on an element. It might not work in some
    cases - eg. when some composed "widgets" make the element that is resolved by the locator
    somehow hidden behind another. We had these issues so we just replaced the click with a two
    stage "move & click the mouse", the :py:meth:`click`.

    Moving to an element involves a workaround that tries to mitigate possible browser misbehaviour
    when scrolling in. Sometimes some browsers complain that it is not possible to scroll to the
    element but when you engage JavaScript, it works just fine, so this is what this wrapper does
    too. Also when you accidentally try moving to ``<option>`` tag, it would throw an exception
    but this wrapper assumes you want the parent ``<select>`` instead.

    :py:meth:`send_keys` automatically detects whether the form item is a file upload and chooses
    the proper file detector accordingly. That is because the default setting of Selenium uses a
    file detector, which then can produce some unexpected results. Eg. if your user is called
    ``admin`` you also have a file called ``admin`` somewhere around and you are testing in a remote
    browser. That makes selenium upload the file on the remote machine and change the string
    to reflect the new file name. Then you end up with the login not being ``admin``, but rather
    something like ``/tmp/someawfulhashadmin`` for obvious reasons that however might not be obvious
    to the ordinary users of Selenium.

    Args:
        selenium: Any :py:class:`selenium.webdriver.remote.webdriver.WebDriver` descendant
        plugin_class: If you want to alter the behaviour of some aspects, you can specify your own
            class as plugin.
        logger: a logger, if not specified, default is used.
        extra_objects: If the testing system needs to know more about the environment, you can pass
            a dictionary in this parameter, where you can store all these additional objects.
    """
    def __init__(self, selenium, plugin_class=None, logger=None, extra_objects=None):
        self.selenium = selenium
        plugin_class = plugin_class or DefaultPlugin
        self.plugin = plugin_class(self)
        self.logger = logger or null_logger
        self.extra_objects = extra_objects or {}

    @property
    def handles_alerts(self):
        """Important for unit testing as PhantomJS does not handle alerts. This makes the alert
        handling functions do nothing."""
        return self.selenium.capabilities.get('handlesAlerts', True)

    @property
    def browser(self):
        """Implemented so :py:class:`widgetastic.widget.View` does not have to check the
        instance of its parent. This property exists there so here it just stops the chain"""
        return self

    @property
    def product_version(self):
        """In order for :py:class:`widgetastic.utils.VersionPick` to work on
        :py:class:`widgetastic.widget.Widget` instances, you need to override this property
        that will enable this functionality.
        """
        raise NotImplementedError('You have to implement product_version')

    @staticmethod
    def _process_locator(locator):
        """Processes the locator so the :py:meth:`elements` gets exactly what it needs."""
        if isinstance(locator, WebElement):
            return locator
        try:
            return Locator(locator)
        except TypeError:
            if hasattr(locator, '__locator__'):
                # Deal with the case when __locator__ returns a webelement.
                loc = locator.__locator__()
                if isinstance(loc, WebElement):
                    return loc
            raise LocatorNotImplemented(
                'You have to implement __locator__ on {!r}'.format(type(locator)))

    @staticmethod
    def _locator_force_visibility_check(locator):
        if hasattr(locator, '__locator__') and hasattr(locator, 'CHECK_VISIBILITY'):
            return locator.CHECK_VISIBILITY
        else:
            return None

    def elements(self, locator, parent=None, check_visibility=False):
        """Method that resolves locators into selenium webelements.

        Args:
            locator: A valid locator. Valid locators are:

                * strings (which are considered as XPath unless they fit the
                    simple ``tag#id.class``, in which case the string is considered as a CSS
                    selector)
                * dictionaries - like ``{'xpath': '//something'}``
                * :py:class:`selenium.webdriver.remote.webelement.WebElement` instances
                * Any other object that implements ``__locator__``
            parent: A parent element identificator. Can be any valid locator.
            check_visibility: If set to ``True`` it will filter out elements that are not visible.

        Returns:
            A :py:class:`list` of :py:class:`selenium.webdriver.remote.webelement.WebElement`
        """
        self.plugin.ensure_page_safe()
        locator = self._process_locator(locator)
        # Get result
        if isinstance(locator, WebElement):
            result = [locator]
        else:
            # Get the direct parent object
            if parent:
                root_element = self.element(parent, check_visibility=check_visibility)
            else:
                root_element = self.selenium
            result = root_element.find_elements(*locator)

        if check_visibility:
            result = [e for e in result if self.is_displayed(e)]

        return result

    def element(self, locator, *args, **kwargs):
        """Returns one :py:class:`selenium.webdriver.remote.webelement.WebElement`

        See: :py:meth:`elements`

        Returns:
            :py:class:`selenium.webdriver.remote.webelement.WebElement`

        Raises:
            :py:class:`selenium.common.exceptions.NoSuchElementException`
        """
        try:
            vcheck = self._locator_force_visibility_check(locator)
            if vcheck is not None:
                kwargs['check_visibility'] = vcheck
            elements = self.elements(locator, *args, **kwargs)
            if len(elements) > 1:
                visible_elements = [e for e in elements if self.is_displayed(e)]
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
        """Clicks at a specific element using two separate events (mouse move, mouse click).

        Args: See :py:meth:`elements`
        """
        ignore_ajax = kwargs.pop('ignore_ajax', False)
        el = self.move_to_element(*args, **kwargs)
        self.plugin.before_click(el)
        # and then click on current mouse position
        self.perform_click()
        if not ignore_ajax:
            try:
                self.plugin.ensure_page_safe()
            except UnexpectedAlertPresentException:
                pass
        self.plugin.after_click(el)

    def raw_click(self, *args, **kwargs):
        """Clicks at a specific element using the direct event.

        Args: See :py:meth:`elements`
        """
        ignore_ajax = kwargs.pop('ignore_ajax', False)
        el = self.element(*args, **kwargs)
        self.plugin.before_click(el)
        el.click()
        if not ignore_ajax:
            try:
                self.plugin.ensure_page_safe()
            except UnexpectedAlertPresentException:
                pass
        self.plugin.after_click(el)

    def is_displayed(self, locator, *args, **kwargs):
        """Check if the element represented by the locator is displayed.

        Args: See :py:meth:`elements`

        Returns:
            A :py:class:`bool`
        """
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
        """Moves the mouse cursor to the middle of the element represented by the locator.

        Can handle moving to the ``<option>`` tags or Firefox being pissy and thus making it utilize
        a JS workaround, ...

        Args: See :py:meth:`elements`

        Returns:
            :py:class:`selenium.webdriver.remote.webelement.WebElement`
        """
        el = self.element(locator, *args, **kwargs)
        if el.tag_name == "option":
            # Instead of option, let's move on its parent <select> if possible
            parent = self.element("..", parent=el)
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

    def move_by_offset(self, x, y):
        ActionChains(self.selenium).move_by_offset(x, y)

    def execute_script(self, script, *args, **kwargs):
        """Executes a script."""
        return self.selenium.execute_script(dedent(script), *args, **kwargs)

    def classes(self, *args, **kwargs):
        """Return a list of classes attached to the element.

        Args: See :py:meth:`elements`

        Returns:
            A :py:class:`set` of strings with classes.
        """
        return set(self.execute_script(
            "return arguments[0].classList;", self.element(*args, **kwargs)))

    def tag(self, *args, **kwargs):
        """Returns the tag name of the element represented by the locator passed.

        Args: See :py:meth:`elements`

        Returns:
            :py:class:`str` with the tag name
        """
        return self.element(*args, **kwargs).tag_name

    def text(self, *args, **kwargs):
        """Returns the text inside the element represented by the locator passed.

        The returned text is normalized with :py:func:`widgetastic.xpath.normalize_space` as defined
        by XPath standard.

        Args: See :py:meth:`elements`

        Returns:
            :py:class:`str` with the text
        """
        try:
            text = self.element(*args, **kwargs).text
        except MoveTargetOutOfBoundsException:
            text = ''

        if not text:
            # It is probably invisible
            text = self.execute_script(
                'return arguments[0].textContent || arguments[0].innerText;',
                self.element(*args, **kwargs))
            if text is None:
                text = ''

        return normalize_space(text)

    def get_attribute(self, attr, *args, **kwargs):
        return self.element(*args, **kwargs).get_attribute(attr)

    def set_attribute(self, attr, value, *args, **kwargs):
        return self.execute_script(
            "arguments[0].setAttribute(arguments[1], arguments[2]);",
            self.element(*args, **kwargs), attr, value)

    def clear(self, *args, **kwargs):
        el = self.element(*args, **kwargs)
        self.plugin.before_keyboard_input(el, None)
        result = el.clear()
        self.plugin.after_keyboard_input(el, None)
        return result

    def is_selected(self, *args, **kwargs):
        return self.element(*args, **kwargs).is_selected()

    def send_keys(self, text, *args, **kwargs):
        """Sends keys to the element. Detects the file inputs automatically.

        Args:
            text: Text to be inserted to the element.
            *args: See :py:meth:`elements`
            **kwargs: See :py:meth:`elements`
        """
        text = six.text_type(text) or ''
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
            el = self.move_to_element(*args, **kwargs)
            self.plugin.before_keyboard_input(el, text)
            result = el.send_keys(text)
            self.plugin.after_keyboard_input(el, text)
            return result
        finally:
            # Always the UselessFileDetector for all other kinds of fields, so do not leave
            # the LocalFileDetector there.
            if file_intercept:
                self.selenium.file_detector = UselessFileDetector()

    def get_alert(self):
        """Returns the current alert object.

        Raises:
            :py:class:`selenium.common.exceptions.NoAlertPresentException`
        """
        if not self.handles_alerts:
            return None
        return self.selenium.switch_to_alert()

    @property
    def alert_present(self):
        """Checks whether there is any alert present.

        Returns:
            :py:class:`bool`."""
        if not self.handles_alerts:
            return False
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
            while self.alert_present:
                alert = self.get_alert()
                alert.dismiss()
        except NoAlertPresentException:  # Just in case. alert_present should be reliable
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
            ``True`` if the alert was handled, ``False`` if exceptions were
            squashed, ``None`` if there was no alert.

        No exceptions will be raised if ``squash`` is True and ``check_present`` is False.

        Raises:
            :py:class:`wait_for.TimedOutError`: If the alert popup does not appear
            :py:class:`selenium.common.exceptions.NoAlertPresentException`: If no alert is present
                when accepting or dismissing the alert.
        """
        if not self.handles_alerts:
            return None
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
