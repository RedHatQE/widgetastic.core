==============
Core Concepts
==============

Understanding the fundamental concepts of widgetastic.core is essential for effective UI automation.
This guide introduces the key ideas that make widgetastic powerful and flexible.

The Widget Philosophy
=====================

**What is a Widget?**

In widgetastic, a *widget* represents any interactive or non-interactive element on a web page.
Unlike traditional automation approaches that work directly with raw elements, widgets provide
a higher-level, object-oriented abstraction.

.. code-block:: python

    # Traditional approach (raw elements)
    element = page.locator("#username")
    element.fill("john_doe")

    # Widgetastic approach (widget abstraction)
    username = TextInput("#username")
    username.fill("john_doe")

**Benefits of the Widget Approach**

- **Reusability & DRY Principle**: Define a widget once and reuse it across your entire test suite. No need to rewrite locators and interaction logic multiple times.
- **Maintainability & Single Source of Truth**: When UI changes, update the widget definition in one place. All tests using that widget automatically benefit from the fix.
- **Readability**: Code reads like natural language
- **Consistency & Standardization**: All widgets follow the same interface patterns (``read()``, ``fill()``, ``click()``), reducing cognitive load and learning curve.
- **Robustness & Error Handling**: Widgets include built-in intelligence for element selection, waiting, and error handling.
- **Testability & Debugging**: Widget-based architecture makes tests easier to debug with clear hierarchical structure and meaningful logging.
- **Separation of Concerns**: Business logic stays in tests, UI interaction details stay in widgets, and page structure stays in views.
- **Introspection & Dynamic Behavior**: Widgets can inspect their state and adapt behavior based on current conditions.
- **Scalability for Large Applications**: Widget approach scales naturally as applications grow, supporting complex hierarchies and component reuse patterns.
- **Customization & Extension**: Easy to extend base widgets with application-specific behavior while maintaining the core interface.

The View Paradigm
==================

**What is a View?**

A *view* is a container that groups related widgets together, typically representing a page,
dialog, or section of a web application. Views provide structure and context for widgets.

.. code-block:: python

    class LoginView(View):
        username = TextInput("#username")
        password = TextInput("#password")
        submit_button = Button("//button[@type='submit']")
        error_message = Text(".error-message")

**Understanding Views**

A View is essentially a specialized widget that acts as a container for other widgets. While it's
technically a widget itself (inheriting widget capabilities), its primary purpose is to organize
and manage collections of child widgets that belong together logically.

**Think of it as:**

* **A Widget Container** - Groups related widgets into logical units
* **A Page Representation** - Models entire web pages or sections
* **A Context Provider** - Gives widgets context about where they exist
* **An Organization Tool** - Structures complex UIs into manageable components
**View Hierarchy**

Views can be nested to represent complex UI structures:

.. code-block:: python

    class ApplicationView(View):
        header = HeaderView()
        sidebar = SidebarView()

        class content(View):
            ROOT = "#main-content"

            class user_form(View):
                ROOT = ".user-form"
                name = TextInput("#name")
                email = TextInput("#email")

The Browser Wrapper
===================

**Enhanced Browser Functionality**

Widgetastic's ``Browser`` class wraps Playwright's ``Page`` with additional intelligence:

* **Smart Element Selection**: Chooses visible, interactable elements when multiple matches exist
* **Robust Text Handling**: Extracts text reliably regardless of CSS styling
* **Network Activity Monitoring**: Waits for page stability before interactions
* **Frame Context Management**: Seamless iframe handling

.. code-block:: python

    # Create a widgetastic browser from a Playwright page
    from widgetastic.browser import Browser

    wt_browser = Browser(playwright_page)

**Automatic Parent Injection**

Widgets automatically receive their parent context, enabling proper element scoping:

.. code-block:: python

    class MyView(View):
        ROOT = "#my-section"
        button = Button("//button")  # Automatically scoped to #my-section

Locators and Smart Detection
=============================

**SmartLocator System**

Widgetastic's ``SmartLocator`` class provides intelligent locator resolution that automatically detects locator types and converts them for Playwright compatibility.
This eliminates the need to explicitly specify locator strategies in most cases.

.. code-block:: python

    from widgetastic.locator import SmartLocator

    # String auto-detection - SmartLocator detects the strategy
    loc1 = SmartLocator("#submit-btn")        # CSS selector detected
    loc2 = SmartLocator("//div[@id='modal']") # XPath detected
    loc3 = SmartLocator("div.container")      # CSS selector detected

    # Explicit formats for precise control
    loc4 = SmartLocator(text="Click Me")      # Keyword argument
    loc5 = SmartLocator({"role": "button"})   # Dictionary format
    loc6 = SmartLocator("xpath", "//button[1]") # Tuple format

**Automatic Strategy Detection**

SmartLocator uses pattern matching to detect locator strategies:

* **CSS Detection**: ``#myid``, ``.myclass``, ``div#id.class``
* **XPath Detection**: ``//div``, ``./span``, ``(//a)[1]``, ``/html/body``
* **Fallback**: Complex selectors like ``div > span`` default to CSS

**Supported Locator Strategies**

* **CSS**: ``#id``, ``.class``, ``tag#id.class``, ``div > span``
* **XPath**: ``//div``, ``./span``, ``(//a)[1]``, ``.//input``
* **Text**: ``text="Click Me"`` - finds elements containing text
* **ID**: ``id="my-element"`` - finds by element ID
* **Role**: ``role="button"`` - finds by ARIA role
* **Data attributes**: ``data-testid="element"`` - test automation attributes
* **Other attributes**: ``placeholder``, ``title``, ``name``

**Widget Integration**

Widgets automatically use SmartLocator for their locator arguments:

.. code-block:: python

    # All these work the same way - SmartLocator handles detection
    button1 = Button("#submit")              # CSS auto-detected
    button2 = Button("//button[@type='submit']") # XPath auto-detected
    button3 = Button({"text": "Submit"})     # Explicit text locator

.. tip::
   **For Complete SmartLocator Details**

   For comprehensive documentation including strategy resolution order, regex patterns,
   and advanced usage examples, see the ``SmartLocator`` class documentation in
   ``widgetastic.locator``. This includes detailed information about CSS detection
   patterns, XPath recognition, and the widget locator protocol.

.. note::
   **Widget Initialization Arguments**

   The arguments required to initialize a widget depend on its specific implementation.
   Always check the widget's documentation to understand what it needs for initialization -
   some widgets require ``id``, others need ``locator``, ``text``, or other specific parameters.
   Each widget type has its own initialization signature.

The Read/Fill Interface
=======================

**Consistent Data Operations**

Every widget implements a standardized interface for data interaction:

**Read Interface**

.. code-block:: python

    # Read individual widget
    username_value = username_widget.read()

    # Read entire view (returns dictionary)
    form_data = login_view.read()
    # Returns: {"username": "john_doe", "password": "secret", ...}

**Fill Interface**

.. code-block:: python

    # Fill individual widget
    changed = username_widget.fill("new_value")  # Returns True/False

    # Fill entire view
    login_view.fill({
        "username": "john_doe",
        "password": "secret123"
    })

**Fill Contract**

All widgets follow these rules:
* ``fill()`` returns ``True`` if the value changed, ``False`` otherwise
* ``widget.fill(widget.read())`` should always work (idempotent)
* ``read()`` returns values compatible with ``fill()``

Element Lifecycle and Caching
==============================

**Lazy Element Resolution**

Widgets don't store raw element references, preventing stale element issues:

.. code-block:: python

    class MyView(View):
        button = Button("#submit")  # This creates a widget descriptor

    view = MyView(browser)
    # Element is only located when accessed:
    view.button.click()  # NOW the element is found and clicked

**Widget Caching**

Widget instances are cached per view for performance:

.. code-block:: python

    view = MyView(browser)
    button1 = view.button  # Creates and caches widget instance
    button2 = view.button  # Returns cached instance (same object)
    assert button1 is button2  # True

Version Picking
===============

**Handling UI Evolution**

Applications change over time. Version picking allows widgets to adapt to different versions:

.. code-block:: python

    from widgetastic.utils import VersionPick, Version

    class MyView(View):
        submit_button = VersionPick({
            Version.lowest(): Button("//input[@value='Submit']"),  # Old version
            "2.0.0": Button("//button[contains(@class, 'submit')]"),  # New version
        })

**Automatic Resolution**

The browser's ``product_version`` property determines which widget is used:

.. code-block:: python

    class MyBrowser(Browser):
        @property
        def product_version(self):
            return "2.1.0"  # Widget for version 2.0.0+ will be selected

Parametrized Views
==================

**Dynamic View Creation**

For repeated UI patterns that differ only in parameters:

.. code-block:: python

    from widgetastic.utils import ParametrizedLocator

    class UserRow(ParametrizedView):
        PARAMETERS = ("user_id",)
        ROOT = ParametrizedLocator("//tr[@data-user-id='{user_id}']")

        name = Text(".//td[1]")
        email = Text(".//td[2]")
        actions = Button(".//button")

**Usage**

.. code-block:: python

    # Create parametrized instance
    user_row = UserRow(browser, user_id="123")

    # Or use in nested view
    class UsersView(View):
        class user_row(ParametrizedView):
            PARAMETERS = ("user_id",)
            # ... widget definitions

    view = UsersView(browser)
    john_row = view.user_row("john123")

Conditional Views
=================

**Context-Dependent UI**

Some UI sections change based on user selections or application state:

.. code-block:: python

    from widgetastic.widget import ConditionalSwitchableView

    class FormView(View):
        user_type = Select("#user-type")

        user_details = ConditionalSwitchableView(reference="user_type")

        @user_details.register("admin")
        class AdminDetails(View):
            admin_key = TextInput("#admin-key")
            permissions = Select("#permissions")

        @user_details.register("regular")
        class RegularDetails(View):
            department = Select("#department")
            manager = TextInput("#manager")

OUIA Support
============

**Accessibility-First Automation**

OUIA (Open UI Automation) enables automation through standardized data attributes:

.. code-block:: python

    from widgetastic.ouia import OUIAGenericWidget

    class Button(OUIAGenericWidget):
        pass

    # Locates elements by data-ouia-component-type and data-ouia-component-id
    save_button = Button(component_id="save-user")

Error Handling and Logging
===========================

**Built-in Error Management**

Widgetastic provides meaningful error messages and comprehensive logging:

.. code-block:: python

    from widgetastic.exceptions import NoSuchElementException

    try:
        widget.click()
    except NoSuchElementException as e:
        print(f"Element not found: {e}")

**Hierarchical Logging**

Every widget gets a logger that shows its position in the widget hierarchy:

.. code-block:: text

    [MyView/user_form/username]: Filled 'john_doe' to value 'admin' with result True
    [MyView/user_form/submit_button]: Click started
    [MyView/user_form/submit_button]: Click (elapsed 234 ms)

Key Takeaways
=============

1. **Widgets** represent UI elements with consistent read/fill interfaces
2. **Views** group related widgets and provide structure
3. **SmartLocators** automatically handle different locator types
4. **Lazy resolution** prevents stale element issues
5. **Version picking** adapts to application changes
6. **Parametrized views** handle repeated UI patterns
7. **Conditional views** adapt to dynamic UI sections
8. **OUIA support** enables accessibility-driven automation

Next Steps
==========

Now that you understand the core concepts:

1. :doc:`first-steps` - Write your first widgetastic script
2. :doc:`../quickstart/index` - See practical examples
3. :doc:`../tutorials/index` - Deep dive into specific topics
