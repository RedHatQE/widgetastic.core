"""
Widgetastic Browser Implementation
==================================

This module provides the core Browser class that wraps Playwright's Page functionality
with the widgetastic API. It serves as the main interface for web element interaction,
page navigation, and browser control in the widgetastic framework.

Key Features:
- Playwright Page wrapper with widgetastic API compatibility
- SmartLocator integration for flexible element location
- Plugin system for extending browser behavior
- Frame-aware element operations
- Network activity monitoring and page safety checks
"""

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
from typing import Literal
import warnings

from cached_property import cached_property
from playwright.sync_api import BrowserContext
from playwright.sync_api import ElementHandle, FrameLocator
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator
from playwright.sync_api import Page

from .locator import SmartLocator
from wait_for import TimedOutError

from .exceptions import LocatorNotImplemented
from .exceptions import NoSuchElementException
from .exceptions import WidgetOperationFailed
from .exceptions import FrameNotFoundError


from .log import create_widget_logger
from .log import null_logger
from .types import ElementParent
from .types import LocatorAlias
from .types import LocatorProtocol
from .xpath import normalize_space


if TYPE_CHECKING:
    from .widget.base import Widget


class Size(NamedTuple):
    width: int
    height: int


class Location(NamedTuple):
    x: int
    y: int


class DefaultPlugin:
    def __init__(self, browser: "Browser") -> None:
        self.browser = browser

    @cached_property
    def logger(self):
        """Logger with prepended plugin name.

        Returns:
            Logger instance with the plugin name prepended
        """
        return create_widget_logger(type(self).__name__, self.browser.logger)

    def ensure_page_safe(self, timeout: Union[int, None] = None) -> None:
        """Waits for the page to be quiescent, replacing the old JS-based check.

        Args:
            timeout: Provide timeout in seconds.
        """
        timeout_ms = 0 if timeout is None else timeout * 1000
        self.browser.page.wait_for_load_state("networkidle", timeout=timeout_ms)

    def after_click(self, element: Locator, locator: LocatorAlias) -> None:
        """Invoked after clicking on an element."""
        pass

    def after_click_safe_timeout(self, element: Locator, locator: LocatorAlias) -> None:
        """Invoked after clicking on an element and `ensure_page_safe` failing to wait."""
        pass

    def before_click(self, element: Locator, locator: LocatorAlias) -> None:
        """Invoked before clicking on an element."""
        pass

    def after_keyboard_input(self, element: Locator, keyboard_input: Optional[str]) -> None:
        """Invoked after sending keys into an element.

        Args:
            keyboard_input: String if any text typed in, None if the element is cleared.
        """
        pass

    def before_keyboard_input(self, element: Locator, keyboard_input: Optional[str]) -> None:
        """Invoked after sending keys into an element.

        Args:
            keyboard_input: String if any text typed in, None if the element is cleared.
        """
        pass

    def highlight_element(
        self,
        element: Locator,
        style: str = "border: 2px solid red;",
        visible_for: float = 0.3,
    ) -> None:
        """
        Highlight the passed element by directly changing it's style to the 'style' argument.

        The new style will be visible for 'visible_for' [s] before reverting to the original style.

        Generally, visible_for should not be > 0.5 s. If the timeout is too high and we check
        an element multiple times in quick succession, the modified style will "stick".
        """
        warnings.warn(
            "Playwright's has build-in functionality for highlighting element."
            "Please use browser.highlight(locator)",
            category=DeprecationWarning,
        )
        element.highlight()


class Browser:
    """Playwright browser wrapper with enhanced UI testing capabilities.

    This class wraps Playwright's Page functionality while maintaining the proven widgetastic API
    and incorporating battle-tested improvements developed over years of UI testing experience.
    It provides intelligent element handling, robust interaction patterns, and comprehensive
    workarounds for common web testing challenges.

    Key Improvements Over Standard Playwright:

    - Smart Element Selection:
    When multiple elements match a locator, this wrapper intelligently selects the visible and
    interactable one rather than just the first match. This solves common issues where the first
    element might be hidden behind overlays or in collapsed sections.

    - Robust Text Handling:
    Unlike standard approaches that might fail with overlaid or dynamically loaded text, this
    wrapper uses multiple strategies including JavaScript evaluation to reliably extract text
    content from any element, regardless of CSS styling or positioning.

    - Normalized Text Operations:
    All text operations automatically normalize whitespace using XPath's normalize-space logic.
    When writing XPath expressions, use ``normalize-space(.)="foo"`` patterns for reliable
    text matching across different browsers and rendering engines.

    - Enhanced Click Operations:
    Implements a robust clicking strategy that handles complex UI scenarios like overlays,
    animations, and dynamically positioned elements. Uses intelligent scrolling and positioning
    to ensure reliable interactions.

    - Smart Form Handling:
    Automatically detects form input types and applies appropriate interaction strategies.
    Handles file uploads, date pickers, and other specialized input types without manual
    configuration.

    - Frame Context Management:
    Provides seamless iframe handling with automatic context switching and restoration.

    - Network Activity Monitoring:
    Integrates page safety checks that wait for network activity to stabilize before
    proceeding with interactions, reducing flaky tests caused by timing issues.


    Practical Usage Examples:

    .. code-block:: python

        # Basic browser setup
        browser = Browser(playwright_page)

        # Smart element finding - gets visible element even if others exist
        login_button = browser.element("//button[text()='Login']")

        # Robust clicking with automatic scrolling and overlay handling
        browser.click("#submit-btn")

        # Text extraction that works with any styling
        error_message = browser.element(".error").text

        # Form filling with automatic input type detection
        browser.send_keys("#username", "admin")

        # Iframe handling
        browser.switch_to_frame("//iframe[@name='content']")
        browser.element("#inner-button").click()
        browser.switch_to_main_frame()


    Args:
        page: Playwright Page instance for browser operations
        plugin_class: Optional plugin class for extending browser behavior
        logger: Optional logger instance (uses null_logger if not provided)
        extra_objects: Optional dictionary for storing additional test environment data
    """

    def __init__(
        self,
        page: Page,
        plugin_class: Optional[Type[DefaultPlugin]] = None,
        logger: Optional[Logger] = None,
        extra_objects: Optional[Dict[Any, Any]] = None,
    ) -> None:
        self.page = page
        self.active_context: Union[Page, FrameLocator] = page
        plugin_class = plugin_class or DefaultPlugin
        self.plugin = plugin_class(self)
        self.logger = logger or null_logger
        self.extra_objects = extra_objects or {}

    # ======================== BROWSER & PAGE MANAGEMENT ========================
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

        Returns:
            Product version string (must be implemented in subclasses)

        Raises:
            NotImplementedError: Always raised since this must be implemented in subclasses
        """
        raise NotImplementedError("You have to implement product_version")

    def goto(
        self, address: str, *, wait_until: Optional[str] = "domcontentloaded", **kwargs
    ) -> None:
        """Navigate to the specified URL with config supported by playwright.

        Args:
            address: URL to navigate to
            wait_until: Wait condition before considering navigation successful.
                       Options: "commit", "domcontentloaded", "load", "networkidle", None
            **kwargs: Additional arguments passed to page.goto()
        """
        self.logger.info("Opening URL: %r (wait_until=%s)", address, wait_until)
        self.page.goto(address, wait_until=wait_until, **kwargs)

    @property
    def url(self) -> str:
        """Current page URL. Can be read to get current location or set to navigate.

        Returns:
            Current page URL as a string
        """
        result = self.page.url
        self.logger.debug("current_url -> %r", result)
        return result

    @url.setter
    def url(self, address: str) -> None:
        """Navigate to the specified URL.

        Args:
            address: URL to navigate to
        """
        self.goto(address, wait_until=None)

    @property
    def title(self) -> str:
        """Current page title as displayed in the browser tab.

        Returns:
            Page title as a string
        """
        current_title = self.page.title()
        self.logger.info("Current title: %r", current_title)
        return current_title

    def refresh(self, *args, **kwargs) -> None:
        """Triggers a page refresh.

        Args:
            timeout : Maximum operation time in milliseconds, defaults to 30 seconds.
            wait_until : commit / domcontentloaded / load / networkidle / None
        """
        self.page.reload(*args, **kwargs)

    def close(self) -> None:
        """Close browser page."""
        self.page.close()

    @property
    def is_browser_closed(self) -> bool:
        """Check browser/page is closed.

        Returns:
            True if browser/page is closed, False otherwise
        """
        return self.page.is_closed()

    @property
    def browser_type(self) -> str:
        """Browser engine name (chromium, firefox).

        Returns:
            Browser engine name as a string
        """
        return self.page.context.browser.browser_type.name

    @property
    def browser_version(self) -> int:
        """Major version number of the browser engine.

        Returns:
            Major version number as an integer
        """
        version_str = self.page.context.browser.version
        return int(version_str.split(".")[0])

    def save_screenshot(self, filename: str) -> None:
        """Saves a screenshot of the current page.

        Args:
            filename: Path where the screenshot will be saved
        """
        self.logger.debug("Saving screenshot to -> %r", filename)
        self.page.screenshot(path=filename)

    # ======================= ELEMENT DISCOVERY & WAITING =======================
    @staticmethod
    def _process_locator(locator: LocatorAlias) -> Union[Locator, SmartLocator, None]:
        """Processes the locator so the :py:meth:`elements` gets exactly what it needs.

        Args:
            locator: The locator to be processed

        Returns:
            Processed locator ready for use by elements() method
        """
        if isinstance(locator, (Locator, ElementHandle)):
            return locator

        if hasattr(locator, "__element__"):
            # https://github.com/python/mypy/issues/1424
            return cast("Widget", locator).__element__()
        try:
            return SmartLocator(locator)
        except TypeError:
            if hasattr(locator, "__locator__"):
                loc = cast(LocatorProtocol, locator).__locator__()
                if isinstance(loc, (Locator, ElementHandle)):
                    return loc
                return SmartLocator(loc)
            raise LocatorNotImplemented(
                f"You have to implement __locator__ on {type(locator)!r}"
            ) from None

    @staticmethod
    def _locator_force_visibility_check(locator: LocatorAlias) -> Optional[bool]:
        if hasattr(locator, "__locator__") and hasattr(locator, "CHECK_VISIBILITY"):
            return cast(LocatorProtocol, locator).CHECK_VISIBILITY
        else:
            return None

    def elements(
        self,
        locator: LocatorAlias,
        parent: Optional[ElementParent] = None,
        check_visibility: bool = False,
        check_safe: bool = True,
        force_check_safe: bool = False,
        *args,
        **kwargs,
    ) -> List[Locator]:
        """Find all elements matching the given locator.

        Locates all elements that match the provided locator, with optional parent scoping
        and visibility filtering. Uses SmartLocator for automatic format detection.

        Args:
            locator: Element locator (CSS, XPath, or SmartLocator compatible)
            parent: Optional parent element to scope the search
            check_visibility: If True, only returns visible elements
            check_safe: If True, waits for page to be safe before searching
            force_check_safe: Deprecated parameter, issues warning if used

        Returns:
            List of Playwright Locator objects for found elements

        Note:
            Returns empty list if no elements found (does not raise exception)
        """
        if force_check_safe:
            warnings.warn("force_check_safe is deprecated.", DeprecationWarning)

        if check_safe:
            self.plugin.ensure_page_safe()

        from .widget.base import Widget

        locator = self._process_locator(locator)
        if isinstance(locator, (Locator, ElementHandle)):
            return [locator]
        else:
            if parent:
                if isinstance(parent, Browser):
                    root_element = parent.page
                elif isinstance(parent, (Locator, ElementHandle, FrameLocator)):
                    root_element = parent
                elif isinstance(parent, Widget):
                    root_element = self.element(parent, parent=parent.locatable_parent)
                elif hasattr(parent, "__locator__"):
                    root_element = self.element(parent, check_visibility=check_visibility)
                else:
                    root_element = self.active_context
            else:
                root_element = self.active_context
            try:
                result = root_element.locator(str(locator)).all()
            except PlaywrightError as e:
                # Handle nonexistent iframe case - ensure consistent behavior across Playwright versions
                if "Failed to find frame" in str(e):
                    # Raise a specific frame error with clear semantics
                    raise FrameNotFoundError(f"Failed to find frame: {str(e)}") from e
                else:
                    raise

            if (
                len(result) == 0
                and isinstance(root_element, FrameLocator)
                and root_element == self.active_context
            ):
                try:
                    # Try to access the frame's document - this will fail if frame doesn't exist
                    test_locator = root_element.locator("html, body").first
                    test_locator.wait_for(state="attached", timeout=50)
                except PlaywrightError:
                    raise FrameNotFoundError("Frame not found: nonexistent frame context") from None

        if check_visibility:
            result = [loc for loc in result if loc.is_visible()]

        return result

    def element(self, locator: LocatorAlias, *args, **kwargs) -> Locator:
        """Find a single element matching the given locator.

        Locates the first element that matches the provided locator. Uses SmartLocator
        for automatic format detection and applies visibility checks if specified.

        Args:
            locator: Element locator (CSS, XPath, or SmartLocator compatible)
            *args, **kwargs: Additional arguments passed to elements() method

        Returns:
            Playwright Locator object for the found element

        Raises:
            NoSuchElementException: If no matching element is found
        """
        try:
            vcheck = self._locator_force_visibility_check(locator)
            if vcheck is not None:
                kwargs["check_visibility"] = vcheck

            # Pass all arguments directly to the `elements` method, which contains
            # the correct visibility filtering logic.
            elements = self.elements(locator, *args, **kwargs)
            if not elements:
                raise NoSuchElementException(f"Could not find an element {repr(locator)}")

            return elements[0]
        except IndexError:
            raise NoSuchElementException(f"Could not find an element {repr(locator)}") from None

    def wait_for_element(
        self,
        locator: str,
        parent: Optional[ElementParent] = None,
        visible: bool = False,
        timeout: Union[float, int] = 5,
        exception: bool = True,
        ensure_page_safe: bool = False,
    ) -> Optional[Locator]:
        """Waits for an element matching the locator to appear, optionally checking for visibility.

        Args:
            locator: A string representing the element's locator.
            parent: An optional parent widget or locator to scope the search.
            visible: If True, waits for the element to be visible (i.e., not hidden and has a
                non-zero size). If False (default), waits only for the element to be attached
                to the DOM.
            timeout: The maximum time to wait in seconds. Defaults to 5.
            exception: If True (default), raises NoSuchElementException on timeout.
                If False, returns None on timeout.
            ensure_page_safe: If True, waits for network activity to be idle before starting
                the element wait.

        Returns:
            A Locator for the found element, or None if the timeout is reached
            and `exception` is set to False.

        Raises:
            NoSuchElementException: If the timeout is reached and `exception` is True.
        """
        if ensure_page_safe:
            self.plugin.ensure_page_safe()

        root_element: Union[Page, Locator] = self.page
        if parent:
            root_element = self.element(parent)

        try:
            target_locator = root_element.locator(str(SmartLocator(locator)))
            state = "visible" if visible else "attached"
            target_locator.first.wait_for(state=state, timeout=timeout * 1000)
            return target_locator.first
        except PlaywrightError:
            if exception:
                raise NoSuchElementException(
                    f"Timed out waiting for element with {locator} in {parent}"
                ) from None
            return None

    # ==================== ELEMENT STATE & PROPERTY QUERIES ====================
    def is_displayed(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Check if the element represented by the locator is displayed (visible).

        Args:
            locator: Element locator to check visibility for
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            True if element is visible, False otherwise

        Raises:
            PlaywrightError: If the frame context is invalid (nonexistent iframe)
        """
        try:
            return self.element(locator, *args, **kwargs).is_visible()
        except NoSuchElementException:
            return False
        except (PlaywrightError, FrameNotFoundError) as e:
            # Re-raise frame-related errors to ensure consistent behavior across Playwright versions.
            if (
                isinstance(e, FrameNotFoundError)
                or "Frame not found" in str(e)
                or "Failed to find frame" in str(e)
            ):
                raise
            else:
                return False

    def is_enabled(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Check if the element represented by the locator is enabled.

        Args:
            locator: Element locator to check enabled state for
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            True if element is enabled, False otherwise
        """
        try:
            return self.element(locator, *args, **kwargs).is_enabled()
        except NoSuchElementException:
            return False

    def is_disabled(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Check if the element represented by the locator is disabled.

        Args:
            locator: Element locator to check disabled state for
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            True if element is disabled, False otherwise
        """
        try:
            return self.element(locator, *args, **kwargs).is_disabled()
        except NoSuchElementException:
            return False

    def is_hidden(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Check if the element represented by the locator is hidden.

        Args:
            locator: Element locator to check visibility for
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            True if element is hidden, False otherwise
        """
        try:
            return self.element(locator, *args, **kwargs).is_hidden()
        except NoSuchElementException:
            return False

    def is_editable(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Check if the element represented by the locator is editable.

        Args:
            locator: Element locator to check editable state for
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            True if element is editable, False otherwise
        """
        try:
            return self.element(locator, *args, **kwargs).is_editable()
        except NoSuchElementException:
            return False

    def is_checked(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Check if the element represented by the locator is checked (checkbox or radio input).

        Args:
            locator: Element locator to check checked state for
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            True if element is checked, False otherwise
        """
        try:
            return self.element(locator, *args, **kwargs).is_checked()
        except NoSuchElementException:
            return False

    def is_selected(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Checks if a checkbox or radio button is selected/checked.

        Args:
            locator: Element locator to check selection state for
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            True if element is selected/checked, False otherwise
        """
        if self.type(locator) in ["checkbox", "radio"]:
            return self.is_checked(locator, *args, **kwargs)
        else:
            return self.element(locator, *args, **kwargs).evaluate("el => el.selected")

    def text(self, locator: LocatorAlias, *args, **kwargs) -> str:
        """Returns the text inside the element, normalized.

        Args:
            locator: Element locator to get text from
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            Normalized text content of the element
        """
        text_content = self.element(locator, *args, **kwargs).text_content() or ""
        return normalize_space(text_content)

    def input_value(self, locator: LocatorAlias, *args, **kwargs) -> str:
        """Returns the input value inside the element, normalized.

        Args:
            locator: Element locator to get input value from
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            Normalized input value of the element
        """
        value = self.element(locator, *args, **kwargs).input_value() or ""
        return normalize_space(value)

    def tag(self, *args, **kwargs) -> str:
        """Returns the tag name of the element.

        Args:
            *args: Arguments passed to element() method
            **kwargs: Keyword arguments passed to element() method

        Returns:
            Tag name of the element in lowercase
        """
        return self.element(*args, **kwargs).evaluate("el => el.tagName.toLowerCase()")

    def type(self, *args, **kwargs) -> str:
        """Returns the type of the element.

        Args:
            *args: Arguments passed to element() method
            **kwargs: Keyword arguments passed to element() method

        Returns:
            Type attribute value of the element
        """
        return self.element(*args, **kwargs).evaluate("el=>el.type")

    def classes(self, locator: LocatorAlias, *args, **kwargs) -> Set[str]:
        """Return a set of classes attached to the element.

        Args:
            locator: Element locator to get classes from
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            Set of CSS class names attached to the element
        """
        class_string = self.get_attribute("class", locator, *args, **kwargs)
        return set(class_string.split()) if class_string else set()

    def attributes(self, locator: LocatorAlias, *args, **kwargs) -> Dict:
        """Return a dict of attributes attached to the element.

        This implementation uses Playwright's .evaluate() method to execute a
        self-contained JavaScript function directly on the element.

        Args: See :py:meth:`elements`

        Returns:
            A :py:class:`dict` of attributes and respective values.
        """
        el = self.element(locator, *args, **kwargs)

        js_function = """
            el => {
                const items = {};
                for (let i = 0; i < el.attributes.length; i++) {
                    items[el.attributes[i].name] = el.attributes[i].value;
                }
                return items;
            }
        """
        result = el.evaluate(js_function)
        self.logger.debug("css attributes for %r => %r", locator, result)
        return result

    def get_attribute(self, attr: str, *args, **kwargs) -> Optional[str]:
        """Returns the value of an element's attribute.

        Uses .input_value() for the 'value' attribute for better reliability.
        """
        el = self.element(*args, **kwargs)
        if attr == "value" and self.browser.tag(el) in ("input", "textarea", "select"):
            return el.input_value()
        return el.get_attribute(attr)

    def set_attribute(self, attr: str, value: str, *args, **kwargs) -> None:
        """Sets an attribute on an element to the given value.

        Args:
            attr: Attribute name to set
            value: Value to set for the attribute
            *args: Arguments passed to element() method
            **kwargs: Keyword arguments passed to element() method
        """
        js_function = "(el, {attr, value}) => el.setAttribute(attr, value)"

        self.element(*args, **kwargs).evaluate(
            js_function,
            {"attr": attr, "value": value},  # This is the object passed to the function
        )
        self.logger.debug("set attribute for %r => %r=%r", args, attr, value)

    # ================== ELEMENT GEOMETRY & VISUAL PROPERTIES ==================
    def size_of(self, *args, **kwargs) -> Size:
        """Returns element's size as a tuple of width/height.

        Args:
            *args: Arguments passed to element() method
            **kwargs: Keyword arguments passed to element() method

        Returns:
            Size object containing width and height
        """
        box = self.element(*args, **kwargs).bounding_box()
        return Size(box["width"], box["height"]) if box else Size(0, 0)

    def location_of(self, *args, **kwargs) -> Location:
        """Returns element's location as a tuple of x/y.

        Args:
            *args: Arguments passed to element() method
            **kwargs: Keyword arguments passed to element() method

        Returns:
            Location object containing x and y coordinates
        """
        box = self.element(*args, **kwargs).bounding_box()
        return Location(box["x"], box["y"]) if box else Location(0, 0)

    def middle_of(self, *args, **kwargs) -> Location:
        """Returns element's middle point as a tuple of x/y.

        Args:
            *args: Arguments passed to element() method
            **kwargs: Keyword arguments passed to element() method

        Returns:
            Location object containing center x and y coordinates
        """
        size = self.size_of(*args, **kwargs)
        location = self.location_of(*args, **kwargs)
        return Location(int(location.x + size.width / 2), int(location.y + size.height / 2))

    def highlight(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Highlight the corresponding element(s) on the screen.

        Args:
            locator: Element locator to highlight
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method
        """
        self.logger.debug("highlight: %r", locator)
        el = self.element(locator, *args, **kwargs)
        el.highlight()

    # ====================== MOUSE & POINTER INTERACTIONS ======================
    def click(
        self,
        locator: LocatorAlias,
        button: Optional[Literal["left", "middle", "right"]] = "left",
        click_count: Optional[int] = None,
        delay: Optional[float] = None,
        force: Optional[bool] = None,
        no_wait_after: Optional[bool] = None,
        timeout: Optional[float] = None,
        *args,
        **kwargs,
    ) -> None:
        """Click on an element specified by the locator.

        Args:
            locator: Element locator to click on
            button: Mouse button to click with ("left", "right", or "middle")
            click_count: defaults to 1
            delay: Time to wait between `mousedown` and `mouseup` in milliseconds. Defaults to 0.
            force: Whether to bypass the actionability checks
            no_wait_after: If True, don't wait for page events after click
            timeout: Maximum time in milliseconds. Defaults to `30000` (30 seconds). Pass `0` to disable timeout.

        Deprecated:
            ignore_ajax: Deprecated parameter. Use `no_wait_after=True` instead.
        """
        self.logger.debug("click: %r with %s button", locator, button)

        # Handle deprecated ignore_ajax parameter
        ignore_ajax = kwargs.pop("ignore_ajax", False)
        if ignore_ajax:
            warnings.warn(
                "The 'ignore_ajax' parameter is deprecated and will be removed in a future version. "
                "Use 'no_wait_after=True' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            no_wait_after = True

        el = self.element(locator, *args, **kwargs)
        self.plugin.before_click(el, locator)

        el.click(
            button=button,
            click_count=click_count,
            delay=delay,
            force=force,
            no_wait_after=no_wait_after,
            timeout=timeout,
        )
        if not ignore_ajax and not no_wait_after:
            try:
                self.plugin.ensure_page_safe()
            except TimedOutError:
                self.plugin.after_click_safe_timeout(el, locator)
        self.plugin.after_click(el, locator)

    def double_click(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Double-click on an element specified by the locator.

        Args:
            locator: Element locator to double-click on
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Deprecated:
            ignore_ajax: Deprecated parameter. Use `no_wait_after=True` instead.
        """
        self.logger.debug("double_click: %r", locator)

        # Handle deprecated ignore_ajax parameter
        ignore_ajax = kwargs.pop("ignore_ajax", False)
        if ignore_ajax:
            warnings.warn(
                "The 'ignore_ajax' parameter is deprecated and will be removed in a future version. "
                "Use 'no_wait_after=True' instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        no_wait_after = kwargs.pop("no_wait_after", False)

        el = self.element(locator, *args, **kwargs)
        self.plugin.before_click(el, locator)
        el.dblclick(no_wait_after=no_wait_after)

        if not ignore_ajax and not no_wait_after:
            try:
                self.plugin.ensure_page_safe()
            except TimedOutError:
                self.plugin.after_click_safe_timeout(el, locator)
        self.plugin.after_click(el, locator)

    def right_click(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Right-click (context click) on an element specified by the locator.

        Args:
            locator: Element locator to right-click on
            *args, **kwargs: Additional arguments passed to click method
        """
        kwargs["button"] = "right"
        self.click(locator, *args, **kwargs)

    def middle_click(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Middle-click on an element specified by the locator.

        Args:
            locator: Element locator to middle-click on
            *args, **kwargs: Additional arguments passed to click method
        """
        kwargs["button"] = "middle"
        self.click(locator, *args, **kwargs)

    def raw_click(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Alias for the standard click method in Playwright.

        Args:
            locator: Element locator to click on
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method
        """
        self.click(locator, *args, **kwargs)

    def perform_click(self) -> None:
        """No longer needed in Playwright. Kept for API compatibility.

        This method exists for backward compatibility but performs no action.
        """
        warnings.warn(
            message="perform_click is a no-op in Playwright. Use .click() on a widget or with browser.",
            category=DeprecationWarning,
        )
        self.logger.warning(
            "perform_click is a no-op in Playwright. Use .click() on a widget or with browser."
        )

    def perform_double_click(self) -> None:
        """No longer needed in Playwright. Kept for API compatibility.

        This method exists for backward compatibility but performs no action.
        """
        warnings.warn(
            message="perform_double_click is a no-op in Playwright. Use .double_click().",
            category=DeprecationWarning,
        )
        self.logger.warning("perform_double_click is a no-op in Playwright. Use .double_click().")

    def hover(self, locator: LocatorAlias, *args, **kwargs) -> Locator:
        """Hover over the matching element represented by the locator.

        Args:
            locator: Element locator to hover over
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            The target element's Locator object
        """
        self.logger.debug("hover: %r", locator)
        el = self.element(locator, *args, **kwargs)
        el.hover()
        return el

    def move_to_element(self, locator: LocatorAlias, *args, **kwargs) -> Locator:
        """Move mouse cursor to element with intelligent handling of special cases.

        This method includes smart workarounds for common UI testing challenges:
        - Automatically handles <option> elements by moving to parent <select>
        - Provides optional element highlighting for debugging
        - Handles elements that may be partially obscured or positioned unusually

        Args:
            locator: Element locator to move to
            highlight_element: If True, highlights the element after moving (via kwargs)

        Returns:
            The target element's Locator object
        """
        self.logger.debug("move_to_element: %r", locator)
        el = self.element(locator, *args, **kwargs)

        # Add this block to handle invisible <option> elements
        if self.tag(el) == "option":
            self.logger.debug("Locator is an <option>, moving to parent <select> instead.")
            # Playwright can't hover on options, so we find and hover on the parent select
            parent_select = self.element("..", parent=el)
            parent_select.hover()
            return el  # Return the original option locator

        el.hover()

        if kwargs.get("highlight_element", False):
            self.browser.highlight(el)
        return el

    def move_by_offset(self, origin: LocatorAlias, x: int, y: int) -> None:
        """Moves the mouse to the center of an origin element and then moves by a given offset.

        This is the recommended stateless approach for precise mouse control, like for
        hovering over different parts of a graph to trigger tooltips.

        Args:
            origin: The widget or locator to use as the starting point for the move.
            x: The horizontal offset in pixels from the center of the origin element.
            y: The vertical offset in pixels from the center of the origin element.
        """
        self.logger.debug("move_by_offset X:%r Y:%r from origin %r", x, y, origin)

        # Find the origin element and its center point
        origin_el = self.element(origin)
        box = origin_el.bounding_box()
        if not box:
            raise WidgetOperationFailed(f"Could not get bounding box for origin element {origin}")

        start_x = box["x"] + box["width"] / 2
        start_y = box["y"] + box["height"] / 2

        # Calculate the final absolute coordinates
        new_x = start_x + x
        new_y = start_y + y

        # Perform the move
        self.page.mouse.move(new_x, new_y)

    # ========================= KEYBOARD & FORM INPUT =========================
    def send_keys(self, text: str, locator: LocatorAlias, sensitive=False, *args, **kwargs) -> None:
        """Send keys to element with intelligent input type detection and handling.

        This method provides smart form input handling that automatically detects the input
        type and applies the appropriate interaction strategy. It solves common testing
        issues around file uploads, special key sequences, and element state management.

        Key Features:
        - Automatic file upload detection
        - Keyboard event simulation
        - Element positioning
        - Sensitive data protection

        Usage Examples:

        .. code-block:: python

            # Regular text input
            browser.send_keys("john.doe@example.com", "#email")

            # File upload (automatically detected)
            browser.send_keys("/path/to/document.pdf", "input[type='file']")

            # Sensitive data (masked in logs)
            browser.send_keys("secret_password", "#password", sensitive=True)

            # Special key sequences
            browser.send_keys("Hello World", "#text-field")

        Args:
            text: Text to type or file path for file inputs
            locator: Element locator to send keys to
            sensitive: If True, masks the text in logs for security
            *args, **kwargs: Additional arguments passed to element finding

        Note:
            For file inputs, provide the full file path. The method automatically
            detects file input fields and handles them appropriately.
        """
        text = str(text) or ""
        el = self.move_to_element(locator, *args, **kwargs)

        # Preserve the logic to detect file inputs
        is_file_input = self.tag(el) == "input" and self.get_attribute("type", el) == "file"

        self.plugin.before_keyboard_input(el, text)
        self.logger.debug("send_keys %r to %r", "*" * len(text) if sensitive else text, locator)

        if is_file_input:
            el.set_input_files(text)
        else:
            # Use .type() to simulate actual keystrokes for other inputs
            el.type(text)

        if "Enter" not in text:
            try:
                self.plugin.after_keyboard_input(el, text)
            except PlaywrightError as e:
                # Catch potential errors if the element detaches after typing
                if "is not a valid selector" in str(e):
                    self.logger.warning(
                        "Element detached after send_keys, skipping after_keyboard_input hook."
                    )
                    pass
                else:
                    raise
        else:
            self.logger.info(
                "skipped the after_keyboard_input call due to %r containing ENTER.",
                text,
            )

    def fill(self, text: str, locator: LocatorAlias, sensitive=False, *args, **kwargs) -> None:
        """Fill text into an element.

        Args:
            text: Text or file path to be inserted into the element
            locator: Element locator to fill text into
            sensitive: If True, masks the text in logs for security
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method
        """
        text = str(text) or ""
        el = self.element(locator, *args, **kwargs)
        self.logger.debug("fill %r to %r", "*" * len(text) if sensitive else text, locator)
        el.fill(text)

    def clear(self, locator: LocatorAlias, *args, **kwargs) -> bool:
        """Clears a text input with given locator.

        Args:
            locator: Element locator to clear text from
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method

        Returns:
            True if clearing was successful
        """
        self.logger.debug("clear: %r", locator)
        el = self.element(locator, *args, **kwargs)
        self.plugin.before_keyboard_input(el, None)
        el.clear()
        self.plugin.after_keyboard_input(el, None)
        return (el.input_value() or "") == ""

    def send_keys_to_focused_element(self, *keys: str) -> None:
        """Sends keys to the current focused element.

        Args:
            *keys: Key sequences to send to the focused element
        """
        text = "".join(keys)
        if len(text) == 1 and text in ["Enter", "Escape", "Tab", "Space"]:
            # Handle special single keys
            self.page.keyboard.press(text)
        else:
            # Handle regular text
            self.page.keyboard.type(text)

    def copy(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Select all and copy to clipboard.

        Args:
            locator: Element locator to copy content from
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method
        """
        self.logger.debug("copy: %r", locator)
        el = self.element(locator, *args, **kwargs)
        el.focus()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Control+C")

    def paste(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Paste from clipboard to current element.

        Args:
            locator: Element locator to paste content into
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method
        """
        self.logger.debug("paste: %r", locator)
        el = self.element(locator, *args, **kwargs)
        el.focus()
        self.page.keyboard.press("Control+V")

    # ======================== CHECKBOX & FORM CONTROLS ========================
    def check(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Check an element (Checkboxes/ Radio buttons) specified by the locator.

        Args:
            locator: Element locator for checkbox/radio button to check
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method
        """
        self.logger.debug("check: %r", locator)
        el = self.element(locator, *args, **kwargs)
        el.check()

    def uncheck(self, locator: LocatorAlias, *args, **kwargs) -> None:
        """Uncheck an element (Checkboxes/ Radio buttons) specified by the locator.

        Args:
            locator: Element locator for checkbox/radio button to uncheck
            *args: Additional arguments passed to element() method
            **kwargs: Additional keyword arguments passed to element() method
        """
        self.logger.debug("uncheck: %r", locator)
        el = self.element(locator, *args, **kwargs)
        el.uncheck()

    # ========================= DRAG & DROP OPERATIONS =========================
    def drag_and_drop(self, source: LocatorAlias, target: LocatorAlias) -> None:
        """Drags the source element and drops it into target.

        Args:
            source: Element locator to drag from
            target: Element locator to drop to
        """
        self.logger.debug("drag_and_drop %r to %r", source, target)
        self.element(source).drag_to(self.element(target))

    def drag_and_drop_by_offset(self, source: LocatorAlias, by_x: int, by_y: int) -> None:
        """Drags the source element and drops it by a given offset.

        Args:
            source: Element locator to drag from
            by_x: Horizontal offset in pixels to drag by
            by_y: Vertical offset in pixels to drag by

        Note:
            Playwright's primary drag/drop is element-to-element. This implementation
            simulates the offset drag.
        """
        self.logger.debug("drag_and_drop_by_offset %r X:%r Y:%r", source, by_x, by_y)
        source_el = self.element(source)
        source_box = source_el.bounding_box()
        if source_box:
            self.page.mouse.move(
                source_box["x"] + source_box["width"] / 2,
                source_box["y"] + source_box["height"] / 2,
            )
            self.page.mouse.down()
            self.page.mouse.move(
                source_box["x"] + source_box["width"] / 2 + by_x,
                source_box["y"] + source_box["height"] / 2 + by_y,
            )
            self.page.mouse.up()

    def drag_and_drop_to(
        self,
        source: LocatorAlias,
        to_x: Optional[int] = None,
        to_y: Optional[int] = None,
    ) -> None:
        """Drags an element to a target location specified by ``to_x`` and ``to_y``.

        Args:
            source: Element locator to drag from
            to_x: Target X coordinate (uses current X if None)
            to_y: Target Y coordinate (uses current Y if None)

        Raises:
            TypeError: If both to_x and to_y are None
        """
        self.logger.debug("drag_and_drop_to %r X:%r Y:%r", source, to_x, to_y)
        if to_x is None and to_y is None:
            raise TypeError("You need to pass either to_x or to_y or both")
        middle = self.middle_of(source)
        self.drag_and_drop_by_offset(
            source, (to_x or middle.x) - middle.x, (to_y or middle.y) - middle.y
        )

    # ========================= JAVASCRIPT EXECUTION =========================
    def execute_script(self, script: str, *args, silent=False, **kwargs) -> Any:
        """Executes a Selenium-style script in a Playwright context.

        This method acts as a compatibility layer. It takes a script written for Selenium
        (which uses the special 'arguments' object) and wraps it in a function that
        Playwright can execute correctly. Widgets are automatically resolved to the
        necessary ElementHandles for use in the script.

        Args:
            script: The JavaScript string to execute.
            *args: Arguments to be passed to the script, accessible via `arguments[i]`.
            silent: If True, suppress debug logging for this call.

        Returns:
            Result of the JavaScript execution
        """
        if not silent:
            self.logger.debug("execute_script: %r", script)
        from .widget.base import Widget

        # Process arguments: Widgets/Locators must be resolved to ElementHandles for Playwright's evaluate method.
        processed_args = []
        for arg in args:
            if isinstance(arg, (Widget, Locator)):
                # .element_handle() is required to pass a node into the page context
                processed_args.append(self.element(arg).element_handle())
            else:
                processed_args.append(arg)

        # Create a JS function that wraps the original script. It takes a single array of our processed arguments.
        js_wrapper_function = f"""
            (args) => {{
                const arguments = args;
                {dedent(script)}
            }}
        """
        return self.page.evaluate(js_wrapper_function, processed_args)

    # =================== FRAME & WINDOW CONTEXT MANAGEMENT ===================
    def switch_to_frame(self, locator: LocatorAlias) -> None:
        """Switch browser context to the specified iframe.

        Changes the active context for element operations to work within the iframe.
        All subsequent element operations will be scoped to this frame until
        switch_to_main_frame() is called.

        Args:
            locator: Locator for the iframe element to switch to
        """
        self.logger.debug("Switching to frame with locator: %r", locator)
        self.active_context = self.active_context.frame_locator(str(SmartLocator(locator)))

    def switch_to_main_frame(self) -> None:
        """Switch browser context back to the main page (exit iframe context).

        Resets the active context to the main page, exiting any iframe context.
        """
        self.logger.debug("Switching back to main frame")
        self.active_context = self.page

    def get_current_location(self) -> str:
        """Returns the URL of the current page or frame.

        Returns:
            Current page or frame URL as a string
        """
        return self.execute_script("return self.location.toString()")

    # ====================== ALERT HANDLING (TODO/FUTURE) ======================
    # TODO: Implement alert handling
    # def get_alert(self) -> Alert:
    #     """Returns the last detected alert object."""
    #     if not self.alert_present:
    #         raise NoAlertPresentException("No alert is currently present.")
    #     return self._last_alert
    #
    # @property
    # def alert_present(self) -> bool:
    #     """Checks whether there is any unhandled alert present."""
    #     return self._last_alert is not None
    #
    # def dismiss_any_alerts(self) -> None:
    #     """Loops and dismisses any unhandled alerts."""
    #     if self.alert_present:
    #         alert = self.get_alert()
    #         self.logger.info("dismissing alert: %r", alert.message)
    #         alert.dismiss()
    #         self._last_alert = None
    #
    # def handle_alert(
    #         self,
    #         cancel: bool = False,
    #         wait: Union[float, None] = 5.0,
    #         squash: bool = False,
    #         prompt: Optional[str] = None,
    #         check_present: bool = False,
    # ) -> Optional[bool]:
    #     """Handles an alert popup by waiting for the dialog event."""
    #     try:
    #         if not self.alert_present and wait:
    #             self.page.wait_for_event("dialog", timeout=(wait * 1000))
    #
    #         popup = self.get_alert()
    #         self.logger.info("handling alert: %r", popup.message)
    #         if prompt is not None:
    #             self.logger.info("  answering prompt: %r", prompt)
    #
    #         if cancel:
    #             self.logger.info("  dismissing")
    #             popup.dismiss()
    #         else:
    #             self.logger.info("  accepting")
    #             popup.accept(prompt_text=prompt)
    #
    #         self._last_alert = None  # Consume the alert
    #         return True
    #     except (PlaywrightError, NoAlertPresentException):
    #         if not check_present:
    #             return None
    #         if squash:
    #             return False
    #         raise


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
    ) -> List[Locator]:
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


class WindowManager:
    """Multi-page/window manager for Playwright-based browser automation.

    WindowManager provides comprehensive management of multiple browser tabs, windows, and popups
    within a single Playwright browser context. It automatically wraps each page with widgetastic
    Browser instances and provides seamless switching between them, making multi-window testing
    scenarios much more manageable.

    Args:
        context: Playwright BrowserContext instance for managing pages
        initial_page: The first Page to wrap and manage
        browser_class: Browser class to use for wrapping pages (defaults to Browser)
        **browser_kwargs: Additional arguments passed to Browser constructor

    Key Features:

    - Automatic Page Wrapping:
    Every Playwright Page is automatically wrapped with a widgetastic Browser instance, providing
    the full widgetastic API for each tab/window. This eliminates the need to manually create
    Browser instances for new pages.

    - Popup Detection and Management:
    Automatically detects when new pages are opened (via popups, target="_blank" links, etc.)
    and immediately wraps them with Browser instances. No manual intervention required for
    popup handling.

    - Intelligent Page Cleanup:
    Automatically removes closed pages from the managed collection and cleans up associated
    Browser instances to prevent memory leaks during long-running test sessions.

    - Current Page Tracking:
    Maintains a reference to the currently active Browser instance, making it easy to work
    with the "focused" window while keeping track of all available windows.

    - Seamless Context Switching:
    Provides simple methods to switch between different pages/windows and automatically
    brings the target page to the front for user visibility during debugging.

    Practical Usage Examples:

    .. code-block:: python

        # Initialize with a browser context and initial page
        window_manager = WindowManager(context, initial_page)

        # Work with the current page
        window_manager.current.element("#login-button").click()

        # Open a new tab and switch to it
        new_browser = window_manager.new_browser("https://example.com", focus=True)
        new_browser.element("#search-box").fill("test query")

        # Handle popup windows automatically
        window_manager.current.click("a[target='_blank']")  # Opens popup
        # WindowManager automatically detects and wraps the popup

        # List all open windows
        all_browsers = window_manager.all_browsers
        print(f"Managing {len(all_browsers)} windows")

        # Switch to a specific window
        window_manager.switch_to(all_browsers[1])

        # Close current window (automatically switches to next available)
        window_manager.close_browser()

        # Close specific window
        window_manager.close_browser(all_browsers[0])


    Example Integration:
        .. code-block:: python

            @pytest.fixture(scope="session")
            def window_manager(playwright_context, initial_page):
                return WindowManager(playwright_context, initial_page)

            def test_multi_window_workflow(window_manager):
                # Test flows across multiple windows
                main_browser = window_manager.current
                popup_browser = window_manager.new_browser("https://popup.com")

                # Test interactions between windows
                main_browser.element("#trigger-popup").click()
                popup_browser.element("#confirm").click()

                # Verify results in main window
                window_manager.switch_to(main_browser)
                assert main_browser.element("#result").text == "Success"
    """

    def __init__(
        self, context: BrowserContext, initial_page: Page, browser_class=Browser, **browser_kwargs
    ):
        self._context = context
        self._browser_class = browser_class
        self._browser_kwargs = browser_kwargs
        self._browsers: Dict[Page, Browser] = {}

        self.current: Browser = self._wrap_page(initial_page)
        self._context.on("page", self._on_new_page)

    def _wrap_page(self, page: Page) -> Browser:
        if page not in self._browsers:
            self._browsers[page] = self._browser_class(page, **self._browser_kwargs)
        return self._browsers[page]

    def _on_new_page(self, page: Page):
        """Handle new page/popup detection and wrapping.

        Args:
            page: The new Playwright Page instance to be wrapped
        """
        self.current.logger.info("New page opened / popup detected: %s", page.url)
        self._wrap_page(page)

    @property
    def all_browsers(self) -> List[Browser]:
        """Get all managed Browser instances with automatic cleanup.

        Returns a list of all currently active widgetastic Browser instances. This property
        automatically performs cleanup by removing any Browser instances associated with
        closed pages, ensuring the returned list only contains valid, active browsers.


        Example:
            .. code-block:: python

                # Get all active browsers
                browsers = window_manager.all_browsers
                print(f"Currently managing {len(browsers)} windows")

                # Iterate through all browsers
                for i, browser in enumerate(browsers):
                    print(f"Window {i}: {browser.title} - {browser.url}")
        """
        current_pages = self._context.pages
        # Clean up browsers for pages that are no longer in the context or are closed
        for page in list(self._browsers.keys()):
            try:
                # Check if page is still in context and not closed
                if page not in current_pages or page.is_closed():
                    del self._browsers[page]
            except Exception:
                # If we can't check the page state, assume it's closed and remove it
                if page in self._browsers:
                    del self._browsers[page]

        # Ensure all current pages are wrapped
        for page in current_pages:
            if not page.is_closed():
                self._wrap_page(page)

        return list(self._browsers.values())

    @property
    def all_pages(self) -> List[Page]:
        """Get all active Playwright Page objects from the browser context.

        Returns the raw Playwright Page instances managed by the browser context.
        Unlike all_browsers, this property returns the underlying Page objects
        without any widgetastic wrapping or cleanup logic.

        Example:
            .. code-block:: python

                # Get raw Playwright pages
                pages = window_manager.all_pages

                # Access Playwright-specific methods
                for page in pages:
                    print(f"Page URL: {page.url}")
                    print(f"Page title: {page.title()}")
        """
        return self._context.pages

    def new_browser(self, url: str, focus: bool = True) -> Browser:
        """Create a new browser tab/window and navigate to the specified URL.

        Opens a new page in the current browser context, navigates to the provided URL,
        wraps it with a widgetastic Browser instance, and optionally switches focus to it.
        This is the primary method for opening new tabs during testing.

        Args:
            url: URL to navigate to in the new page
            focus: If True, switches to the new page immediately (default: True)

        Returns:
            New Browser instance wrapping the created page

        Example:
            .. code-block:: python

                # Open new tab and switch to it
                new_browser = window_manager.new_browser("https://example.com")
                new_browser.element("#search").fill("test query")

                # Open new tab without switching focus
                background_browser = window_manager.new_browser(
                    "https://api.example.com",
                    focus=False
                )

                # Continue working with current tab while background loads
                window_manager.current.element("#submit").click()

                # Switch to background tab when ready
                window_manager.switch_to(background_browser)
        """
        self.current.logger.info("Opening URL in new page: %r", url)
        page = self._context.new_page()
        page.goto(url)
        new_browser_instance = self._wrap_page(page)
        if focus:
            self.switch_to(new_browser_instance)
        return new_browser_instance

    def switch_to(self, browser_or_page: Union[Browser, Page]):
        """Switch focus to a different browser tab/window.

        Changes the currently active browser to the specified Browser or Page instance.
        The target page is brought to the front for visibility and becomes the new
        current browser for subsequent operations.

        Args:
            browser_or_page: Browser instance or Playwright Page to switch to

        Raises:
            NoSuchElementException: If the specified page doesn't exist in the context

        Example:
            .. code-block:: python

                # Switch using Browser instance
                all_browsers = window_manager.all_browsers
                window_manager.switch_to(all_browsers[1])

                # Switch using Playwright Page
                all_pages = window_manager.all_pages
                window_manager.switch_to(all_pages[0])

                # Verify the switch
                print(f"Now on: {window_manager.current.title}")
        """
        target_page = (
            browser_or_page.page if isinstance(browser_or_page, Browser) else browser_or_page
        )

        if target_page not in self.all_pages:
            raise NoSuchElementException("The specified Page handle does not exist.")

        target_page.bring_to_front()
        self.current = self._browsers[target_page]

    def close_browser(self, browser_or_page: Optional[Union[Browser, Page]] = None):
        """Close a browser tab/window with automatic cleanup and focus management.

        Closes the specified browser tab/window or the current one if none specified.
        Automatically cleans up the associated Browser instance and switches focus
        to another available page if the current page was closed.

        Args:
            browser_or_page: Browser or Page instance to close. If None, closes current page.

        Behavior:
            - Removes the Browser instance from the managed collection
            - Closes the underlying Playwright Page
            - If the closed page was current, switches to the first available page
            - If no pages remain, the WindowManager becomes inactive

        Example:
            .. code-block:: python

                # Close current tab
                window_manager.close_browser()

                # Close specific tab
                browsers = window_manager.all_browsers
                window_manager.close_browser(browsers[1])

                # Close using Page reference
                pages = window_manager.all_pages
                window_manager.close_browser(pages[0])

                # Check remaining browsers
                remaining = len(window_manager.all_browsers)
                print(f"{remaining} tabs still open")
        """
        target_browser = browser_or_page or self.current
        target_page = target_browser.page if isinstance(target_browser, Browser) else target_browser

        # Check if page is already closed
        try:
            is_closed = target_page.is_closed()
        except Exception:
            is_closed = True

        if not is_closed:
            try:
                self.current.logger.debug("Closing page: %r", target_page.url)
            except Exception:
                self.current.logger.debug("Closing page (URL unavailable)")

        # Remove from internal tracking
        if target_page in self._browsers:
            del self._browsers[target_page]

        # Close the page if not already closed
        if not is_closed:
            try:
                target_page.close()
            except Exception:
                pass  # Page might already be closed

        # Switch focus if there are remaining pages
        remaining_pages = self.all_pages
        if remaining_pages:
            try:
                self.switch_to(remaining_pages[0])
            except Exception:
                # If switching fails, try to find a valid page
                for page in remaining_pages:
                    try:
                        if not page.is_closed():
                            self.switch_to(page)
                            break
                    except Exception:
                        continue

    def close_extra_pages(self, current=False):
        """Cleanup all extra pages other than current page.

        Args:
            current: Close current page as well. Default current page will not close
        """
        pages = list(self.all_pages)

        if current:
            pages_to_delete = pages
        else:
            current_page = self.current.page if hasattr(self, "current") and self.current else None
            pages_to_delete = [p for p in pages if p != current_page]

        for p in pages_to_delete:
            try:
                if not p.is_closed():
                    p.close()
            except Exception:
                pass
