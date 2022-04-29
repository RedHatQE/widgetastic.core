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
        selenium: WebDriver,
        plugin_class: Optional[Type[DefaultPlugin]] = None,
        logger: Optional[Logger] = None,
        extra_objects: Optional[Dict[Any, Any]] = None,
    ) -> None:
        self.selenium = selenium
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
            else:
                # Something else, never let it sink
                raise
        if highlight_element:
            self.plugin.highlight_element(el)
        return el

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

    def tag(self, *args, **kwargs) -> str:
        """Returns the tag name of the element represented by the locator passed.

        Args: See :py:meth:`elements`

        Returns:
            :py:class:`str` with the tag name
        """
        return self.element(*args, **kwargs).tag_name

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

    @retry_stale_element
    def get_attribute(self, attr: str, *args, **kwargs) -> Optional[str]:
        return self.element(*args, **kwargs).get_attribute(attr)

    @retry_stale_element
    def set_attribute(self, attr: str, value: str, *args, **kwargs) -> None:
        return self.execute_script(
            "arguments[0].setAttribute(arguments[1], arguments[2]);",
            self.element(*args, **kwargs),
            attr,
            value,
        )

    def size_of(self, *args, **kwargs) -> Size:
        """Returns element's size as a tuple of width/height."""
        size = self.element(*args, **kwargs).size
        return Size(size["width"], size["height"])

    def location_of(self, *args, **kwargs) -> Location:
        """Returns element's location as a tuple of x/y."""
        location = self.element(*args, **kwargs).location
        return Location(location["x"], location["y"])

    def middle_of(self, *args, **kwargs) -> Location:
        """Returns element's location as a tuple of x/y."""
        size = self.size_of(*args, **kwargs)
        location = self.location_of(*args, **kwargs)
        return Location(int(location.x + size.width / 2), int(location.y + size.height / 2))

    def clear(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Clears a text input with given locator."""
        self.logger.debug("clear: %r", locator)
        el = self.element(locator, *args, **kwargs)
        self.plugin.before_keyboard_input(el, None)
        result = el.clear()
        if el.get_attribute("value") and self.browser_type == "chrome":
            # Chrome is not able to clear input with element.clear() method, use javascript instead
            # We need to click on element
            el.click()
            self.execute_script("arguments[0].value = '';", el)
            # If clearing is not followed by send_keys, the previous text will appear again
            el.send_keys(Keys.SPACE, Keys.BACK_SPACE)
        self.plugin.after_keyboard_input(el, None)
        return result

    def is_selected(self, *args, **kwargs) -> bool:
        return self.element(*args, **kwargs).is_selected()

    def send_keys(self, text: str, locator: LocatorAlias, *args, **kwargs) -> None:
        """Sends keys to the element. Detects the file inputs automatically.

        Args:
            text: Text to be inserted to the element.
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
            self.logger.debug("send_keys %r to %r", text, locator)
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
