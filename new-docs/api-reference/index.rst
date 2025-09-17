==============
API Reference
==============

Complete API documentation for widgetastic.core. This reference provides detailed information about every class,
method, and function in the library.

.. note::
   **Navigation Tip**: Use the search function (Ctrl+F / Cmd+F) to quickly find specific APIs.
   All methods include usage examples and parameter descriptions.

Core Components
===============

**🌐 Browser**
  The enhanced Playwright wrapper providing intelligent web automation

  * Page management and navigation
  * Element location and interaction
  * Network monitoring and safety checks
  * Frame context management

**🎯 Widgets**
  UI component abstractions with consistent interfaces

  * Basic widgets (Text, TextInput, Button)
  * Form widgets (Select, Checkbox, FileInput)
  * Complex widgets (Table, Image)
  * Widget lifecycle and caching

**📋 Views**
  Page and section organization with hierarchical structure

  * View creation and nesting
  * Parametrized and conditional views
  * Fill strategies and data operations
  * Context management

**📍 Locators**
  Smart element location with automatic format detection

  * SmartLocator system
  * CSS, XPath, and text locators
  * Dynamic locator generation
  * Playwright compatibility

Quick Reference
===============

**Most Used Classes**

.. code-block:: python

    from widgetastic.browser import Browser
    from widgetastic.widget import View, Widget
    from widgetastic.widget import Text, TextInput, Button, Select, Checkbox
    from widgetastic.locator import SmartLocator
    from widgetastic.utils import VersionPick, ParametrizedString

**Essential Methods**

.. code-block:: python

    # Browser operations
    browser.element(locator)          # Find single element
    browser.elements(locator)         # Find multiple elements
    browser.click(locator)           # Click element
    browser.text(locator)            # Get text content
    browser.fill(text, locator)      # Fill input field

    # Widget operations
    widget.read()                    # Get widget value
    widget.fill(value)              # Set widget value
    widget.is_displayed             # Check visibility
    widget.wait_displayed()         # Wait for element

    # View operations
    view.read()                     # Read all widgets
    view.fill(data_dict)           # Fill multiple widgets
    view.widget_names              # Get widget list

**Common Exceptions**

.. code-block:: python

    from widgetastic.exceptions import (
        NoSuchElementException,      # Element not found
        WidgetOperationFailed,       # Widget operation failed
        DoNotReadThisWidget,         # Skip widget in read()
        FrameNotFoundError          # Frame context error
    )

API Organization
================

.. note::
   **Complete API Documentation Coming Soon**

   Detailed API reference documentation for each module will be added in the next update.
   For now, you can explore the source code directly or use the tutorials and examples above
   to understand the API patterns.

Inheritance Hierarchy
=====================

**Core Classes**

.. code-block:: text

    Browser
    ├── Enhanced Playwright Page wrapper
    ├── Smart element location
    └── Network activity monitoring

    Widget (metaclass: WidgetMetaclass)
    ├── View
    │   ├── ParametrizedView
    │   └── ConditionalSwitchableView
    ├── GenericLocatorWidget
    │   ├── Text
    │   ├── Image
    │   └── Button (via ClickableMixin)
    ├── BaseInput
    │   ├── TextInput
    │   ├── FileInput
    │   └── ColourInput
    ├── Select (with ClickableMixin)
    ├── Checkbox (BaseInput + ClickableMixin)
    └── Table
        ├── TableRow
        └── TableColumn

**Mixin Classes**

.. code-block:: text

    ClickableMixin
    ├── Provides click() method
    └── Used by Button, Select, Checkbox, etc.

    Widgetable
    ├── Base for all widget-like objects
    ├── Sequential ID assignment
    └── Child item discovery

**OUIA Classes**

.. code-block:: text

    OUIABase
    ├── OUIAGenericView
    └── OUIAGenericWidget
        ├── ouia.Text
        ├── ouia.TextInput
        └── ouia.Checkbox

Method Categories
=================

**Element Location**

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Method
     - Description
     - Returns
   * - ``browser.element(locator)``
     - Find single element
     - ``Locator``
   * - ``browser.elements(locator)``
     - Find multiple elements
     - ``List[Locator]``
   * - ``browser.wait_for_element(locator)``
     - Wait for element to appear
     - ``Optional[Locator]``

**Element Interaction**

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Method
     - Description
     - Returns
   * - ``browser.click(locator)``
     - Click element
     - ``None``
   * - ``browser.send_keys(text, locator)``
     - Type text into element
     - ``None``
   * - ``browser.clear(locator)``
     - Clear input field
     - ``bool``

**Element Properties**

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Method
     - Description
     - Returns
   * - ``browser.text(locator)``
     - Get text content
     - ``str``
   * - ``browser.get_attribute(attr, locator)``
     - Get attribute value
     - ``Optional[str]``
   * - ``browser.is_displayed(locator)``
     - Check if visible
     - ``bool``

**Form Operations**

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Method
     - Description
     - Returns
   * - ``widget.fill(value)``
     - Set widget value
     - ``bool`` (changed)
   * - ``widget.read()``
     - Get widget value
     - ``Any``
   * - ``view.fill(data)``
     - Fill multiple widgets
     - ``bool`` (changed)

Parameter Types
===============

**Common Type Annotations**

.. code-block:: python

    from typing import Union, Optional, List, Dict, Any
    from playwright.sync_api import Locator, ElementHandle

    # Locator aliases
    LocatorAlias = Union[str, Dict[str, str], Locator, ElementHandle, Widget]
    ElementParent = Union[LocatorAlias, Browser]
    ViewParent = Union[Browser, View]

    # Version types
    VString = Union[str, Version, List[Union[int, str]]]

    # Handler types
    Handler = Union[str, ClickableMixin, Callable]

**Locator Formats**

.. code-block:: python

    # String locators (auto-detected)
    "#my-id"                    # CSS ID selector
    ".my-class"                 # CSS class selector
    "button#submit.primary"     # CSS combined selector
    "//div[@class='content']"   # XPath expression

    # Dictionary locators (explicit)
    {"css": "#my-element"}      # CSS selector
    {"xpath": "//button[1]"}    # XPath selector
    {"text": "Click Me"}        # Text content
    {"id": "submit-button"}     # Element ID
    {"role": "button"}          # ARIA role

Usage Patterns
==============

**Pattern 1: Basic Widget Usage**

.. code-block:: python

    from widgetastic.widget import View, TextInput, Button

    class LoginView(View):
        username = TextInput("#username")
        password = TextInput("#password")
        submit = Button("#login-btn")

    # Usage
    login = LoginView(browser)
    login.fill({"username": "user", "password": "pass"})
    login.submit.click()

**Pattern 2: Advanced Locator Usage**

.. code-block:: python

    from widgetastic.locator import SmartLocator
    from widgetastic.utils import ParametrizedLocator

    # Smart locator with explicit type
    submit_btn = Button(SmartLocator({"text": "Submit Form"}))

    # Parametrized locator for dynamic content
    class UserRow(ParametrizedView):
        PARAMETERS = ("user_id",)
        ROOT = ParametrizedLocator("//tr[@data-user-id='{user_id}']")

**Pattern 3: Error Handling**

.. code-block:: python

    from widgetastic.exceptions import NoSuchElementException

    try:
        widget.click()
    except NoSuchElementException:
        print("Widget not found")
    except WidgetOperationFailed:
        print("Operation failed")

Version Compatibility
=====================

.. list-table:: Version Compatibility Matrix
   :header-rows: 1
   :widths: 20 20 20 40

   * - widgetastic.core
     - Python
     - Playwright
     - Notes
   * - 2.0+
     - 3.10+
     - 1.54+
     - Current stable release
   * - 1.30+
     - 3.8+
     - 1.40+
     - Legacy maintenance
   * - 1.0-1.29
     - 3.7+
     - N/A
     - Selenium-based (deprecated)

**Migration Notes**

- **v2.0**: Switched from Selenium to Playwright backend
- **v1.30**: Last Selenium-compatible version
- **v1.20**: Introduced OUIA support
- **v1.10**: Added parametrized views

Contributing to Documentation
=============================

**Found an Error?**

Help improve this documentation:

1. **Report Issues**: `GitHub Issues <https://github.com/RedHatQE/widgetastic.core/issues>`_
2. **Submit Fixes**: Pull requests welcome for corrections
3. **Suggest Improvements**: Better examples, missing details
4. **Add Examples**: Real-world usage patterns

**Documentation Standards**

- **Complete Examples**: Every method should have working code
- **Parameter Descriptions**: All parameters documented with types
- **Return Values**: Clear description of what methods return
- **Error Conditions**: When methods fail and what exceptions are raised
- **Cross-References**: Links to related methods and concepts

**API Documentation Guidelines**

.. code-block:: python

    def example_method(self, param1: str, param2: Optional[int] = None) -> bool:
        """Brief one-line description of what the method does.

        Longer description explaining the method's behavior, use cases,
        and any important details about its implementation.

        Args:
            param1: Description of first parameter including type and constraints
            param2: Description of optional parameter with default behavior

        Returns:
            Description of return value and what it represents

        Raises:
            ExceptionType: When this exception is raised and why
            AnotherException: Another possible exception condition

        Examples:
            Basic usage example:

            >>> result = obj.example_method("test")
            >>> print(result)
            True

            Advanced usage with optional parameter:

            >>> result = obj.example_method("test", param2=42)
            >>> if result:
            ...     print("Operation successful")

        Note:
            Any important notes, warnings, or additional information

        See Also:
            related_method: Related functionality
            OtherClass.method: Cross-references to related APIs
        """

Getting Started with the API
=============================

**New to Widgetastic?**

1. Start with the Browser classes for basic browser operations
2. Learn about Widgets for UI component interaction
3. Explore Views for organizing your automation code
4. Review the tutorials section for hands-on examples

**Looking for Specific Functionality?**

Use the module index to quickly find what you need:

* **Element Location** → Browser and Locators modules
* **Form Automation** → Widget classes (TextInput, Select, Checkbox)
* **Page Organization** → Views and Widget base classes
* **Error Handling** → Exceptions module
* **Advanced Features** → Utils module (VersionPick, ParametrizedString)
* **Accessibility** → OUIA support modules

**Integration Examples**

See the tutorials section for complete, real-world implementations showing how different API components work together.

This API reference is your complete guide to widgetastic.core. Every public method, class, and function is documented with examples and best practices. Happy automating! 🚀
