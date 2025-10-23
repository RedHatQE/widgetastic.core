.. _version-picking:

===============
Version picking
===============

This tutorial demonstrates version picking in Widgetastic.core, a powerful feature for handling application evolution and multiple product versions.
You'll learn to create version-aware widgets/views that adapt to different application versions automatically.



Understanding Version Picking
=============================

Version picking allows widgets and views to adapt their behavior based on the application version being tested:

**Why Version Picking is Important**

* **Application Evolution**: UI changes between software versions
* **Backward Compatibility**: Support testing multiple versions simultaneously
* **Maintenance Efficiency**: Single test suite for multiple product versions
* **Gradual Migration**: Smooth transitions between widget implementations

Setting Up Version Picking Environment
======================================

.. code-block:: python

    from pathlib import Path
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser

    # Custom browser with version information
    class BrowserV1(Browser):
        """Browser with version 1.0.0."""

        @property
        def product_version(self):
            """Return the current product version."""
            return Version("1.0.0")

    class BrowserV2(Browser):
        """Browser with version 2.1.0."""

        @property
        def product_version(self):
            """Return the current product version."""
            return Version("2.1.0")

    def get_pw_and_browser(version: str = "v1"):
        """Get browser with specific version."""
        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()
        test_page_path = Path("testing/html/testing_page.html").resolve()
        test_page_url = test_page_path.as_uri()

        if version == "v1":
            return p, BrowserV1(page)
        elif version == "v2":
            return p, BrowserV2(page)
        else:
            raise ValueError(f"Invalid version: {version}")


Basic Version Picking
=====================

Start with simple version-dependent widget definitions:

**Simple Version Pick Example**

In this example, we want to select input and click button for different versions.

* Default/fallback (v1.x): TextInput (name=fill_with_1) and Button (id=#fill_with_button_1)
* Version 2.0.0+ (v2.x): TextInput (name=fill_with_2) and Button (id=#fill_with_button_2)

.. code-block:: python

    from widgetastic.utils import VersionPick, Version
    from widgetastic.widget import View, Text, TextInput

    class VersionedView(View):
        input_field = VersionPick({
            Version.lowest(): TextInput(name="fill_with_1"),      # Default/fallback (v1.x)
            "2.0.0": TextInput(name="fill_with_2")                # Version 2.0.0+ (newer approach)
        })
        click_button = VersionPick({
            Version.lowest(): Text("#fill_with_button_1"),        # Default/fallback (v1.x)
            "2.0.0": Text("#fill_with_button_2")                  # Version 2.0.0+ (newer approach)
        })


*Test with version V1 browser*

.. code-block:: python

    # Test with version 1.0.0 browser
    pw, browser_v1 = get_pw_and_browser("v1")
    view = VersionedView(browser_v1)
    print(f"Browser version (v1): {browser_v1.product_version}")
    print(f"Input locator (v1): {view.input_field.locator}")
    print(f"Button locator (v1): {view.click_button.locator}")
    pw.stop() # close playwright session and browser


*Test with version V2 browser*

.. code-block:: python

    # Test with version 2.1.0 browser
    pw, browser_v2 = get_pw_and_browser("v2")
    view = VersionedView(browser_v2)
    print(f"Browser version (v2): {browser_v2.product_version}")
    print(f"Input locator (v2): {view.input_field.locator}")
    print(f"Button locator (v2): {view.click_button.locator}")
    browser_v2.close() # close playwright session and browser
