import inspect
from logging import Logger
from textwrap import dedent
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Set
from typing import Type
from typing import TYPE_CHECKING
from typing import Union

from cached_property import cached_property
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.file_detector import LocalFileDetector
from selenium.webdriver.remote.file_detector import UselessFileDetector
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from smartloc import Locator
from wait_for import TimedOutError
from wait_for import wait_for
from playwright.sync_api import Locator as PlayLocator, Page, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import ElementHandle

from .exceptions import ElementNotInteractableException
from .exceptions import LocatorNotImplemented
from .exceptions import MoveTargetOutOfBoundsException
from .exceptions import NoAlertPresentException
from .exceptions import NoSuchElementException
from .exceptions import StaleElementReferenceException
from .exceptions import UnexpectedAlertPresentException
from .exceptions import WebDriverException
from .log import create_widget_logger
from .log import null_logger
from .types import ElementParent
from .types import LocatorAlias
from .types import LocatorProtocol
from .utils import crop_string_middle
from .utils import retry_stale_element
from .xpath import normalize_space

EXTRACT_CLASSES_OF_ELEMENT = """
return (
    function(arguments){
        var cl = arguments[0].classList;
        if(typeof cl.value === "undefined") {
            return cl;
        } else {
            var arr=[];
            for (i=0; i < cl.length; i++){
                arr.push(cl[i]);
            };
            return arr;
        }
})(arguments);
"""

EXTRACT_ATTRIBUTES_OF_ELEMENT = """
var items = {};
for (index = 0; index < arguments[0].attributes.length; ++index) {
    items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value
    };
return items;
"""


if TYPE_CHECKING:
    from .widget.base import Widget


class Size(NamedTuple):
    width: int
    height: int


class Location(NamedTuple):
    x: int
    y: int


class DefaultPlugin:
    ENSURE_PAGE_SAFE = """\
        return {
            jquery: (typeof jQuery === "undefined") ? true : jQuery.active < 1,
            prototype: (typeof Ajax === "undefined") ? true : Ajax.activeRequestCount < 1,
            document: document.readyState == "complete"
        }
        """

    def __init__(self, browser: "Browser") -> None:
        self.browser = browser

    @cached_property
    def logger(self):
        """Logger with prepended plugin name."""
        return create_widget_logger(type(self).__name__, self.browser.logger)

    def ensure_page_safe(self, timeout: str = "10s") -> None:
        # THIS ONE SHOULD ALWAYS USE JAVASCRIPT ONLY, NO OTHER SELENIUM INTERACTION

        def _check():
            result = self.browser.execute_script(self.ENSURE_PAGE_SAFE, silent=True)
            # TODO: Logging
            try:
                return all(result.values())
            except AttributeError:
                return True

        wait_for(_check, timeout=timeout, delay=0.2, very_quiet=True)

    def after_click(self, element: WebElement, locator: LocatorAlias) -> None:
        """Invoked after clicking on an element."""
        pass

    def after_click_safe_timeout(self, element: WebElement, locator: LocatorAlias) -> None:
        """Invoked after clicking on an element and :py:meth:`ensure_page_safe` failing to wait."""
        pass

    def before_click(self, element: WebElement, locator: LocatorAlias) -> None:
        """Invoked before clicking on an element."""
        pass

    def after_keyboard_input(self, element: WebElement, keyboard_input: Optional[str]) -> None:
        """Invoked after sending keys into an element.

        Args:
            keyboard_input: String if any text typed in, None if the element is cleared.
        """
        pass

    def before_keyboard_input(self, element: WebElement, keyboard_input: Optional[str]) -> None:
        """Invoked after sending keys into an element.

        Args:
            keyboard_input: String if any text typed in, None if the element is cleared.
        """
        pass

    def highlight_element(
        self,
        element: WebElement,
        style: str = "border: 2px solid red;",
        visible_for: float = 0.3,
    ) -> None:
        """
        Highlight the passed element by directly changing it's style to the 'style' argument.

        The new style will be visible for 'visible_for' [s] before reverting to the original style.

        Generally, visible_for should not be > 0.5 s. If the timeout is too high and we check
        an element multiple times in quick succession, the modified style will "stick".
        """
        self.browser.selenium.execute_script(
            """
            element = arguments[0];
            original_style = element.getAttribute('style');
            element.setAttribute('style', arguments[1]);
            setTimeout(function(){
                element.setAttribute('style', original_style);
            }, arguments[2]);
        """,
            element,
            style,
            int(visible_for * 1000),
        )  # convert visible_for to milliseconds


class Browser:
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

    def __init__(
        self,
        selenium: WebDriver = None,
        page: Page = None,
        plugin_class: Optional[Type[DefaultPlugin]] = None,
        logger: Optional[Logger] = None,
        extra_objects: Optional[Dict[Any, Any]] = None,
    ) -> None:
        self.selenium = selenium
        self.playwright = page
        plugin_class = plugin_class or DefaultPlugin
        self.plugin = plugin_class(self)
        self.logger = logger or null_logger
        self.extra_objects = extra_objects or {}

    @property
    def url(self) -> str:
        """Returns the current URL of the browser."""
        result = self.selenium.current_url
        self.logger.debug("current_url -> %r", result)
        return result

    @url.setter
    def url(self, address: str) -> None:
        """Opens the address in the browser."""
        self.logger.info("Opening URL: %r", address)
        self.selenium.get(address)

    @property
    def title(self) -> str:
        """Returns current title"""
        current_title = self.selenium.title
        self.logger.info("Current title: %r", current_title)
        return current_title

    @property
    def title_play(self) -> str:
        """Returns the current page title."""
        current_title = self.playwright.title()
        self.logger.info("Current title: %r", current_title)
        return current_title

    @property
    def handles_alerts(self) -> bool:
        return self.selenium.capabilities.get("handlesAlerts", True)

    @property
    def browser_type(self) -> str:
        return self.selenium.capabilities.get("browserName")

    @property
    def browser_version(self) -> int:
        version = self.selenium.capabilities.get(
            "browserVersion"
        ) or self.selenium.capabilities.get("version")
        return int(version.split(".")[0])

    @property
    def browser(self) -> "Browser":
        """Implemented so :py:class:`widgetastic.widget.View` does not have to check the
        instance of its parent. This property exists there so here it just stops the chain"""
        return self

    @property
    def root_browser(self) -> "Browser":
        return self

    @property
    def product_version(self):
        """In order for :py:class:`widgetastic.utils.VersionPick` to work on
        :py:class:`widgetastic.widget.Widget` instances, you need to override this property
        that will enable this functionality.
        """
        raise NotImplementedError("You have to implement product_version")

    @staticmethod
    def _process_locator(locator: LocatorAlias) -> Union[WebElement, Locator]:
        """Processes the locator so the :py:meth:`elements` gets exactly what it needs."""
        if isinstance(locator, WebElement):
            return locator
        if hasattr(locator, "__element__"):
            # https://github.com/python/mypy/issues/1424
            return cast("Widget", locator).__element__()
        try:
            return Locator(locator)
        except TypeError:
            if hasattr(locator, "__locator__"):
                # Deal with the case when __locator__ returns a webelement.
                loc = cast(LocatorProtocol, locator).__locator__()
                if isinstance(loc, WebElement):
                    return loc
            raise LocatorNotImplemented(
                f"You have to implement __locator__ on {type(locator)!r}"
            ) from None

    @staticmethod
    def _locator_force_visibility_check(locator: LocatorAlias) -> Optional[bool]:
        if hasattr(locator, "__locator__") and hasattr(locator, "CHECK_VISIBILITY"):
            return cast(LocatorProtocol, locator).CHECK_VISIBILITY
        else:
            return None

    @retry_stale_element
    def elements(
        self,
        locator: LocatorAlias,
        parent: Optional[ElementParent] = None,
        check_visibility: bool = False,
        check_safe: bool = True,
        force_check_safe: bool = False,
        *args,
        **kwargs,
    ) -> List[WebElement]:
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
            check_safe: You can turn off the page safety check. It is turned off automatically when
                :py:class:`WebElement` is passed.

        Returns:
            A :py:class:`list` of :py:class:`selenium.webdriver.remote.webelement.WebElement`
        """
        if force_check_safe:
            import warnings

            warnings.warn(
                "force_check_safe has been removed and left in definition "
                "only for backward compatibility. "
                "It will also be removed from definition soon.",
                category=DeprecationWarning,
            )
        if check_safe:
            self.plugin.ensure_page_safe()
        from .widget import Widget

        locator = self._process_locator(locator)
        # Get result
        if isinstance(locator, WebElement):
            result = [locator]
        else:
            if parent:
                if isinstance(parent, Browser):
                    root_element = parent.selenium
                elif isinstance(parent, WebElement):
                    root_element = parent
                elif isinstance(parent, Widget):
                    root_element = self.element(parent, parent=parent.locatable_parent)
                elif hasattr(parent, "__locator__"):
                    root_element = self.element(parent, check_visibility=check_visibility)
                else:
                    # TODO: handle intermediate views that do not have __locator__
                    root_element = self.selenium
            else:
                root_element = self.selenium
            result = root_element.find_elements(*locator)

        if check_visibility:
            result = [e for e in result if self.is_displayed(e)]

        return result

    def elements_play(
        self,
        locator: Union[str, dict, ElementHandle],
        parent: Optional[Union[Locator, ElementHandle]] = None,
        check_visibility: bool = False,
        check_safe: bool = True,
        force_check_safe: bool = False,
        *args,
        **kwargs,
    ) -> List[ElementHandle]:
        """Method that resolves locators into Playwright ElementHandles.

        Args:
            locator: A valid locator. Valid locators are:
                * strings (CSS or XPath selectors).
                * dictionaries - like ``{'xpath': '//something'}``.
                * :py:class:`ElementHandle` instances.
            parent: A parent element or locator.
            check_visibility: If set to ``True`` it will filter out elements that are not visible.
            check_safe: Checks if the page is safe to interact with.
        Returns:
            A :py:class:`list` of :py:class:`ElementHandle`
        """

        if force_check_safe:
            import warnings

            warnings.warn(
                "force_check_safe has been removed and left in definition "
                "only for backward compatibility. "
                "It will also be removed from definition soon.",
                category=DeprecationWarning,
            )

        locator = self._process_locator_play(locator)

        # Resolve root element or page
        if isinstance(locator, ElementHandle):
            result = [locator]
        else:
            root_element = self.resolve_parent_element_play(parent)
            result = self.find_elements_play(locator, root_element)

        if check_visibility:
            result = [e for e in result if e.is_visible()]

        return result

    def _process_locator_play(
        self, locator: Union[str, dict, ElementHandle]
    ) -> Union[str, ElementHandle]:
        """Converts locator to string for Playwright (CSS or XPath)."""
        if isinstance(locator, ElementHandle):
            return locator
        elif isinstance(locator, dict):
            # Handle dictionary-based locators, assuming XPath for simplicity
            if "xpath" in locator:
                return locator["xpath"]
            elif "css" in locator:
                return locator["css"]
            else:
                raise ValueError(f"Unsupported locator format: {locator}")
        return locator

    def resolve_parent_element_play(
        self, parent: Optional[Union[PlayLocator, ElementHandle]]
    ) -> PlayLocator:
        """Resolves the parent element or defaults to the page."""
        if parent is None:
            return self.playwright
        elif isinstance(parent, ElementHandle):
            return parent
        return parent

    def find_elements_play(
        self, locator: str, root: Union[Page, ElementHandle]
    ) -> List[ElementHandle]:
        """Finds elements using the provided locator under the root element."""
        if locator.startswith("//"):
            # If locator looks like an XPath, use it
            return root.query_selector_all(f"xpath={locator}")
        else:
            # Otherwise, treat as a CSS selector
            return root.query_selector_all(locator)

    def wait_for_element(
        self,
        locator: str,
        parent: Optional[ElementParent] = None,
        visible: bool = False,
        timeout: Union[float, int] = 5,
        delay: float = 0.2,
        exception: bool = True,
        ensure_page_safe: bool = False,
    ) -> Optional[WebElement]:
        """Wait for presence or visibility of elements specified by a locator.

        Args:
            locator, parent: Arguments for :py:meth:`elements`
            visible: If False, then it only checks presence not considering visibility. If True, it
                     also checks visibility.
            timeout: How long to wait for.
            delay: How often to check.
            exception: If True (default), in case of element not being found an exception will be
                       raised. If False, it returns None.
            ensure_page_safe: Whether to call the ``ensure_page_safe`` hook on repeat.

        Returns:
            :py:class:`selenium.webdriver.remote.webelement.WebElement` if element found according
            to params. ``None`` if not found and ``exception=False``.

        Raises:
            :py:class:`selenium.common.exceptions.NoSuchElementException` if element not found.
        """

        def _element_lookup():
            try:
                return self.elements(
                    locator,
                    parent=parent,
                    check_visibility=visible,
                    check_safe=ensure_page_safe,
                )
            # allow other exceptions through to caller on first wait
            except NoSuchElementException:
                return False

        # turn the timeout into NoSuchElement
        try:
            result = wait_for(
                _element_lookup,
                num_sec=timeout,
                delay=delay,
                fail_condition=lambda elements: not bool(elements),
                fail_func=self.plugin.ensure_page_safe if ensure_page_safe else None,
            )
        except TimedOutError:
            if exception:
                raise NoSuchElementException(
                    f"Failed waiting for element with {locator} in {parent}"
                ) from None
            else:
                return None
        # wait_for returns NamedTuple, return first item from 'out', the WebElement
        return result.out[0]

    def wait_for_element_play(
        self,
        locator: str,
        visible: bool = False,
        timeout: Union[float, int] = 5000,  # Playwright's timeout is in milliseconds
        exception: bool = True,
        ensure_page_safe: bool = False,
    ) -> Optional[str]:
        """
        Wait for presence or visibility of an element specified by a locator.

        Args:
            locator (str): The selector or locator to find the element.
            visible (bool): If True, it checks for visibility as well as presence.
            timeout (int or float): How long to wait for (in milliseconds). Defaults to 5000 ms.
            exception (bool): If True (default), raises an error if the element isn't found.
                              If False, returns None if not found.
            ensure_page_safe (bool): Not used in this context, can be removed if unnecessary.

        Returns:
            The Playwright locator if found; None if not found and exception is False.

        Raises:
            PlaywrightTimeoutError if the element is not found and exception is True.
        """
        try:
            if visible:
                # Wait for the element to be visible
                self.playwright.locator(locator).wait_for(state="visible", timeout=timeout)
            else:
                # Wait for the element to be present in the DOM
                self.playwright.locator(locator).wait_for(state="attached", timeout=timeout)

            return self.playwright.locator(locator)
        except PlaywrightTimeoutError:
            if exception:
                raise PlaywrightTimeoutError(f"Failed waiting for element with locator: {locator}")
            else:
                return None

    def element(self, locator: LocatorAlias, *args, **kwargs) -> WebElement:
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
                kwargs["check_visibility"] = vcheck
            elements = self.elements(locator, *args, **kwargs)
            return elements[0]
        except IndexError:
            raise NoSuchElementException(f"Could not find an element {repr(locator)}") from None

    def element_play(self, locator: Any, *args, **kwargs) -> PlayLocator:
        """Returns a Locator for the specified element.

        Args:
            locator: The locator for the element.

        Returns:
            A Locator object representing the element.

        Raises:
            Error if the element is not found.
        """
        try:
            vcheck = self._locator_force_visibility_check(locator)
            if vcheck is not None:
                kwargs["visible"] = vcheck  # Use Playwright's 'visible' option

            elements = self.elements_play(
                locator, *args, **kwargs
            )  # Assuming this method returns a list of Locators
            return elements[0]  # Return the first element

        except IndexError:
            raise Exception(
                f"Could not find an element {repr(locator)}"
            )  # Playwright's equivalent for not found

    def perform_click(self) -> None:
        """Clicks the left mouse button at the current mouse position."""
        ActionChains(self.selenium).click().perform()

    def perform_double_click(self) -> None:
        """Double-clicks the left mouse button at the current mouse position."""
        ActionChains(self.selenium).double_click().perform()

    @retry_stale_element
    def click(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Clicks at a specific element using two separate events (mouse move, mouse click).

        Args: See :py:meth:`elements`
        """
        self.logger.debug("click: %r", locator)
        ignore_ajax = kwargs.pop("ignore_ajax", False)
        force_scroll = self.browser_type == "firefox"
        el = self.move_to_element(locator, force_scroll=force_scroll, *args, **kwargs)
        self.plugin.before_click(el, locator)
        # and then click on current mouse position
        self.perform_click()
        if not ignore_ajax:
            try:
                self.plugin.ensure_page_safe()
            except TimedOutError:
                try:
                    self.plugin.after_click_safe_timeout(el, locator)
                except UnexpectedAlertPresentException:
                    pass
                except Exception:
                    raise
            except UnexpectedAlertPresentException:
                pass
        try:
            self.plugin.after_click(el, locator)
        except UnexpectedAlertPresentException:
            pass

    def click_play(self, locator: str, ignore_ajax: bool = False, *args, **kwargs) -> None:
        """
        Clicks a specific element using Playwright's click method.

        Args:
            locator (str): The selector or locator to find the element.
            ignore_ajax (bool): If True, it won't wait for network activity after clicking.
        """
        # Move to the element and click
        self.playwright.locator(locator).hover()
        self.playwright.locator(locator).click()

        # Optionally wait for any AJAX or page activity if not ignoring it
        if not ignore_ajax:
            self.playwright.wait_for_load_state("networkidle")

    @retry_stale_element
    def double_click(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Double-clicks at a specific element using two separate events (mouse move, mouse click).

        Args: See :py:meth:`elements`
        """
        self.logger.debug("double_click: %r", locator)
        ignore_ajax = kwargs.pop("ignore_ajax", False)
        force_scroll = self.browser_type == "firefox"
        el = self.move_to_element(locator, force_scroll=force_scroll, *args, **kwargs)
        self.plugin.before_click(el, locator)
        # and then click on current mouse position
        self.perform_double_click()
        if not ignore_ajax:
            try:
                self.plugin.ensure_page_safe()
            except TimedOutError:
                try:
                    self.plugin.after_click_safe_timeout(el, locator)
                except UnexpectedAlertPresentException:
                    pass
                except Exception:
                    raise
            except UnexpectedAlertPresentException:
                pass
        try:
            self.plugin.after_click(el, locator)
        except UnexpectedAlertPresentException:
            pass

    @retry_stale_element
    def raw_click(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Clicks at a specific element using the direct event.

        Args: See :py:meth:`elements`
        """
        self.logger.debug("raw_click: %r", locator)
        ignore_ajax = kwargs.pop("ignore_ajax", False)
        el = self.element(locator, *args, **kwargs)
        self.plugin.before_click(el, locator)
        el.click()
        if not ignore_ajax:
            try:
                self.plugin.ensure_page_safe()
            except TimedOutError:
                try:
                    self.plugin.after_click_safe_timeout(el, locator)
                except UnexpectedAlertPresentException:
                    pass
                except Exception:
                    raise
            except UnexpectedAlertPresentException:
                pass
        try:
            self.plugin.after_click(el, locator)
        except UnexpectedAlertPresentException:
            pass

    @retry_stale_element
    def is_displayed(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Check if the element represented by the locator is displayed.

        Args: See :py:meth:`elements`

        Returns:
            A :py:class:`bool`
        """
        kwargs["check_visibility"] = False
        try:
            return self.move_to_element(locator, *args, **kwargs).is_displayed()
        except (NoSuchElementException, MoveTargetOutOfBoundsException):
            return False

    def is_displayed_play(self, locator: PlayLocator) -> bool:
        """Check if the element represented by the locator is displayed.

        Args:
            locator: The locator for the element.

        Returns:
            A bool indicating whether the element is displayed.
        """
        try:
            element = self.playwright.locator(locator)
            # Check if the element is visible
            return element.is_visible()
        except Exception:
            return False

    @retry_stale_element
    def move_to_element(self, locator: LocatorAlias, *args, **kwargs) -> WebElement:
        """Moves the mouse cursor to the middle of the element represented by the locator.

        Can handle moving to the ``<option>`` tags or Firefox being pissy and thus making it utilize
        a JS workaround, ...

        Args: See :py:meth:`elements`

        Returns:
            :py:class:`selenium.webdriver.remote.webelement.WebElement`
        """
        kw = kwargs.copy()
        force_scroll = kw.pop("force_scroll", False)
        highlight_element = kw.pop("highlight_element", False)
        self.logger.debug("move_to_element: %r", locator)
        el = self.element(locator, *args, **kw)
        if el.tag_name == "option":
            # Instead of option, let's move on its parent <select> if possible
            parent = self.element("..", parent=el)
            if parent.tag_name == "select":
                self.move_to_element(parent)
                return el

        # element can be obscured by e.g. sticky header,
        # selenium doesn't recognize this case as MoveTargetOutOfBoundsException,
        # thus we have to forcefully scroll the page to have the element in the center
        if force_scroll:
            self.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)

        move_to = ActionChains(self.selenium).move_to_element(el)
        try:
            move_to.perform()
        except MoveTargetOutOfBoundsException:
            # ff workaround
            self.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
            try:
                move_to.perform()
            except MoveTargetOutOfBoundsException:  # This has become desperate now.
                raise MoveTargetOutOfBoundsException(
                    "Despite all the workarounds, scrolling to `{}` was unsuccessful.".format(
                        locator
                    )
                ) from None
        except ElementNotInteractableException:
            # ChromeDriver 89 started throwing this exception if an element is hidden, because it
            # has no size and location.
            if self.browser_type == "chrome" and self.browser_version >= 89:
                pass
        except WebDriverException as e:
            # Handling Edge weirdness
            if self.browser_type == "MicrosoftEdge" and "Invalid argument" in e.msg:
                # Moving to invisible element triggers a WebDriverException instead of the former
                # MoveTargetOutOfBoundsException with NORMAL, SANE BROWSERS.
                pass
            # It seems Firefox 60 or geckodriver have an issue related to moving to hidden elements
            # https://github.com/mozilla/geckodriver/issues/1269
            if (
                self.browser_type == "firefox"
                and self.browser_version >= 60
                and ("rect is undefined" in e.msg or "Component returned failure code" in e.msg)
            ):
                pass
            elif "failed to parse value of getElementRegion" in e.msg:
                # The element is located in Shadow DOM (at least in Chrome), so no moving
                pass
            # ChromeDriver is not able to MoveToElement that is not visible, because it has no
            # location. Previous version silently ignored such attempts, but with version 76, it
            # detects the invalid action and throws the error as you saw. The error message will be
            # improved in version 78.
            # https://bugs.chromium.org/p/chromedriver/issues/detail?id=3110
            # https://bugs.chromium.org/p/chromedriver/issues/detail?id=3087
            elif (
                self.browser_type == "chrome"
                and 76 <= self.browser_version < 78
                and ("Cannot read property 'left' of undefined" in e.msg)
            ):
                pass
            # Previous issue ^ wasn't fixed in Chrome 78 but throws another error
            elif (
                self.browser_type == "chrome"
                and self.browser_version >= 78
                and (
                    "Failed to execute 'elementsFromPoint' on 'Document': The provided double "
                    "value is non-finite." in e.msg
                )
            ):
                pass
            elif (
                self.browser_type == "chrome"
                and self.browser_version >= 123
                and ("has no size and location" in e.msg)
            ):
                pass
            else:
                # Something else, never let it sink
                raise
        if highlight_element:
            self.plugin.highlight_element(el)
        return el

    def move_to_element_play(self, locator: str, *args, **kwargs) -> None:
        """
        Moves the mouse cursor to the middle of the element represented by the locator.

        Args:
            locator: A string representing the locator (e.g., CSS selector, XPath).
        """
        # Use the locator to find the element and move the mouse to it.
        element = self.playwright.locator(locator)
        element.evaluate("(el) => el.scrollIntoView()")
        self.logger.debug("Hovered over element at locator: %r", locator)
        return element

    def drag_and_drop(self, source: LocatorAlias, target: LocatorAlias) -> None:
        """Drags the source element and drops it into target.

        Args:
            source: Locator or the source element itself
            target: Locator or the target element itself.
        """
        self.logger.debug("drag_and_drop %r to %r", source, target)
        ActionChains(self.selenium).drag_and_drop(
            self.element(source), self.element(target)
        ).perform()

    def drag_and_drop_by_offset(self, source: LocatorAlias, by_x: int, by_y: int) -> None:
        """Drags the source element and drops it into target.

        Args:
            source: Locator or the source element itself
            target: Locator or the target element itself.
        """
        self.logger.debug("drag_and_drop_by_offset %r X:%r Y:%r", source, by_x, by_y)
        ActionChains(self.selenium).drag_and_drop_by_offset(
            self.element(source), by_x, by_y
        ).perform()

    def drag_and_drop_to(
        self,
        source: LocatorAlias,
        to_x: Optional[int] = None,
        to_y: Optional[int] = None,
    ) -> None:
        """Drags an element to a target location specified by ``to_x`` and ``to_y``

        At least one of ``to_x`` or ``to_y`` must be specified.

        Args:
            source: Dragged element.
            to_x: Absolute location on the X axis where to drag the element.
            to_y: Absolute location on the Y axis where to drag the element.
        """
        self.logger.debug("drag_and_drop_to %r X:%r Y:%r", source, to_x, to_y)
        if to_x is None and to_y is None:
            raise TypeError("You need to pass either to_x or to_y or both")
        middle = self.middle_of(source)
        if to_x is None:
            to_x = middle.x
        if to_y is None:
            to_y = middle.y
        return self.drag_and_drop_by_offset(source, to_x - middle.x, to_y - middle.y)

    def move_by_offset(self, x: int, y: int) -> None:
        self.logger.debug("move_by_offset X:%r Y:%r", x, y)
        ActionChains(self.selenium).move_by_offset(x, y).perform()

    @retry_stale_element
    def execute_script(self, script: str, *args, silent=False, **kwargs) -> Any:
        """Executes a script."""
        from .widget import Widget

        if not silent:
            self.logger.debug("execute_script: %r", script)
        processed_args = []
        for arg in args:
            if isinstance(arg, Widget):
                processed_args.append(arg.__element__())
            else:
                processed_args.append(arg)
        return self.selenium.execute_script(dedent(script), *processed_args, **kwargs)

    def refresh(self) -> None:
        """Triggers a page refresh."""
        return self.selenium.refresh()

    @retry_stale_element
    def classes(self, locator: LocatorAlias, *args, **kwargs) -> Set[str]:
        """Return a list of classes attached to the element.

        Args: See :py:meth:`elements`

        Returns:
            A :py:class:`set` of strings with classes.
        """
        result = set(
            self.execute_script(
                EXTRACT_CLASSES_OF_ELEMENT,
                self.element(locator, *args, **kwargs),
                silent=True,
            )
        )
        self.logger.debug("css classes for %r => %r", locator, result)
        return result

    def classes_play(self, locator: str) -> set:
        """
        Returns a set of classes attached to the element identified by the locator.

        Args:
            locator: A string representing the locator (e.g., CSS selector, XPath).

        Returns:
            A set of strings with the classes.
        """
        # Use the locator to find the element.
        element = self.playwright.locator(locator)

        # Use JavaScript to retrieve the class list of the element.
        class_list = element.evaluate("(el) => el.className.split(' ').filter(Boolean)")
        self.logger.debug(f"CSS classes for {locator} => {class_list}")

        # Convert the list to a set to ensure uniqueness.
        return set(class_list)

    def tag(self, *args, **kwargs) -> str:
        """Returns the tag name of the element represented by the locator passed.

        Args: See :py:meth:`elements`

        Returns:
            :py:class:`str` with the tag name
        """
        return self.element(*args, **kwargs).tag_name

    def tag_play(self, locator: str, *args, **kwargs) -> str:
        """Returns the tag name of the element represented by the locator passed.

        Args: locator: The selector string or locator of the element.

        Returns:
            str: The tag name of the element.
        """
        element = self.playwright.locator(locator)
        tag_name = element.evaluate("element => element.tagName.toLowerCase()")
        return tag_name

    @retry_stale_element
    def text(self, locator: LocatorAlias, *args, **kwargs) -> str:
        """Returns the text inside the element represented by the locator passed.

        The returned text is normalized with :py:func:`widgetastic.xpath.normalize_space` as defined
        by XPath standard.

        Args: See :py:meth:`elements`

        Returns:
            :py:class:`str` with the text
        """
        try:
            text = self.element(locator, *args, **kwargs).text
        except MoveTargetOutOfBoundsException:
            text = ""

        if not text:
            # It is probably invisible
            text = self.execute_script(
                "return arguments[0].textContent || arguments[0].innerText;",
                self.element(locator, *args, **kwargs),
                silent=True,
            )
            if text is None:
                text = ""

        result = normalize_space(text)
        self.logger.debug("text(%r) => %r", locator, crop_string_middle(result))
        return result

    def text_play(self, locator: str, *args, **kwargs) -> str:
        """Returns the normalized text inside the element represented by the locator passed.

        Args:
            locator: The selector string or locator of the element.

        Returns:
            str: The normalized text content of the element.
        """
        element = self.playwright.locator(locator)

        # Fetch text content, handling cases where the element might be invisible or empty
        try:
            text_content = element.text_content()
        except Exception as e:
            # Handle cases where the text content can't be retrieved, fall back to empty string
            self.logger.error(f"Error fetching text content for {locator}: {e}")
            text_content = ""

        # Normalize the text by stripping extra spaces
        return text_content.strip() if text_content else ""

    @retry_stale_element
    def attributes(self, locator: LocatorAlias, *args, **kwargs) -> Dict:
        """Return a dict of attributes attached to the element.

        Args: See :py:meth:`elements`

        Returns:
            A :py:class:`dict` of attributes and respective values.
        """
        result = self.execute_script(
            EXTRACT_ATTRIBUTES_OF_ELEMENT,
            self.element(locator, *args, **kwargs),
            silent=True,
        )
        self.logger.debug("css attributes for %r => %r", locator, result)
        return result

    def attributes_play(self, locator: str, *args, **kwargs) -> dict:
        """Return a dictionary of attributes attached to the element.

        Args:
            locator: The selector string or locator of the element.

        Returns:
            dict: A dictionary of attributes and their respective values.
        """
        element = self.playwright.locator(locator)

        try:
            # Use JavaScript to get all attributes of the element
            attributes = element.evaluate(
                "(el) => { let attrs = {}; for (let attr of el.attributes) { attrs[attr.name] = attr.value; } return attrs; }"
            )
        except Exception as e:
            self.logger.error(f"Error fetching attributes for {locator}: {e}")
            attributes = {}

        return attributes

    @retry_stale_element
    def get_attribute(self, attr: str, *args, **kwargs) -> Optional[str]:
        return self.element(*args, **kwargs).get_attribute(attr)

    def get_attribute_play(self, attr: str, locator: str, *args, **kwargs) -> str:
        """
        Returns the value of the specified attribute of the element.

        Args:
            locator: The locator of the element.
            attr: The attribute to retrieve the value of.

        Returns:
            The value of the specified attribute as a string.
        """
        # Locate the element using Playwright
        element: Locator = self.element_play(locator, *args, **kwargs)

        # Retrieve the attribute value
        attribute_value = element.get_attribute(attr)

        if attribute_value is None:
            self.logger.warning(f"Attribute '{attr}' not found for element located by {locator}")
            return ""

        self.logger.debug(f"Attribute '{attr}' for {locator} => {attribute_value}")
        return attribute_value

    @retry_stale_element
    def set_attribute(self, attr: str, value: str, *args, **kwargs) -> None:
        return self.execute_script(
            "arguments[0].setAttribute(arguments[1], arguments[2]);",
            self.element(*args, **kwargs),
            attr,
            value,
        )

    def set_attribute_play(self, locator: str, attr: str, value: str) -> None:
        """
        Sets an attribute on an element.

        Args:
            locator: The locator of the element (e.g., CSS selector or XPath).
            attr: The name of the attribute to set.
            value: The value to set for the attribute.
        """
        # Find the element using the locator and set the attribute using JavaScript
        print(f"\n{attr=}, \n{value=}")
        element = self.playwright.locator(locator)
        element.evaluate(
            "(el, props) => el.setAttribute(props.attr, props.value)",
            {"attr": attr, "value": value},
        )

    def size_of(self, *args, **kwargs) -> Size:
        """Returns element's size as a tuple of width/height."""
        size = self.element(*args, **kwargs).size
        return Size(size["width"], size["height"])

    def size_of_play(self, locator: str, *args, **kwargs) -> Size:
        """
        Returns the element's size as a named tuple of width and height.

        Args:
            locator: A string representing the selector of the element.
            *args: Additional arguments (if any).
            **kwargs: Additional keyword arguments (if any).

        Returns:
            A named tuple containing the width and height of the element.
        """
        # Locate the element using the provided locator
        element = self.playwright.locator(locator, *args, **kwargs)

        # Get the bounding box of the element
        bounding_box = element.bounding_box()

        # Extract width and height from the bounding box
        width = bounding_box["width"]
        height = bounding_box["height"]

        # Return as a named tuple for easier access
        return Size(width, height)

    def location_of(self, *args, **kwargs) -> Location:
        """Returns element's location as a tuple of x/y."""
        location = self.element(*args, **kwargs).location
        return Location(location["x"], location["y"])

    def middle_of(self, *args, **kwargs) -> Location:
        """Returns element's location as a tuple of x/y."""
        size = self.size_of(*args, **kwargs)
        location = self.location_of(*args, **kwargs)
        return Location(int(location.x + size.width / 2), int(location.y + size.height / 2))

    def clear(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Clears a text input with given locator."""
        self.logger.debug("clear: %r", locator)

        el = self.element(locator, *args, **kwargs)
        self.plugin.before_keyboard_input(el, None)

        self.click(locator, *args, **kwargs)
        # CTRL + A doesn't work on 'number' types, as
        # browser does not treat the numeric value as selectable text
        if el.get_attribute("type") == "number":
            self.execute_script("arguments[0].value = '';", el)
            el.send_keys(Keys.SPACE, Keys.BACK_SPACE)

        ActionChains(self.selenium).key_down(Keys.CONTROL).send_keys("a").key_up(
            Keys.CONTROL
        ).perform()
        el.send_keys(Keys.DELETE)

        self.plugin.after_keyboard_input(el, None)

        return el.get_attribute("value") == ""

    def clear_play(self, locator: str, *args, **kwargs) -> None:
        """Clears a text input with the given locator."""
        input_locator = self.playwright.locator(locator)

        try:
            # First attempt: use the fill method to clear the input
            input_locator.fill("")  # Try to clear the input by setting it to an empty string
            # Verify if the input is cleared
            if input_locator.evaluate("el => el.value") == "":
                return
        except Exception as e:
            print(f"fill() method failed with error: {e}")

        try:
            # Second attempt: use JavaScript to clear the value
            input_locator.evaluate("el => el.value = ''")
            # Verify if the input is cleared
            if input_locator.evaluate("el => el.value") == "":
                print("Input cleared using JavaScript.")
                return
        except Exception as e:
            print(f"JavaScript method failed with error: {e}")

    def is_selected(self, *args, **kwargs) -> bool:
        return self.element(*args, **kwargs).is_selected()

    def send_keys(self, text: str, locator: LocatorAlias, sensitive=False, *args, **kwargs) -> None:
        """Sends keys to the element. Detects the file inputs automatically.

        Args:
            text: Text to be inserted to the element.
            sensitive: Bool, If is set to True do not log sensitive data.
            *args: See :py:meth:`elements`
            **kwargs: See :py:meth:`elements`
        """
        text = str(text) or ""
        file_intercept = False
        # If the element is input type file, we will need to use the file detector
        if self.tag(locator, *args, **kwargs) == "input":
            type_attr = self.get_attribute("type", locator, *args, **kwargs)
            if type_attr and type_attr.strip() == "file":
                file_intercept = True
        try:
            if file_intercept:
                # If we detected a file upload field, let's use the file detector.
                self.selenium.file_detector = LocalFileDetector()
            el = self.move_to_element(locator, *args, **kwargs)
            self.plugin.before_keyboard_input(el, text)
            self.logger.debug("send_keys %r to %r", "*" * len(text) if sensitive else text, locator)
            result = el.send_keys(text)
            if Keys.ENTER not in text:
                try:
                    self.plugin.after_keyboard_input(el, text)
                except StaleElementReferenceException:
                    pass
            else:
                self.logger.info(
                    "skipped the after_keyboard_input call due to %r containing ENTER.",
                    text,
                )
            return result
        finally:
            # Always the UselessFileDetector for all other kinds of fields, so do not leave
            # the LocalFileDetector there.
            if file_intercept:
                self.selenium.file_detector = UselessFileDetector()

    def send_keys_play(
        self, text: str, locator: LocatorAlias, sensitive=False, *args, **kwargs
    ) -> None:
        """
        Sends keys to the element. Clears the input field before typing.
        Detects file inputs automatically and handles sensitive text.

        Args:
            text: Text to be inserted into the element.
            sensitive: If True, sensitive data will not be logged.
            *args: Additional arguments.
            **kwargs: Additional keyword arguments.
        """
        text = str(text) or ""
        file_intercept = False

        # Check if the element is an input of type file
        element = self.element_play(locator, *args, **kwargs)
        tag_name = element.evaluate("el => el.tagName.toLowerCase()")

        if tag_name == "input":
            input_type = element.get_attribute("type")
            if input_type and input_type.strip() == "file":
                file_intercept = True

        # Handle file input field
        if file_intercept:
            self.logger.debug(f"Uploading file {text} to {locator}")
            element.set_input_files(text)
        else:
            # Clear the input field before typing
            element.fill("")  # Clear the input field

            # Log sensitive data conditionally
            self.logger.debug(f"Sending keys {'*' * len(text) if sensitive else text} to {locator}")
            element.fill(text)  # Use `fill` to input the text

        # Optionally handle ENTER key separately if needed
        if "\n" in text:
            self.logger.info(f"Detected ENTER in the text {text}")

    def send_keys_to_focused_element(self, *keys: str) -> None:
        """Sends keys to current focused element.

        Args:
            keys: The keys to send.
        """
        ActionChains(self.selenium).send_keys(*keys).perform()

    def copy(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Select all and copy to clipboard."""
        self.logger.debug("copy: %r", locator)
        el = self.element(locator)
        self.click(locator, *args, **kwargs)
        self.plugin.before_keyboard_input(el, None)
        ActionChains(self.selenium).key_down(Keys.CONTROL).send_keys("a").key_up(
            Keys.CONTROL
        ).perform()
        ActionChains(self.selenium).key_down(Keys.CONTROL).send_keys("c").key_up(
            Keys.CONTROL
        ).perform()
        self.plugin.after_keyboard_input(el, None)

    def copy_play(self, locator: str) -> None:
        """
        Selects all text in an element and copies it to the clipboard.

        Args:
            page: A Playwright Page object.
            locator: A string representing the selector of the input element.
        """
        # Locate the input element and Click on the element to ensure it has focus
        self.playwright.locator(locator).click()

        # Simulate keyboard events to select all text and copy it
        # Adjust for macOS with 'Meta' if necessary
        self.playwright.keyboard.press("Control+A")  # Select all text (use 'Meta+A' on macOS)
        self.playwright.keyboard.press(
            "Control+C"
        )  # Copy the selected text (use 'Meta+C' on macOS)

    def paste(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Paste from clipboard to current element."""
        self.logger.debug("paste: %r", locator)
        el = self.element(locator)
        self.click(locator, *args, **kwargs)
        self.plugin.before_keyboard_input(el, None)
        ActionChains(self.selenium).key_down(Keys.CONTROL).send_keys("v").key_up(
            Keys.CONTROL
        ).perform()
        self.plugin.after_keyboard_input(el, None)

    def paste_play(self, locator: str) -> None:
        """
        Pastes clipboard content into the specified element.

        Args:
            page: A Playwright Page object.
            locator: A string representing the selector of the input element.
        """
        # Locate the input element and Click on the element to ensure it has focus
        self.playwright.locator(locator).click()

        # Simulate keyboard events to paste content
        # Adjust for macOS with 'Meta' if necessary
        self.playwright.keyboard.press("Control+V")  # Paste content (use 'Meta+V' on macOS)

    def get_alert(self) -> Alert:
        """Returns the current alert object.

        Raises:
            :py:class:`selenium.common.exceptions.NoAlertPresentException`
        """
        if not self.handles_alerts:
            return None
        return self.selenium.switch_to.alert

    @property
    def alert_present(self) -> bool:
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

    def dismiss_any_alerts(self) -> None:
        """Loops until there are no further alerts present to dismiss.

        Useful for handling the cases where the alert pops up multiple times.
        """
        try:
            while self.alert_present:
                alert = self.get_alert()
                self.logger.info("dismissing alert: %r", alert.text)
                alert.dismiss()
        except NoAlertPresentException:  # Just in case. alert_present should be reliable
            pass

    def handle_alert(
        self,
        cancel: bool = False,
        wait: float = 30.0,
        squash: bool = False,
        prompt: Optional[str] = None,
        check_present: bool = False,
    ) -> Optional[bool]:
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
            self.logger.info("handling alert: %r", popup.text)
            if prompt is not None:
                self.logger.info("  answering prompt: %r", prompt)
                popup.send_keys(prompt)
            if cancel:
                self.logger.info("  dismissing")
                popup.dismiss()
            else:
                self.logger.info("  accepting")
                popup.accept()
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

    def switch_to_frame(self, *args, **kwargs) -> None:
        parent = kwargs.pop("parent", self.browser)
        self.selenium.switch_to.frame(self.element(parent=parent, *args, **kwargs))

    def switch_to_main_frame(self) -> None:
        self.selenium.switch_to.default_content()

    def get_current_location(self) -> str:
        # useful if it is necessary to recognize current frame
        return self.execute_script("return self.location.toString()")

    @property
    def current_window_handle(self) -> str:
        """Returns the current window handle"""
        window_handle = self.selenium.current_window_handle
        self.logger.debug("current_window_handle -> %r", window_handle)
        return window_handle

    @property
    def window_handles(self) -> List[str]:
        """Returns all available window handles"""
        handles = self.selenium.window_handles
        self.logger.debug("window_handles -> %r", handles)
        return handles

    def switch_to_window(self, window_handle: str) -> None:
        """switches focus to the specified window

        Args:
            window_handle: The name or window handle
        """
        self.logger.debug("switch_to_window -> %r", window_handle)
        self.selenium.switch_to.window(window_handle)

    def new_window(self, url: str, focus: bool = False) -> str:
        """Opens the url in new window of the browser.

        Args:
            url: web address to open in new window
            focus: switch focus to new window; default False
        Returns:
            new windows handle
        """
        handles = set(self.window_handles)
        self.logger.info("Opening URL %r in new window", url)
        self.selenium.execute_script(f"window.open('{url}', '_blank')")
        new_handle = (set(self.window_handles) - handles).pop()

        if focus:
            self.switch_to_window(new_handle)
        return new_handle

    def close_window(self, window_handle: Optional[str] = None) -> None:
        """Close window form browser

        Args:
            window_handle: The name or window handle; default current window handle
        """
        main_window_handle = self.current_window_handle
        self.logger.debug(
            "close_window -> %r", window_handle if window_handle else main_window_handle
        )

        if window_handle and window_handle != main_window_handle:
            self.switch_to_window(window_handle)
            self.selenium.close()
            self.switch_to_window(main_window_handle)
        else:
            self.selenium.close()

    def save_screenshot(self, filename: str) -> None:
        """Saves a screenshot of current browser window to a PNG image file.

        Args:
            filename: The full path you wish to save your screenshot to.
                      This should end with a `.png` extension.
        Returns:
            ``False`` for any IOError else ``True``.
        """
        self.logger.debug("Saving screenshot to -> %r", filename)
        self.selenium.save_screenshot(filename=filename)

    def save_screenshot_play(self, filename: str) -> bool:
        """Saves a screenshot of the current browser window to a PNG image file.

        Args:
            filename: The full path where you wish to save your screenshot.
                      This should end with a `.png` extension.

        Returns:
            bool: True if the screenshot is saved successfully, False otherwise.
        """
        self.logger.debug("Saving screenshot to -> %r", filename)
        try:
            # Use Playwright's screenshot method to save the screenshot.
            self.playwright.screenshot(path=filename)
            self.logger.info("Screenshot saved successfully.")
            return True
        except Exception as e:
            self.logger.error("Failed to save screenshot: %s", e)
            return False


class BrowserParentWrapper:
    """A wrapper/proxy class that ensures passing of correct parent locator on elements lookup.

    Required for the proper operation of nesting.

    Assumes the object passed has a ``browser`` attribute.

    Args:
        o: Object which should be considered as a parent element for lookups. Must have ``.browser``
           defined.
    """

    def __init__(self, o: "Widget", browser: Browser) -> None:
        self._o = o
        self._browser = browser

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, BrowserParentWrapper):
            return False
        return self._o == other._o and self._browser == other._browser

    def elements(
        self,
        locator: LocatorAlias,
        parent: Optional[ElementParent] = None,
        check_visibility: bool = False,
        check_safe: bool = True,
        force_check_safe: bool = False,
    ) -> List[WebElement]:
        return self._browser.elements(
            locator,
            parent=parent or self._o,
            check_visibility=check_visibility,
            check_safe=check_safe,
            force_check_safe=force_check_safe,
        )

    def __getattr__(self, attr: str) -> Any:
        """Route all other attribute requests into the parent object's browser. Black magic included

        Here is the explanation:
        If you call ``.elements`` on this object directly, it will correctly inject the parent
        locator. But if you call eg. ``element``, what will happen is that it will invoke the
        original method from underlying browser and that method's ``self`` is the underlying browser
        and not this wrapper. Therefore ``element`` would call the original ``elements`` without
        injecting the parent.

        What this getter does is that if you pull out a method, it detects that, unbinds the
        pure function and rebinds it to this wrapper. The method that came from the browser object
        is now executed not against the browser, but against this wrapper, enabling us to intercept
        every single ``elements`` call.
        """
        value = getattr(self._browser, attr)
        if inspect.ismethod(value):
            function = value.__func__
            # Bind the function like it was defined on this class
            value = function.__get__(self, BrowserParentWrapper)
        return value

    def __repr__(self) -> str:
        return f"<{type(self).__name__} for {self._o!r}>"
