"""
SmartLocator - Intelligent Locator Resolution for Widgetastic.core
==================================================================

Overview
--------
The SmartLocator class provides intelligent locator resolution and Playwright compatibility.
It automatically detects and converts various locator formats into a standardized (by, locator)
representation while providing Playwright-compatible string output.

Why SmartLocator is Essential
-----------------------------
SmartLocator addresses several key requirements for modern web automation:

1. **Intelligent Detection**: Users can write locators naturally without specifying the strategy
   - "#myid" is automatically detected as CSS
   - "//div" is automatically detected as XPath
   - "text=Click Me" is detected as text locator

2. **Multiple Input Formats**: Support various ways users might specify locators
   - String: SmartLocator("//div")
   - Tuple: SmartLocator("xpath", "//div")
   - Dict: SmartLocator({"xpath": "//div"}) or SmartLocator({"by": "xpath", "locator": "//div"})
   - Kwargs: SmartLocator(xpath="//div")

3. **Playwright Integration**: Direct compatibility with Playwright's locator format requirements
   - Automatic string formatting for different locator types
   - CSS: "#id" → "#id"
   - XPath: "//div" → "xpath=//div"
   - Text: "Click" → 'text="Click"'

4. **Widget Integration**: Seamless integration with widgetastic widgets via __locator__ protocol

Quick Start Examples
--------------------
```python
# Basic usage - let SmartLocator detect the strategy
loc = SmartLocator("#submit-btn")  # CSS selector
loc = SmartLocator("//button")     # XPath
loc = SmartLocator(text="Click Me") # Text locator

# Use with Playwright
str(loc)  # Returns Playwright-compatible string

# Widget integration
class MyButton:
    def __locator__(self):
        return {"text": "Submit"}

button_loc = SmartLocator(MyButton())
```

Supported Locator Types
------------------------
- CSS selectors: "#id", ".class", "tag#id.class"
- XPath expressions: "//div", "./span", "(//a)[1]"
- Text locators: text="Click Me"
- ID locators: id="my-id"
- Role locators: role="button"
- Data-testid: data-testid="test-element"
- Placeholder, title, name attributes
"""

import re
from collections import namedtuple
from typing import Any
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Type


class LocatorStrategy:
    """Abstract base class for all locator resolution strategies."""

    locator_class: "Type[SmartLocator]"  # This will be injected to avoid circular imports

    def create_locator(self, value: Any) -> Optional[Tuple[str, str]]:
        """
        Tries to create a (by, locator) tuple from the given value.
        Returns the tuple if successful, otherwise None.
        """
        raise NotImplementedError


class CSSStrategy(LocatorStrategy):
    """Handles simple CSS selectors like 'tag#id.class'."""

    CSS_SELECTOR_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9-]*)?(?:[#.][a-zA-Z0-9_-]+)+$")

    def create_locator(self, value: Any) -> Optional[Tuple[str, str]]:
        if isinstance(value, str) and self.CSS_SELECTOR_RE.match(value):
            return "css", value
        return None


class XPathStrategy(LocatorStrategy):
    """Handles simple XPath expressions."""

    def create_locator(self, value: Any) -> Optional[Tuple[str, str]]:
        if isinstance(value, str) and value.strip().startswith(("/", "(", ".")):
            return "xpath", value
        return None


class KwargsStrategy(LocatorStrategy):
    """Handles keyword arguments like SmartLocator(text='Login')."""

    SUPPORTED_ENGINES = {
        "text",
        "id",
        "data-testid",
        "role",
        "placeholder",
        "title",
        "name",
        "xpath",
        "css",
    }

    def create_locator(self, value: Any) -> Optional[Tuple[str, str]]:
        if isinstance(value, dict):
            if "by" in value and "locator" in value:
                engine, locator_value = value["by"], value["locator"]
            elif len(value) == 1:
                engine, locator_value = next(iter(value.items()))
            else:
                return None

            if engine in self.SUPPORTED_ENGINES:
                return engine, locator_value
        return None


class LocatorObjectStrategy(LocatorStrategy):
    """Handles cases where a locatable object is passed in."""

    def create_locator(self, value: Any) -> Optional[Tuple[str, str]]:
        if isinstance(value, self.locator_class):
            return value.by, value.locator
        if hasattr(value, "__locator__"):
            recursive_locator = self.locator_class(value.__locator__())
            return recursive_locator.by, recursive_locator.locator
        return None


class SmartLocator(namedtuple("SmartLocator", ["by", "locator"])):
    """
    Intelligently resolves various inputs into a locator with 'by' and 'locator' attributes,
    while providing a Playwright-compatible string representation.

    This class uses a strategy pattern to automatically detect the locator type and convert
    it to the appropriate format for Playwright.

    Attributes:
        by (str): The locator strategy (e.g., "css", "xpath", "text", "id", "role")
        locator (str): The locator value (e.g., "#myid", "//div", "Click Me")

    Usage Examples:
        >>> # String auto-detection
        >>> SmartLocator("#submit")          # CSS selector
        >>> SmartLocator("//button")         # XPath
        >>> SmartLocator("plain-text")       # Falls back to CSS

        >>> # Explicit tuple format
        >>> SmartLocator("xpath", "//div[@class='content']")
        >>> SmartLocator("text", "Click Here")

        >>> # Dictionary formats
        >>> SmartLocator({"xpath": "//div"})
        >>> SmartLocator({"by": "css", "locator": "#login"})

        >>> # Keyword arguments
        >>> SmartLocator(id="username")
        >>> SmartLocator(text="Submit")
        >>> SmartLocator(role="button")

        >>> # Widget integration
        >>> class LoginButton:
        ...     def __locator__(self):
        ...         return {"text": "Login"}
        >>> SmartLocator(LoginButton())

    Playwright String Output:
        >>> str(SmartLocator("#button"))     # "#button"
        >>> str(SmartLocator("//div"))       # "xpath=//div"
        >>> str(SmartLocator(text="Click"))  # 'text="Click"'

    Strategy Resolution Order:
        1. LocatorObjectStrategy - Handles SmartLocator instances and __locator__ protocol
        2. CSSStrategy - Detects CSS selectors using regex pattern matching
        3. XPathStrategy - Detects XPath expressions by starting patterns
        4. KwargsStrategy - Handles dictionary and keyword argument formats

    CSS Detection Patterns:
        - ID selectors: #myid, div#myid
        - Class selectors: .myclass, div.myclass
        - Combined: div#id.class1.class2
        - Regex: ^(?:[a-zA-Z][a-zA-Z0-9-]*)?(?:[#.][a-zA-Z0-9_-]+)+$
        - Complex selectors fall back to CSS: div > span, input[type="text"]

    XPath Detection Patterns:
        - // (descendant): //div, //button[@type='submit']
        - / (document root): /html/body/div
        - ./ (current context): ./div, ./span[@class='active']
        - .// (descendant from current): .//input
        - ( (expressions): (//a)[1], (//div[contains(@class, 'active')])[2]

    Best Practices:
        - Use simple strings when possible: SmartLocator("#myid")
        - Choose stable strategies: id > text > xpath > css classes
        - Implement __locator__ in custom widgets
        - Use explicit formats for dynamic locators

    """

    STRATEGIES = [
        LocatorObjectStrategy(),
        CSSStrategy(),
        XPathStrategy(),
        KwargsStrategy(),
    ]

    def __new__(cls, *args: Any, **kwargs: Any):
        by: Optional[str] = None
        locator: Optional[str] = None

        if args and len(args) == 2 and not kwargs:
            # Handle tuple-style: SmartLocator("xpath", "//h1")
            value = {"by": args[0], "locator": args[1]}
        elif args and len(args) == 1 and not kwargs:
            # Handle single argument: SmartLocator("#foo") or SmartLocator(some_object)
            value = args[0]
        elif kwargs and not args:
            # Handle keyword arguments: SmartLocator(xpath="//h1")
            value = kwargs
        else:
            raise TypeError("Provide a single value, a (by, locator) tuple, or keyword arguments.")

        for strategy in cls.STRATEGIES:
            strategy.locator_class = cls
            result = strategy.create_locator(value)
            if result:
                by, locator = result
                break

        if not by:
            if isinstance(value, str):
                by = "css"
                locator = value
            elif isinstance(value, dict) and "by" in value and "locator" in value:
                # Handle unsupported strategies explicitly
                raise ValueError(f"Unsupported locator strategy: '{value['by']}'")
            else:
                raise TypeError(f"Could not resolve '{value}' into a valid locator.")

        return super().__new__(cls, by, locator)

    def __str__(self):
        """
        Produces Playwright-compatible locator string.

        Returns:
            str: Formatted locator string for Playwright

        Examples:
            >>> str(SmartLocator(css="#foo"))        # "#foo"
            >>> str(SmartLocator(xpath="//div"))     # "xpath=//div"
            >>> str(SmartLocator(text="Click"))      # 'text="Click"'
            >>> str(SmartLocator(id="myid"))         # 'id="myid"'
        """
        if self.by == "css":
            return self.locator
        if self.by in ["text", "id", "data-testid", "role", "placeholder", "title", "name"]:
            return f'{self.by}="{self.locator}"'
        else:  # xpath
            return f"{self.by}={self.locator}"

    def __repr__(self):
        """
        Developer-friendly string representation.

        Returns:
            str: Detailed representation showing by and locator values
        """
        return f'SmartLocator(by="{self.by}", locator="{self.locator}")'

    def __locator__(self):
        """
        Allows SmartLocator to be passed to another SmartLocator.

        This implements the widget locator protocol, enabling SmartLocator
        instances to be used anywhere a locatable object is expected.

        Returns:
            SmartLocator: Self-reference for protocol compatibility
        """
        return self
