========================
Version Picking Tutorial
========================

This tutorial demonstrates version picking in Widgetastic.core, a powerful feature for handling application evolution and multiple product versions. You'll learn to create version-aware widgets and views that adapt to different application versions automatically.

.. note::
   **Time Required**: 35 minutes
   **Prerequisites**: Basic and advanced widgets tutorials
   **Key Concept**: Version-dependent widget behavior

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Understand version picking concepts and use cases
* ✅ Implement version-aware widgets using VersionPick
* ✅ Handle application evolution with minimal code changes
* ✅ Create version detection strategies
* ✅ Test across multiple application versions

Understanding Version Picking
=============================

Version picking allows widgets and views to adapt their behavior based on the application version being tested:

**Why Version Picking is Important**
* **Application Evolution**: UI changes between software versions
* **Backward Compatibility**: Support testing multiple versions simultaneously
* **Maintenance Efficiency**: Single test suite for multiple product versions
* **Gradual Migration**: Smooth transitions between widget implementations

**How Version Picking Works**
* Define multiple implementations for the same logical widget
* Associate each implementation with version ranges
* Framework automatically selects correct implementation at runtime
* Fallback to default implementation when no version matches

Setting Up Version Picking Environment
======================================

.. code-block:: python

    from pathlib import Path
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput, Button, Select
    from widgetastic.utils import VersionPick, Version

    # Custom browser with version information
    class VersionedBrowser(Browser):
        """Browser with version detection capabilities."""

        def __init__(self, page, product_version="1.0.0"):
            super().__init__(page)
            self._product_version = product_version

        @property
        def product_version(self):
            """Return the current product version."""
            return Version(self._product_version)

    def setup_versioned_browser(version="1.0.0"):
        """Setup browser with specific version."""
        test_page_path = Path("testing/html/testing_page.html").resolve()
        test_page_url = test_page_path.as_uri()

        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()

        # Create versioned browser
        browser = VersionedBrowser(page, product_version=version)
        browser.goto(test_page_url)

        return browser, p, browser_instance, context

    # Test with different versions
    browser_v1, p1, bi1, ctx1 = setup_versioned_browser("1.0.0")
    browser_v2, p2, bi2, ctx2 = setup_versioned_browser("2.1.0")

Basic Version Picking
=====================

Start with simple version-dependent widget definitions:

**Simple Version Pick Example**

.. code-block:: python

    from widgetastic.utils import VersionPick

    class VersionedLoginForm(View):
        """Login form that evolved between versions."""

        # Version 1.x used ID-based locators
        # Version 2.x moved to name-based locators
        username_input = VersionPick({
            Version.lowest(): TextInput(id="input"),      # Default/fallback (v1.x)
            "2.0.0": TextInput(name="input1")             # Version 2.0.0+ (newer approach)
        })

        # Submit button changed from ID to class in v2.x
        submit_button = VersionPick({
            Version.lowest(): Text(id="a_button"),        # v1.x implementation
            "2.0.0": Text(locator=".submit-btn")          # v2.x implementation (hypothetical)
        })

        # New field added in version 2.1.0
        remember_me = VersionPick({
            "2.1.0": Checkbox(id="input2")                # Only exists in v2.1.0+
        })

    # Test with version 1.0.0 browser
    login_form_v1 = VersionedLoginForm(browser_v1)
    print(f"Browser v1 version: {browser_v1.product_version}")
    print(f"Username input locator (v1): {login_form_v1.username_input.locator}")

    # Test with version 2.1.0 browser
    login_form_v2 = VersionedLoginForm(browser_v2)
    print(f"Browser v2 version: {browser_v2.product_version}")
    print(f"Username input locator (v2): {login_form_v2.username_input.locator}")

    # Demonstrate version-specific widgets
    if hasattr(login_form_v1, 'remember_me') and login_form_v1.remember_me:
        print("v1 has remember_me: False")
    else:
        print("v1 has remember_me: False")

    if hasattr(login_form_v2, 'remember_me') and login_form_v2.remember_me:
        print("v2 has remember_me: True")
    else:
        print("v2 has remember_me: False")

**Version Range Specifications**

.. code-block:: python

    class AdvancedVersionPicking(View):
        """Demonstrates various version picking strategies."""

        # Range-based version picking
        text_widget = VersionPick({
            Version.lowest(): Text(id="old-text"),        # Default (< 1.5.0)
            "1.5.0": Text(id="medium-text"),              # 1.5.0 <= version < 2.0.0
            "2.0.0": Text(id="new-text")                  # 2.0.0+
        })

        # Specific version targeting
        feature_button = VersionPick({
            "1.2.0": Text(id="button-v12"),               # Only 1.2.0
            "1.3.0": Text(id="button-v13"),               # Only 1.3.0
            "2.0.0": Text(id="button-v2")                 # 2.0.0+
        })

        # Complex version logic with conditions
        conditional_input = VersionPick({
            # Use old input for versions < 1.8.0
            Version.lowest(): TextInput(id="input"),

            # Use transitional input for 1.8.0-1.9.x
            "1.8.0": TextInput(name="transitional_input"),

            # Use new input for 2.0.0+
            "2.0.0": TextInput(locator="input[data-testid='modern-input']")
        })

    advanced_v1 = AdvancedVersionPicking(browser_v1)
    advanced_v2 = AdvancedVersionPicking(browser_v2)

    def test_version_selection():
        """Test which widgets are selected for each version."""

        # Test version 1.0.0 selections
        print("=== Version 1.0.0 Widget Selection ===")
        try:
            # This will use the lowest version (default) implementations
            print(f"Text widget uses: {advanced_v1.text_widget.locator}")
            print(f"Conditional input uses: {advanced_v1.conditional_input.locator}")
        except Exception as e:
            print(f"Error accessing v1 widgets: {e}")

        # Test version 2.1.0 selections
        print("\n=== Version 2.1.0 Widget Selection ===")
        try:
            # This will use version 2.0.0+ implementations
            print(f"Text widget uses: {advanced_v2.text_widget.locator}")
            print(f"Conditional input uses: {advanced_v2.conditional_input.locator}")
        except Exception as e:
            print(f"Error accessing v2 widgets: {e}")

    test_version_selection()

Dynamic Version Detection
=========================

Implement strategies to automatically detect application version:

**Browser-Based Version Detection**

.. code-block:: python

    class SmartVersionBrowser(VersionedBrowser):
        """Browser that automatically detects application version."""

        def __init__(self, page):
            # Start with unknown version
            super().__init__(page, product_version="0.0.0")
            self._detected_version = None

        @property
        def product_version(self):
            """Detect and return product version."""
            if self._detected_version is None:
                self._detected_version = self._detect_version()
            return Version(self._detected_version)

        def _detect_version(self):
            """Detect application version using various strategies."""
            # Strategy 1: Check for version meta tag
            try:
                version_meta = self.element('meta[name="app-version"]')
                if version_meta:
                    return self.get_attribute(version_meta, "content")
            except:
                pass

            # Strategy 2: Check JavaScript global variable
            try:
                version = self.execute_script("return window.APP_VERSION || window.appVersion")
                if version:
                    return version
            except:
                pass

            # Strategy 3: Detect based on UI elements (feature detection)
            try:
                # If modern input exists, assume v2+
                modern_input = self.element('input[data-testid="modern-input"]')
                if modern_input:
                    return "2.0.0"
            except:
                pass

            # Strategy 4: Check for version-specific CSS classes or IDs
            try:
                # If new button class exists, assume v2+
                new_button = self.element('.modern-button')
                if new_button:
                    return "2.0.0"
            except:
                pass

            # Strategy 5: Check page title or other content indicators
            try:
                title = self.title
                if "v2" in title.lower() or "2.0" in title:
                    return "2.0.0"
            except:
                pass

            # Default fallback
            return "1.0.0"

    # Test smart version detection
    def test_smart_version_detection():
        """Test automatic version detection."""
        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()

        smart_browser = SmartVersionBrowser(page)

        # Navigate to testing page
        test_page_path = Path("testing/html/testing_page.html").resolve()
        smart_browser.goto(test_page_path.as_uri())

        # Get detected version
        detected_version = smart_browser.product_version
        print(f"Auto-detected version: {detected_version}")

        # Cleanup
        context.close()
        browser_instance.close()
        p.stop()

        return detected_version

    detected_version = test_smart_version_detection()

Complex Version Picking Scenarios
=================================

Handle advanced version picking use cases:

**Widget Composition with Version Picking**

.. code-block:: python

    class VersionedFormWidget(View):
        """Complex form that changed significantly between versions."""

        def __init__(self, parent, logger=None):
            super().__init__(parent, logger)

        # Form layout changed completely in v2
        form_container = VersionPick({
            Version.lowest(): View(ROOT="#testform"),     # v1: single form
            "2.0.0": View(ROOT="#advanced-form")          # v2: advanced form (hypothetical)
        })

        # Input strategy changed
        inputs = VersionPick({
            # v1: Simple ID-based inputs
            Version.lowest(): {
                'username': TextInput(name="input1"),
                'checkbox': Checkbox(id="input2")
            },
            # v2: Advanced data-testid based inputs
            "2.0.0": {
                'username': TextInput(locator='input[data-testid="username"]'),
                'email': TextInput(locator='input[data-testid="email"]'),
                'checkbox': Checkbox(locator='input[data-testid="terms"]'),
                'submit': Button(locator='button[data-testid="submit"]')
            }
        })

        def get_input(self, input_name):
            """Get version-appropriate input widget."""
            current_inputs = self.inputs
            return current_inputs.get(input_name)

        def fill_form(self, data):
            """Fill form using version-appropriate strategy."""
            current_version = self.browser.product_version
            results = {}

            if current_version >= Version("2.0.0"):
                # v2+ strategy: use advanced inputs
                for field_name, value in data.items():
                    input_widget = self.get_input(field_name)
                    if input_widget and input_widget.is_displayed:
                        changed = input_widget.fill(value)
                        results[field_name] = {'changed': changed, 'value': input_widget.read()}
                    else:
                        results[field_name] = {'error': 'Widget not available'}
            else:
                # v1 strategy: use basic inputs
                basic_inputs = self.get_input('username'), self.get_input('checkbox')
                username_input, checkbox_input = basic_inputs

                if 'username' in data and username_input:
                    changed = username_input.fill(data['username'])
                    results['username'] = {'changed': changed, 'value': username_input.read()}

                if 'checkbox' in data and checkbox_input:
                    changed = checkbox_input.fill(data['checkbox'])
                    results['checkbox'] = {'changed': changed, 'value': checkbox_input.read()}

            return results

    # Test with different versions
    versioned_form_v1 = VersionedFormWidget(browser_v1)
    versioned_form_v2 = VersionedFormWidget(browser_v2)

    # Test form filling with different versions
    test_data = {
        'username': 'version_test_user',
        'checkbox': True,
        'email': 'test@example.com'  # Only available in v2+
    }

    print("=== Version-Specific Form Filling ===")
    v1_results = versioned_form_v1.fill_form(test_data)
    print(f"v1.0.0 fill results: {v1_results}")

    v2_results = versioned_form_v2.fill_form(test_data)
    print(f"v2.1.0 fill results: {v2_results}")

**Method-Level Version Picking**

.. code-block:: python

    class VersionedBehaviorWidget(View):
        """Widget with version-dependent behavior methods."""

        # Basic widget that exists in all versions
        main_input = TextInput(id="input")

        # Version-specific behavior methods
        def fill_data(self, value):
            """Fill data using version-appropriate method."""
            current_version = self.browser.product_version

            if current_version >= Version("2.0.0"):
                return self._fill_data_v2(value)
            else:
                return self._fill_data_v1(value)

        def _fill_data_v1(self, value):
            """v1 fill strategy: simple fill."""
            changed = self.main_input.fill(value)
            return {'method': 'v1_simple', 'changed': changed}

        def _fill_data_v2(self, value):
            """v2 fill strategy: fill with validation."""
            # v2 has client-side validation
            if len(value) < 3:
                return {'method': 'v2_validated', 'error': 'Value too short for v2'}

            changed = self.main_input.fill(value)

            # v2 might have additional confirmation
            try:
                # Hypothetical: v2 shows confirmation after fill
                confirm_element = self.browser.element('.fill-confirmation', parent=self)
                if confirm_element:
                    return {'method': 'v2_validated', 'changed': changed, 'confirmed': True}
            except:
                pass

            return {'method': 'v2_validated', 'changed': changed}

        # Version-specific validation
        validation_rules = VersionPick({
            Version.lowest(): {
                'min_length': 1,
                'required_fields': ['main_input']
            },
            "2.0.0": {
                'min_length': 3,
                'required_fields': ['main_input'],
                'format_validation': True
            }
        })

        def validate_input(self, value):
            """Validate input using version-appropriate rules."""
            rules = self.validation_rules

            if len(value) < rules['min_length']:
                return {'valid': False, 'error': f'Minimum length: {rules["min_length"]}'}

            if rules.get('format_validation') and not value.isalnum():
                return {'valid': False, 'error': 'Only alphanumeric characters allowed in v2+'}

            return {'valid': True}

    # Test version-specific behavior
    behavior_v1 = VersionedBehaviorWidget(browser_v1)
    behavior_v2 = VersionedBehaviorWidget(browser_v2)

    test_values = ['ab', 'valid_input', 'test@123']

    print("\n=== Version-Specific Behavior Testing ===")
    for value in test_values:
        print(f"\nTesting value: '{value}'")

        # Test v1 behavior
        v1_validation = behavior_v1.validate_input(value)
        print(f"  v1 validation: {v1_validation}")
        if v1_validation['valid']:
            v1_fill = behavior_v1.fill_data(value)
            print(f"  v1 fill result: {v1_fill}")

        # Test v2 behavior
        v2_validation = behavior_v2.validate_input(value)
        print(f"  v2 validation: {v2_validation}")
        if v2_validation['valid']:
            v2_fill = behavior_v2.fill_data(value)
            print(f"  v2 fill result: {v2_fill}")

Testing Across Multiple Versions
================================

Implement comprehensive version testing strategies:

**Multi-Version Test Suite**

.. code-block:: python

    class MultiVersionTestSuite:
        """Test suite that runs across multiple application versions."""

        def __init__(self, test_versions):
            self.test_versions = test_versions
            self.test_results = {}

        def run_version_tests(self, test_function, test_name):
            """Run test function across all versions."""
            results = {}

            for version in self.test_versions:
                print(f"\n--- Testing {test_name} on version {version} ---")

                try:
                    # Setup browser for this version
                    browser, p, bi, ctx = setup_versioned_browser(version)

                    # Run test
                    result = test_function(browser, version)
                    results[version] = result

                    # Cleanup
                    ctx.close()
                    bi.close()
                    p.stop()

                except Exception as e:
                    results[version] = {'error': str(e)}

            self.test_results[test_name] = results
            return results

        def generate_compatibility_report(self):
            """Generate compatibility report across versions."""
            report = {
                'total_tests': len(self.test_results),
                'version_coverage': len(self.test_versions),
                'compatibility_matrix': {}
            }

            for test_name, version_results in self.test_results.items():
                report['compatibility_matrix'][test_name] = {}

                for version, result in version_results.items():
                    if 'error' in result:
                        status = 'FAILED'
                    else:
                        status = 'PASSED'

                    report['compatibility_matrix'][test_name][version] = status

            return report

    # Example version test functions
    def test_form_filling(browser, version):
        """Test form filling on specific version."""
        form = VersionedFormWidget(browser)

        test_data = {
            'username': f'user_v{version}',
            'checkbox': True
        }

        results = form.fill_form(test_data)

        # Check if filling worked
        success_count = sum(1 for r in results.values() if 'error' not in r)

        return {
            'success': success_count > 0,
            'filled_fields': success_count,
            'total_fields': len(test_data),
            'details': results
        }

    def test_widget_selection(browser, version):
        """Test that correct widgets are selected for version."""
        form = VersionedLoginForm(browser)

        # Try to access version-specific widgets
        results = {
            'username_accessible': hasattr(form, 'username_input') and form.username_input.is_displayed,
            'submit_accessible': hasattr(form, 'submit_button') and form.submit_button.is_displayed,
        }

        # Check version-specific widgets
        if Version(version) >= Version("2.1.0"):
            results['remember_me_accessible'] = hasattr(form, 'remember_me') and form.remember_me

        return {
            'success': all(results.values()),
            'accessible_widgets': results
        }

    # Run multi-version tests
    test_versions = ["1.0.0", "2.0.0", "2.1.0"]
    test_suite = MultiVersionTestSuite(test_versions)

    # Run tests
    form_results = test_suite.run_version_tests(test_form_filling, "form_filling")
    widget_results = test_suite.run_version_tests(test_widget_selection, "widget_selection")

    # Generate compatibility report
    compatibility_report = test_suite.generate_compatibility_report()

    print("\n=== Multi-Version Compatibility Report ===")
    print(f"Total tests: {compatibility_report['total_tests']}")
    print(f"Version coverage: {compatibility_report['version_coverage']}")

    for test_name, version_results in compatibility_report['compatibility_matrix'].items():
        print(f"\n{test_name}:")
        for version, status in version_results.items():
            print(f"  v{version}: {status}")

Best Practices for Version Picking
==================================

Guidelines for effective version management:

**Version Picking Best Practices**

.. code-block:: python

    # 1. Use semantic versioning consistently
    class GoodVersionPractices(View):
        # ✓ Good - Clear version boundaries
        widget = VersionPick({
            Version.lowest(): TextInput(id="old-input"),
            "2.0.0": TextInput(id="new-input"),
            "3.0.0": TextInput(locator="input[data-testid='modern-input']")
        })

        # ✗ Avoid - Too many micro-version distinctions
        # bad_widget = VersionPick({
        #     "1.0.0": TextInput(id="input-v100"),
        #     "1.0.1": TextInput(id="input-v101"),
        #     "1.0.2": TextInput(id="input-v102"),
        # })

    # 2. Document version changes and rationale
    class DocumentedVersionChanges(View):
        """Form widget with documented version evolution."""

        # Document why versions changed
        submit_button = VersionPick({
            # v1.x: Used simple ID-based locator
            Version.lowest(): Button(id="submit"),

            # v2.0: Moved to CSS class for styling consistency
            "2.0.0": Button(locator=".submit-button"),

            # v3.0: Adopted data-testid for better testing
            "3.0.0": Button(locator="button[data-testid='submit']")
        })

    # 3. Provide fallback strategies
    class FallbackVersionPicking(View):
        """Version picking with robust fallbacks."""

        primary_input = VersionPick({
            # Always provide a lowest version fallback
            Version.lowest(): TextInput(id="input"),

            # Version-specific improvements
            "2.0.0": TextInput(name="primary_input"),
            "3.0.0": TextInput(locator="input[data-testid='primary']")
        })

        def safe_fill(self, value):
            """Fill with fallback error handling."""
            try:
                return self.primary_input.fill(value)
            except Exception as e:
                # Log version and error for debugging
                version = self.browser.product_version
                print(f"Fill failed for version {version}: {e}")
                return False

    # 4. Test version boundaries carefully
    def test_version_boundaries():
        """Test edge cases around version boundaries."""
        edge_versions = ["1.9.9", "2.0.0", "2.0.1"]

        for version in edge_versions:
            browser, p, bi, ctx = setup_versioned_browser(version)
            try:
                form = FallbackVersionPicking(browser)
                result = form.safe_fill("boundary_test")
                print(f"Version {version} fill result: {result}")
            finally:
                ctx.close()
                bi.close()
                p.stop()

    test_version_boundaries()

    # 5. Version picking performance considerations
    class PerformantVersionPicking(View):
        """Optimize version picking for performance."""

        # Cache version-dependent objects when possible
        def __init__(self, parent, logger=None):
            super().__init__(parent, logger)
            self._version_cache = {}

        def get_versioned_widget(self, widget_name):
            """Get widget with caching for performance."""
            cache_key = f"{widget_name}_{self.browser.product_version}"

            if cache_key not in self._version_cache:
                widget_config = self._get_widget_config(widget_name)
                self._version_cache[cache_key] = widget_config

            return self._version_cache[cache_key]

        def _get_widget_config(self, widget_name):
            """Get widget configuration for current version."""
            # This would contain your VersionPick logic
            configs = {
                'input': VersionPick({
                    Version.lowest(): TextInput(id="input"),
                    "2.0.0": TextInput(name="input")
                })
            }
            return configs.get(widget_name)

Final Cleanup
==============

.. code-block:: python

    try:
        # Cleanup all browser instances
        for ctx, bi, p in [(ctx1, bi1, p1), (ctx2, bi2, p2)]:
            ctx.close()
            bi.close()
            p.stop()
    except Exception as e:
        print(f"Cleanup error: {e}")

Summary
=======

Version picking in Widgetastic.core provides:

* **Application Evolution Support**: Handle UI changes across software versions
* **Backward Compatibility**: Maintain single test suite for multiple versions
* **Automatic Selection**: Framework chooses correct implementation at runtime
* **Flexible Strategies**: Support for simple to complex version dependencies
* **Testing Efficiency**: Comprehensive testing across version ranges

Key takeaways:
* Use VersionPick for widgets that change between application versions
* Provide fallback implementations using Version.lowest()
* Document version changes and their rationale clearly
* Test version boundaries and edge cases thoroughly
* Cache version-dependent objects for better performance
* Implement version detection strategies for dynamic environments

This completes the version picking tutorial. You can now handle application evolution gracefully and maintain robust automation across multiple product versions.
