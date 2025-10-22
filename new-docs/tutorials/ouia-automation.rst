===================================
OUIA (Open UI Automation) Tutorial
===================================

This tutorial demonstrates OUIA (Open UI Automation) support in Widgetastic.core using examples from ``testing_page.html``. You'll learn to work with OUIA-compliant components and leverage standardized automation attributes.

.. note::
   **Time Required**: 30 minutes
   **Prerequisites**: Basic widgets tutorial
   **Test Pages Used**: ``testing/html/testing_page.html``

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Understand OUIA standards and automation benefits
* ✅ Work with OUIA-compliant widgets without explicit locators
* ✅ Use OUIA component types and IDs for reliable automation
* ✅ Handle OUIA safe/unsafe states for testing coordination
* ✅ Implement OUIA-based automation strategies

Understanding OUIA Standards
============================

OUIA (Open UI Automation) is a standard that defines how web applications should expose automation-friendly attributes:

**OUIA Attributes**
* ``data-ouia-component-type``: Identifies the component type (e.g., "Button", "TextInput")
* ``data-ouia-component-id``: Unique identifier for the component instance
* ``data-ouia-safe``: Boolean indicating if component is ready for automation

**Benefits of OUIA**
* **Stable Locators**: Less brittle than CSS classes or complex XPath
* **Semantic Meaning**: Component types have clear automation intent
* **Test Coordination**: Safe/unsafe states prevent timing issues
* **Cross-Framework**: Standard works across different UI frameworks

Setting Up OUIA Environment
===========================

.. code-block:: python

    from pathlib import Path
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.ouia import OUIAGenericView, OUIAGenericWidget
    from widgetastic.ouia.text import Text as OUIAText
    from widgetastic.ouia.text_input import TextInput as OUIATextInput
    from widgetastic.ouia.checkbox import Checkbox as OUIACheckbox

    def setup_ouia_browser():
        """Setup browser with OUIA testing page."""
        test_page_path = Path("testing/html/testing_page.html").resolve()
        test_page_url = test_page_path.as_uri()

        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()
        browser = Browser(page)

        # Navigate to testing page with OUIA examples
        browser.goto(test_page_url)

        return browser, p, browser_instance, context

    browser, playwright, browser_instance, context = setup_ouia_browser()

OUIA Generic Widgets
====================

OUIA widgets can be located using component types and IDs without explicit locators:

**Basic OUIA Widget Usage**

.. code-block:: python

    from widgetastic.ouia import OUIAGenericWidget

    class BasicOUIAWidgets(OUIAGenericView):
        # OUIA widgets using component IDs - no locator needed!
        ouia_button = OUIAGenericWidget(component_id="This is a button")
        ouia_select = OUIAGenericWidget(component_id="some_id")
        ouia_text_input = OUIAGenericWidget(component_id="unique_id", component_type="TextInput")
        ouia_checkbox = OUIAGenericWidget(component_id="unique_id", component_type="CheckBox")
        ouia_text = OUIAGenericWidget(component_id="unique_id", component_type="Text")

    ouia_widgets = BasicOUIAWidgets(browser)

    # Verify OUIA widgets are found and accessible
    print(f"OUIA button displayed: {ouia_widgets.ouia_button.is_displayed}")
    print(f"OUIA select displayed: {ouia_widgets.ouia_select.is_displayed}")
    print(f"OUIA text input displayed: {ouia_widgets.ouia_text_input.is_displayed}")

    # Read OUIA attributes
    button_type = browser.get_attribute(ouia_widgets.ouia_button, "data-ouia-component-type")
    button_id = browser.get_attribute(ouia_widgets.ouia_button, "data-ouia-component-id")
    button_safe = browser.get_attribute(ouia_widgets.ouia_button, "data-ouia-safe")

    print(f"Button - Type: {button_type}, ID: {button_id}, Safe: {button_safe}")

**Specialized OUIA Widgets**

.. code-block:: python

    # Use specialized OUIA widgets for better type safety
    class SpecializedOUIAWidgets(OUIAGenericView):
        # Specialized OUIA widgets with implicit component types
        ouia_text = OUIAText(component_id="unique_id")
        ouia_input = OUIATextInput(component_id="unique_id")
        ouia_checkbox = OUIACheckbox(component_id="unique_id")

    specialized_ouia = SpecializedOUIAWidgets(browser)

    # Work with specialized widgets
    if specialized_ouia.ouia_text.is_displayed:
        text_content = specialized_ouia.ouia_text.read()
        print(f"OUIA text content: {text_content}")

    # Fill OUIA input
    if specialized_ouia.ouia_input.is_displayed:
        specialized_ouia.ouia_input.fill("OUIA automated input")
        input_value = specialized_ouia.ouia_input.read()
        print(f"OUIA input value: {input_value}")

    # Toggle OUIA checkbox
    if specialized_ouia.ouia_checkbox.is_displayed:
        specialized_ouia.ouia_checkbox.fill(True)
        checkbox_state = specialized_ouia.ouia_checkbox.read()
        print(f"OUIA checkbox state: {checkbox_state}")

OUIA Views and Component Hierarchies
====================================

OUIA views can contain other OUIA components in hierarchical structures:

**OUIA View Containers**

.. code-block:: python

    class OUIAContainerView(OUIAGenericView):
        """OUIA view that represents a container with OUIA component type."""
        # The view itself has OUIA attributes
        ROOT = "[data-ouia-component-type='TestView'][data-ouia-component-id='ouia']"

        # Child OUIA widgets within the container
        container_select = OUIAGenericWidget(component_id="some_id", component_type="PF/Select")
        container_button = OUIAGenericWidget(component_id="This is a button", component_type="PF/Button")
        container_input = OUIATextInput(component_id="unique_id")
        container_checkbox = OUIACheckbox(component_id="unique_id")
        container_text = OUIAText(component_id="unique_id")

    ouia_container = OUIAContainerView(browser)

    # Verify container view is accessible
    print(f"OUIA container displayed: {ouia_container.is_displayed}")

    # Work with container widgets
    if ouia_container.container_select.is_displayed:
        # Get select options
        select_element = ouia_container.container_select

        # Note: For select operations, you might need to use standard Select widget
        # with the OUIA element as locator
        from widgetastic.widget import Select
        ouia_select_widget = Select(locator=select_element)

        current_selection = ouia_select_widget.read()
        print(f"OUIA select current value: {current_selection}")

        # Change selection
        ouia_select_widget.fill("second option")
        new_selection = ouia_select_widget.read()
        print(f"OUIA select new value: {new_selection}")

OUIA Safe State Management
==========================

OUIA components indicate their automation readiness with the ``data-ouia-safe`` attribute:

**Checking OUIA Safe States**

.. code-block:: python

    def check_ouia_safe_state(widget):
        """Check if OUIA widget is in safe state for automation."""
        try:
            safe_attr = browser.get_attribute(widget, "data-ouia-safe")

            # Convert string to boolean
            if safe_attr is None:
                return None  # No OUIA safe attribute

            return safe_attr.lower() == "true"
        except Exception:
            return None

    def wait_for_ouia_safe(widget, timeout=10):
        """Wait for OUIA widget to become safe for automation."""
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            if check_ouia_safe_state(widget):
                return True
            time.sleep(0.1)

        return False

    # Check safe states of OUIA widgets
    widgets_to_check = [
        ("Button", ouia_widgets.ouia_button),
        ("Select", ouia_widgets.ouia_select),
        ("TextInput", ouia_widgets.ouia_text_input),
        ("Checkbox", ouia_widgets.ouia_checkbox),
    ]

    for widget_name, widget in widgets_to_check:
        safe_state = check_ouia_safe_state(widget)
        print(f"{widget_name} safe state: {safe_state}")

        if safe_state is False:
            print(f"  Waiting for {widget_name} to become safe...")
            if wait_for_ouia_safe(widget):
                print(f"  ✓ {widget_name} is now safe for automation")
            else:
                print(f"  ⚠ {widget_name} did not become safe within timeout")

**OUIA-Aware Automation**

.. code-block:: python

    def safe_ouia_interaction(widget, operation, *args, **kwargs):
        """Perform automation operations only when OUIA widget is safe."""
        # First check if widget is displayed
        if not widget.is_displayed:
            return {'success': False, 'error': 'Widget not displayed'}

        # Check OUIA safe state
        safe_state = check_ouia_safe_state(widget)
        if safe_state is False:
            # Try waiting for safe state
            if not wait_for_ouia_safe(widget, timeout=5):
                return {'success': False, 'error': 'Widget not safe for automation'}

        # Proceed with operation
        try:
            if operation == 'click':
                browser.click(widget)
                return {'success': True, 'action': 'clicked'}
            elif operation == 'fill' and hasattr(widget, 'fill'):
                result = widget.fill(*args, **kwargs)
                return {'success': True, 'changed': result, 'value': widget.read()}
            elif operation == 'read':
                if hasattr(widget, 'read'):
                    value = widget.read()
                else:
                    value = browser.text(widget)
                return {'success': True, 'value': value}
            else:
                return {'success': False, 'error': f'Unknown operation: {operation}'}
        except Exception as e:
            return {'success': False, 'error': f'{type(e).__name__}: {e}'}

    # Test safe OUIA interactions
    button_result = safe_ouia_interaction(ouia_widgets.ouia_button, 'click')
    print(f"OUIA button click result: {button_result}")

    if specialized_ouia.ouia_input.is_displayed:
        input_result = safe_ouia_interaction(specialized_ouia.ouia_input, 'fill', 'Safe OUIA input')
        print(f"OUIA input fill result: {input_result}")

Advanced OUIA Patterns
======================

Handle complex OUIA scenarios and dynamic components:

**OUIA Component Discovery**

.. code-block:: python

    def discover_ouia_components(browser, root_element=None):
        """Discover all OUIA components on the page or within a root element."""
        if root_element:
            ouia_elements = browser.elements("[data-ouia-component-type]", parent=root_element)
        else:
            ouia_elements = browser.elements("[data-ouia-component-type]")

        components = []
        for element in ouia_elements:
            component_type = browser.get_attribute(element, "data-ouia-component-type")
            component_id = browser.get_attribute(element, "data-ouia-component-id")
            safe_state = browser.get_attribute(element, "data-ouia-safe")

            components.append({
                'element': element,
                'type': component_type,
                'id': component_id,
                'safe': safe_state,
                'displayed': browser.is_displayed(element),
                'enabled': browser.is_enabled(element) if browser.is_enabled(element) is not None else True
            })

        return components

    # Discover all OUIA components on the page
    all_ouia_components = discover_ouia_components(browser)

    print(f"Found {len(all_ouia_components)} OUIA components:")
    for i, component in enumerate(all_ouia_components):
        print(f"  {i+1}. Type: {component['type']}, ID: {component['id']}")
        print(f"     Safe: {component['safe']}, Displayed: {component['displayed']}")

**Dynamic OUIA Widget Creation**

.. code-block:: python

    def create_ouia_widget_dynamically(component_type, component_id):
        """Dynamically create OUIA widget based on component type."""

        # Map component types to appropriate widget classes
        widget_map = {
            'TextInput': OUIATextInput,
            'CheckBox': OUIACheckbox,
            'Text': OUIAText,
            'Button': OUIAGenericWidget,
            'PF/Button': OUIAGenericWidget,
            'PF/Select': OUIAGenericWidget,
        }

        widget_class = widget_map.get(component_type, OUIAGenericWidget)

        if widget_class == OUIAGenericWidget:
            return widget_class(component_id=component_id, component_type=component_type)
        else:
            return widget_class(component_id=component_id)

    # Create widgets dynamically based on discovered components
    dynamic_widgets = {}

    for component in all_ouia_components:
        if component['displayed'] and component['id']:
            widget_name = f"dynamic_{component['type'].replace('/', '_').lower()}"
            widget = create_ouia_widget_dynamically(component['type'], component['id'])

            # Initialize widget with browser context
            widget.parent = browser
            widget.parent_view = None

            dynamic_widgets[widget_name] = widget

    print(f"Created {len(dynamic_widgets)} dynamic OUIA widgets:")
    for name, widget in dynamic_widgets.items():
        print(f"  {name}: {type(widget).__name__}")

**OUIA Form Automation**

.. code-block:: python

    class OUIAFormView(OUIAGenericView):
        """Complete OUIA form with all widget types."""
        ROOT = "[data-ouia-component-type='TestView']"

        # Form inputs
        text_input = OUIATextInput(component_id="unique_id")
        checkbox = OUIACheckbox(component_id="unique_id")

        # Using generic widgets for complex controls
        select_widget = OUIAGenericWidget(component_id="some_id", component_type="PF/Select")
        submit_button = OUIAGenericWidget(component_id="This is a button", component_type="PF/Button")

        # Display elements
        status_text = OUIAText(component_id="unique_id", component_type="Text")

    def ouia_form_automation_workflow():
        """Complete OUIA form automation workflow."""
        form = OUIAFormView(browser)
        results = {}

        print("=== OUIA Form Automation Workflow ===")

        # Step 1: Verify all OUIA widgets are safe and ready
        widgets_to_verify = [
            ('text_input', form.text_input),
            ('checkbox', form.checkbox),
            ('select_widget', form.select_widget),
            ('submit_button', form.submit_button),
        ]

        ready_widgets = []
        for name, widget in widgets_to_verify:
            if widget.is_displayed:
                safe_state = check_ouia_safe_state(widget)
                if safe_state is not False:  # True or None (no safe attribute)
                    ready_widgets.append((name, widget))
                    results[f"{name}_ready"] = True
                else:
                    results[f"{name}_ready"] = False
                    print(f"⚠ {name} is not safe for automation")

        # Step 2: Fill form inputs
        for name, widget in ready_widgets:
            if name == 'text_input':
                result = safe_ouia_interaction(widget, 'fill', 'OUIA form data')
                results[f"{name}_fill"] = result
            elif name == 'checkbox':
                result = safe_ouia_interaction(widget, 'fill', True)
                results[f"{name}_fill"] = result
            elif name == 'select_widget':
                # For select widgets, you might need to handle differently
                try:
                    from widgetastic.widget import Select
                    select_wrapper = Select(locator=widget)
                    select_wrapper.parent = browser
                    select_wrapper.fill("second option")
                    results[f"{name}_fill"] = {'success': True}
                except Exception as e:
                    results[f"{name}_fill"] = {'success': False, 'error': str(e)}

        # Step 3: Submit form
        if ('submit_button', form.submit_button) in ready_widgets:
            submit_result = safe_ouia_interaction(form.submit_button, 'click')
            results['form_submit'] = submit_result

        # Step 4: Read status
        if form.status_text.is_displayed:
            status_result = safe_ouia_interaction(form.status_text, 'read')
            results['status_text'] = status_result

        return results

    # Execute OUIA form workflow
    form_results = ouia_form_automation_workflow()
    print("\n=== OUIA Form Results ===")
    for key, value in form_results.items():
        print(f"{key}: {value}")

OUIA Integration with Standard Widgets
======================================

Combine OUIA attributes with standard Widgetastic widgets:

**Hybrid OUIA/Standard Approach**

.. code-block:: python

    from widgetastic.widget import View, Text, TextInput, Select, Checkbox

    class HybridOUIAView(View):
        """Mix OUIA and standard widgets based on what's available."""

        # Use OUIA when available
        ouia_button = OUIAGenericWidget(component_id="This is a button")
        ouia_input = OUIATextInput(component_id="unique_id")

        # Fall back to standard locators when OUIA not available
        standard_input = TextInput(id="input")
        standard_checkbox = Checkbox(id="input2")

        # Hybrid approach: OUIA element as locator for standard widget
        ouia_select_as_standard = Select(
            locator='[data-ouia-component-id="some_id"][data-ouia-component-type="PF/Select"]'
        )

    hybrid_view = HybridOUIAView(browser)

    def demonstrate_hybrid_approach():
        """Demonstrate mixing OUIA and standard widgets."""
        results = {}

        # OUIA widgets
        if hybrid_view.ouia_button.is_displayed:
            results['ouia_button'] = safe_ouia_interaction(hybrid_view.ouia_button, 'click')

        if hybrid_view.ouia_input.is_displayed:
            results['ouia_input'] = safe_ouia_interaction(hybrid_view.ouia_input, 'fill', 'Hybrid data')

        # Standard widgets
        if hybrid_view.standard_input.is_displayed:
            hybrid_view.standard_input.fill("Standard widget data")
            results['standard_input'] = hybrid_view.standard_input.read()

        if hybrid_view.standard_checkbox.is_displayed:
            hybrid_view.standard_checkbox.fill(True)
            results['standard_checkbox'] = hybrid_view.standard_checkbox.read()

        # Hybrid OUIA-locator with standard widget
        if hybrid_view.ouia_select_as_standard.is_displayed:
            current_value = hybrid_view.ouia_select_as_standard.read()
            hybrid_view.ouia_select_as_standard.fill("second option")
            new_value = hybrid_view.ouia_select_as_standard.read()
            results['hybrid_select'] = {'from': current_value, 'to': new_value}

        return results

    hybrid_results = demonstrate_hybrid_approach()
    print("\n=== Hybrid OUIA/Standard Results ===")
    for key, value in hybrid_results.items():
        print(f"{key}: {value}")

OUIA Best Practices
===================

Guidelines for effective OUIA automation:

**OUIA Development Guidelines**

.. code-block:: python

    # 1. Prefer OUIA widgets when available
    class PreferOUIAWidgets(OUIAGenericView):
        # ✓ Good - Uses OUIA component ID
        submit_button = OUIAGenericWidget(component_id="submit-form-button")

        # ✗ Less ideal - CSS/XPath when OUIA available
        # submit_button = Text(id="submit-button")

    # 2. Use meaningful component IDs and types
    class MeaningfulOUIAWidgets(OUIAGenericView):
        # ✓ Good - Clear semantic meaning
        user_name_input = OUIATextInput(component_id="user-name-field")
        save_user_button = OUIAGenericWidget(component_id="save-user", component_type="PF/Button")

        # ✗ Less ideal - Generic or unclear IDs
        # generic_input = OUIATextInput(component_id="input1")

    # 3. Always check OUIA safe state for critical operations
    def safe_ouia_form_submission(view):
        """Safely submit OUIA form only when ready."""
        submit_button = view.submit_button

        # Wait for safe state before critical operation
        if not wait_for_ouia_safe(submit_button):
            raise Exception("Submit button not safe for automation")

        # Perform submission
        browser.click(submit_button)

        return True

    # 4. Combine OUIA with standard error handling
    def robust_ouia_interaction(widget, operation, **kwargs):
        """Robust OUIA interaction with comprehensive error handling."""
        try:
            # OUIA-specific checks
            if not widget.is_displayed:
                return {'success': False, 'error': 'Widget not displayed'}

            safe_state = check_ouia_safe_state(widget)
            if safe_state is False:
                if not wait_for_ouia_safe(widget, timeout=10):
                    return {'success': False, 'error': 'Widget not safe within timeout'}

            # Standard widget checks
            if hasattr(widget, 'is_enabled') and not widget.is_enabled:
                return {'success': False, 'error': 'Widget not enabled'}

            # Perform operation
            if operation == 'fill':
                if hasattr(widget, 'fill'):
                    result = widget.fill(kwargs.get('value'))
                    return {'success': True, 'changed': result}
                else:
                    return {'success': False, 'error': 'Widget not fillable'}
            elif operation == 'click':
                browser.click(widget)
                return {'success': True, 'action': 'clicked'}
            elif operation == 'read':
                if hasattr(widget, 'read'):
                    value = widget.read()
                else:
                    value = browser.text(widget)
                return {'success': True, 'value': value}

        except Exception as e:
            return {'success': False, 'error': f'{type(e).__name__}: {e}'}

**OUIA Testing Strategies**

.. code-block:: python

    def validate_ouia_compliance(browser, root_element=None):
        """Validate OUIA compliance of components on page."""
        components = discover_ouia_components(browser, root_element)
        compliance_report = {
            'total_components': len(components),
            'compliant': 0,
            'non_compliant': 0,
            'issues': []
        }

        for component in components:
            issues = []

            # Check required attributes
            if not component['type']:
                issues.append('Missing data-ouia-component-type')

            if not component['id']:
                issues.append('Missing data-ouia-component-id')

            # Check safe attribute format
            safe_attr = component['safe']
            if safe_attr and safe_attr not in ['true', 'false']:
                issues.append(f'Invalid data-ouia-safe value: {safe_attr}')

            if issues:
                compliance_report['non_compliant'] += 1
                compliance_report['issues'].append({
                    'type': component['type'],
                    'id': component['id'],
                    'issues': issues
                })
            else:
                compliance_report['compliant'] += 1

        return compliance_report

    # Validate OUIA compliance
    compliance = validate_ouia_compliance(browser)
    print("\n=== OUIA Compliance Report ===")
    print(f"Total components: {compliance['total_components']}")
    print(f"Compliant: {compliance['compliant']}")
    print(f"Non-compliant: {compliance['non_compliant']}")

    if compliance['issues']:
        print("\nIssues found:")
        for issue in compliance['issues']:
            print(f"  {issue['type']} ({issue['id']}): {', '.join(issue['issues'])}")

Final Cleanup
==============

.. code-block:: python

    try:
        context.close()
        browser_instance.close()
        playwright.stop()
    except Exception as e:
        print(f"Cleanup error: {e}")

Summary
=======

OUIA support in Widgetastic.core provides:

* **Standardized Locators**: Use component types and IDs instead of fragile selectors
* **Semantic Automation**: Widget types have clear automation intent
* **Safe State Management**: Coordinate testing with application readiness
* **Framework Independence**: Works across different UI frameworks
* **Hybrid Approach**: Combine with standard widgets as needed

Key takeaways:
* Use OUIA widgets when components have proper OUIA attributes
* Always check ``data-ouia-safe`` state for critical operations
* Combine OUIA with standard Widgetastic patterns for robust automation
* Validate OUIA compliance during development and testing
* Use meaningful component IDs and types for maintainable tests

This completes the OUIA tutorial. You can now leverage OUIA standards for more reliable and maintainable web automation with Widgetastic.core.
