========================
Fill Strategies Tutorial
========================

This tutorial demonstrates comprehensive fill strategies in Widgetastic.core using examples from ``testing_page.html``. You'll learn to handle complex form filling scenarios, batch operations, and advanced fill patterns.

.. note::
   **Time Required**: 40 minutes
   **Prerequisites**: Basic and advanced widgets tutorials
   **Test Pages Used**: ``testing/html/testing_page.html``

Learning Objectives
===================

By completing this tutorial, you will:

* ✅ Master different fill strategies and patterns
* ✅ Handle complex form validation and error scenarios
* ✅ Implement batch fill operations efficiently
* ✅ Use conditional and dynamic fill strategies
* ✅ Handle fill strategy optimization and performance

Understanding Fill Operations
=============================

Fill operations in Widgetastic are the primary way to input data into web forms. The framework provides several strategies:

**Fill Operation Types**
* **Direct Fill**: Direct value assignment to widgets
* **Conditional Fill**: Fill based on current state or conditions
* **Batch Fill**: Fill multiple widgets in a single operation
* **Strategy Fill**: Use different fill methods based on widget type
* **Validation Fill**: Fill with validation and error handling

Setting Up Fill Strategy Environment
====================================

.. code-block:: python

    from pathlib import Path
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput, Checkbox, Select
    from widgetastic.utils import Fillable, FillContext

    def setup_fill_browser():
        """Setup browser with testing page for fill strategies."""
        test_page_path = Path("testing/html/testing_page.html").resolve()
        test_page_url = test_page_path.as_uri()

        p = sync_playwright().start()
        browser_instance = p.chromium.launch(headless=False)
        context = browser_instance.new_context()
        page = context.new_page()
        browser = Browser(page)

        browser.goto(test_page_url)

        return browser, p, browser_instance, context

    browser, playwright, browser_instance, context = setup_fill_browser()

Basic Fill Strategies
=====================

Start with fundamental fill patterns using the testing page widgets:

**Simple Fill Operations**

.. code-block:: python

    class BasicFillForm(View):
        # Basic form inputs from testing page
        text_input = TextInput(id="input")
        paste_input = TextInput(id="input_paste")
        number_input = TextInput(id="input_number")

        # Form checkboxes
        main_checkbox = Checkbox(id="input2")

        # Form inputs by name
        form_input1 = TextInput(name="input1")

    basic_form = BasicFillForm(browser)

    # Strategy 1: Individual fill operations
    def individual_fill_strategy():
        """Fill widgets one by one with individual operations."""
        results = {}

        # Fill text inputs
        changed = basic_form.text_input.fill("individual_value")
        results['text_input'] = {'changed': changed, 'value': basic_form.text_input.read()}

        changed = basic_form.number_input.fill("42")
        results['number_input'] = {'changed': changed, 'value': basic_form.number_input.read()}

        # Fill checkbox
        changed = basic_form.main_checkbox.fill(True)
        results['main_checkbox'] = {'changed': changed, 'value': basic_form.main_checkbox.read()}

        return results

    individual_results = individual_fill_strategy()
    print("=== Individual Fill Results ===")
    for widget, result in individual_results.items():
        print(f"{widget}: Changed={result['changed']}, Value={result['value']}")

**Batch Fill Operations**

.. code-block:: python

    # Strategy 2: Batch fill using View.fill()
    def batch_fill_strategy():
        """Fill multiple widgets in a single batch operation."""
        fill_data = {
            'text_input': 'batch_text_value',
            'paste_input': 'batch_paste_value',
            'number_input': '99',
            'main_checkbox': True,
            'form_input1': 'batch_form_value'
        }

        # Batch fill - returns dictionary of what changed
        changed_widgets = basic_form.fill(fill_data)

        # Read back all values
        current_data = basic_form.read()

        return {
            'changed_widgets': changed_widgets,
            'current_values': current_data
        }

    batch_results = batch_fill_strategy()
    print("\n=== Batch Fill Results ===")
    print(f"Changed widgets: {batch_results['changed_widgets']}")
    print(f"Current values: {batch_results['current_values']}")

**Conditional Fill Strategy**

.. code-block:: python

    # Strategy 3: Conditional fill based on current state
    def conditional_fill_strategy():
        """Fill widgets only when certain conditions are met."""
        results = {}

        # Only fill if current value is empty or different
        current_text = basic_form.text_input.read()
        if not current_text or current_text != "conditional_target":
            changed = basic_form.text_input.fill("conditional_target")
            results['text_input'] = f"Filled (was '{current_text}')"
        else:
            results['text_input'] = "Skipped (already correct value)"

        # Only check checkbox if unchecked
        current_checkbox = basic_form.main_checkbox.read()
        if not current_checkbox:
            basic_form.main_checkbox.fill(True)
            results['main_checkbox'] = "Checked (was unchecked)"
        else:
            results['main_checkbox'] = "Skipped (already checked)"

        # Fill number input only if enabled
        if basic_form.number_input.is_enabled:
            basic_form.number_input.fill("123")
            results['number_input'] = "Filled (widget enabled)"
        else:
            results['number_input'] = "Skipped (widget disabled)"

        return results

    conditional_results = conditional_fill_strategy()
    print("\n=== Conditional Fill Results ===")
    for widget, result in conditional_results.items():
        print(f"{widget}: {result}")

Advanced Fill Patterns
======================

Handle complex fill scenarios with validation and error handling:

**Fill with Validation**

.. code-block:: python

    class ValidatedFillForm(View):
        text_input = TextInput(id="input")
        number_input = TextInput(id="input_number")
        main_checkbox = Checkbox(id="input2")

        def validate_fill_data(self, data):
            """Validate data before filling."""
            errors = []

            # Validate text input
            if 'text_input' in data:
                value = data['text_input']
                if len(value) > 50:
                    errors.append("text_input: Value too long (max 50 chars)")
                if not value.strip():
                    errors.append("text_input: Value cannot be empty")

            # Validate number input
            if 'number_input' in data:
                try:
                    num_value = int(data['number_input'])
                    if num_value < 0:
                        errors.append("number_input: Value must be positive")
                except ValueError:
                    errors.append("number_input: Must be a valid number")

            return errors

        def safe_fill(self, data):
            """Fill with validation and error handling."""
            # Validate data
            validation_errors = self.validate_fill_data(data)
            if validation_errors:
                return {'success': False, 'errors': validation_errors}

            # Attempt fill with error handling
            try:
                results = {}

                for widget_name, value in data.items():
                    widget = getattr(self, widget_name, None)
                    if widget is None:
                        results[widget_name] = {'success': False, 'error': 'Widget not found'}
                        continue

                    if not widget.is_displayed:
                        results[widget_name] = {'success': False, 'error': 'Widget not displayed'}
                        continue

                    if hasattr(widget, 'is_enabled') and not widget.is_enabled:
                        results[widget_name] = {'success': False, 'error': 'Widget not enabled'}
                        continue

                    changed = widget.fill(value)
                    final_value = widget.read()

                    results[widget_name] = {
                        'success': True,
                        'changed': changed,
                        'final_value': final_value
                    }

                return {'success': True, 'results': results}

            except Exception as e:
                return {'success': False, 'error': f'Fill operation failed: {e}'}

    validated_form = ValidatedFillForm(browser)

    # Test validated fill
    test_data = {
        'text_input': 'validated_input',
        'number_input': '42',
        'main_checkbox': True
    }

    validated_results = validated_form.safe_fill(test_data)
    print("\n=== Validated Fill Results ===")
    if validated_results['success']:
        for widget, result in validated_results['results'].items():
            print(f"{widget}: Success={result['success']}, Changed={result.get('changed')}")
    else:
        print(f"Validation failed: {validated_results.get('errors', validated_results.get('error'))}")

**Custom Fill Strategies with Fillable Objects**

.. code-block:: python

    class CustomFillable(Fillable):
        """Custom fillable object that generates dynamic values."""

        def __init__(self, base_value, prefix="auto_"):
            self.base_value = base_value
            self.prefix = prefix
            self.counter = 0

        def as_fill_value(self):
            """Generate dynamic fill value."""
            self.counter += 1
            return f"{self.prefix}{self.base_value}_{self.counter}"

    class ConditionalFillable(Fillable):
        """Fillable that returns different values based on conditions."""

        def __init__(self, widget_name, browser):
            self.widget_name = widget_name
            self.browser = browser

        def as_fill_value(self):
            """Return value based on current page state."""
            # Example: different values based on current time
            import datetime
            hour = datetime.datetime.now().hour

            if hour < 12:
                return f"{self.widget_name}_morning_value"
            elif hour < 18:
                return f"{self.widget_name}_afternoon_value"
            else:
                return f"{self.widget_name}_evening_value"

    # Test custom fillable objects
    def test_custom_fillables():
        """Test various fillable object strategies."""
        results = {}

        # Auto-incrementing fillable
        auto_fill = CustomFillable("test", "auto_")

        # Fill multiple times to see increment
        for i in range(3):
            basic_form.text_input.fill(auto_fill)
            results[f'auto_fill_{i+1}'] = basic_form.text_input.read()

        # Conditional fillable
        conditional_fill = ConditionalFillable("time_based", browser)
        basic_form.paste_input.fill(conditional_fill)
        results['conditional_fill'] = basic_form.paste_input.read()

        return results

    fillable_results = test_custom_fillables()
    print("\n=== Custom Fillable Results ===")
    for key, value in fillable_results.items():
        print(f"{key}: {value}")

Complex Form Fill Scenarios
===========================

Handle real-world complex forms with multiple validation levels:

**Multi-Step Form Fill**

.. code-block:: python

    class MultiStepForm(View):
        # Step 1: Basic info
        text_input = TextInput(id="input")
        number_input = TextInput(id="input_number")

        # Step 2: Preferences
        main_checkbox = Checkbox(id="input2")

        # Step 3: Additional data
        form_input1 = TextInput(name="input1")

        def fill_step_by_step(self, data, validate_each_step=True):
            """Fill form in multiple steps with optional validation."""
            steps = [
                {
                    'name': 'basic_info',
                    'widgets': ['text_input', 'number_input'],
                    'validation': self._validate_basic_info
                },
                {
                    'name': 'preferences',
                    'widgets': ['main_checkbox'],
                    'validation': self._validate_preferences
                },
                {
                    'name': 'additional',
                    'widgets': ['form_input1'],
                    'validation': self._validate_additional
                }
            ]

            results = {}

            for step in steps:
                step_name = step['name']
                step_data = {k: v for k, v in data.items() if k in step['widgets']}

                if not step_data:
                    results[step_name] = {'skipped': True}
                    continue

                # Fill step data
                step_results = {}
                for widget_name, value in step_data.items():
                    widget = getattr(self, widget_name)
                    changed = widget.fill(value)
                    step_results[widget_name] = {
                        'changed': changed,
                        'value': widget.read()
                    }

                # Validate step if requested
                if validate_each_step and step.get('validation'):
                    validation_result = step['validation'](step_data)
                    step_results['validation'] = validation_result

                results[step_name] = step_results

                # Stop if validation failed
                if validate_each_step and step_results.get('validation', {}).get('success') is False:
                    results['stopped_at_step'] = step_name
                    break

            return results

        def _validate_basic_info(self, data):
            """Validate basic info step."""
            if 'text_input' in data and len(data['text_input']) < 3:
                return {'success': False, 'error': 'Text input too short'}

            if 'number_input' in data:
                try:
                    num = int(data['number_input'])
                    if num <= 0:
                        return {'success': False, 'error': 'Number must be positive'}
                except ValueError:
                    return {'success': False, 'error': 'Invalid number'}

            return {'success': True}

        def _validate_preferences(self, data):
            """Validate preferences step."""
            # Always valid for this example
            return {'success': True}

        def _validate_additional(self, data):
            """Validate additional data step."""
            if 'form_input1' in data and not data['form_input1'].strip():
                return {'success': False, 'error': 'Additional field cannot be empty'}

            return {'success': True}

    multi_step_form = MultiStepForm(browser)

    # Test multi-step fill
    multi_step_data = {
        'text_input': 'multi_step_text',
        'number_input': '100',
        'main_checkbox': True,
        'form_input1': 'additional_data'
    }

    multi_step_results = multi_step_form.fill_step_by_step(multi_step_data)
    print("\n=== Multi-Step Fill Results ===")
    for step, result in multi_step_results.items():
        print(f"{step}: {result}")

**Dynamic Fill Strategies**

.. code-block:: python

    class DynamicFillStrategy:
        """Dynamic fill strategy that adapts based on form state."""

        def __init__(self, view):
            self.view = view

        def analyze_form_state(self):
            """Analyze current form state to determine fill strategy."""
            state = {}

            # Check which widgets are available and enabled
            widgets = ['text_input', 'number_input', 'main_checkbox', 'form_input1']

            for widget_name in widgets:
                widget = getattr(self.view, widget_name, None)
                if widget:
                    state[widget_name] = {
                        'exists': True,
                        'displayed': widget.is_displayed,
                        'enabled': getattr(widget, 'is_enabled', True),
                        'current_value': widget.read() if widget.is_displayed else None
                    }
                else:
                    state[widget_name] = {'exists': False}

            return state

        def determine_fill_strategy(self, data, current_state):
            """Determine the best fill strategy based on state."""
            strategy = {
                'method': 'batch',  # batch, individual, selective
                'widgets_to_fill': [],
                'skip_reason': {}
            }

            for widget_name, value in data.items():
                widget_state = current_state.get(widget_name, {})

                if not widget_state.get('exists'):
                    strategy['skip_reason'][widget_name] = 'Widget does not exist'
                    continue

                if not widget_state.get('displayed'):
                    strategy['skip_reason'][widget_name] = 'Widget not displayed'
                    continue

                if not widget_state.get('enabled'):
                    strategy['skip_reason'][widget_name] = 'Widget not enabled'
                    continue

                # Check if value is already set correctly
                current_value = widget_state.get('current_value')
                if current_value == value:
                    strategy['skip_reason'][widget_name] = 'Value already correct'
                    continue

                strategy['widgets_to_fill'].append(widget_name)

            # Determine method based on how many widgets to fill
            if len(strategy['widgets_to_fill']) == 1:
                strategy['method'] = 'individual'
            elif len(strategy['widgets_to_fill']) <= 3:
                strategy['method'] = 'batch'
            else:
                strategy['method'] = 'selective'

            return strategy

        def execute_fill_strategy(self, data, strategy):
            """Execute the determined fill strategy."""
            widgets_to_fill = {k: v for k, v in data.items()
                             if k in strategy['widgets_to_fill']}

            if strategy['method'] == 'batch':
                # Fill all widgets at once
                changed = self.view.fill(widgets_to_fill)
                return {
                    'method_used': 'batch',
                    'changed_widgets': changed,
                    'skipped': strategy['skip_reason']
                }

            elif strategy['method'] == 'individual':
                # Fill widgets one by one
                results = {}
                for widget_name, value in widgets_to_fill.items():
                    widget = getattr(self.view, widget_name)
                    changed = widget.fill(value)
                    results[widget_name] = {
                        'changed': changed,
                        'final_value': widget.read()
                    }

                return {
                    'method_used': 'individual',
                    'results': results,
                    'skipped': strategy['skip_reason']
                }

            elif strategy['method'] == 'selective':
                # Fill with error handling for each widget
                results = {}
                for widget_name, value in widgets_to_fill.items():
                    try:
                        widget = getattr(self.view, widget_name)
                        changed = widget.fill(value)
                        results[widget_name] = {
                            'success': True,
                            'changed': changed,
                            'final_value': widget.read()
                        }
                    except Exception as e:
                        results[widget_name] = {
                            'success': False,
                            'error': str(e)
                        }

                return {
                    'method_used': 'selective',
                    'results': results,
                    'skipped': strategy['skip_reason']
                }

    # Test dynamic fill strategy
    dynamic_strategy = DynamicFillStrategy(basic_form)

    dynamic_data = {
        'text_input': 'dynamic_text',
        'number_input': '999',
        'main_checkbox': False,
        'form_input1': 'dynamic_form'
    }

    # Analyze and execute
    current_state = dynamic_strategy.analyze_form_state()
    fill_strategy = dynamic_strategy.determine_fill_strategy(dynamic_data, current_state)
    dynamic_results = dynamic_strategy.execute_fill_strategy(dynamic_data, fill_strategy)

    print("\n=== Dynamic Fill Strategy Results ===")
    print(f"Method used: {dynamic_results['method_used']}")
    print(f"Results: {dynamic_results.get('results', dynamic_results.get('changed_widgets'))}")
    print(f"Skipped widgets: {dynamic_results['skipped']}")

Performance-Optimized Fill Strategies
====================================

Optimize fill operations for speed and reliability:

**Batch vs Individual Performance**

.. code-block:: python

    import time

    def measure_fill_performance():
        """Compare performance of different fill strategies."""
        test_data = {
            'text_input': 'perf_test',
            'number_input': '777',
            'main_checkbox': True,
            'form_input1': 'perf_form'
        }

        results = {}

        # Method 1: Individual fills
        start_time = time.time()
        for i in range(5):  # Multiple iterations
            basic_form.text_input.fill(f'individual_{i}')
            basic_form.number_input.fill(str(100 + i))
            basic_form.main_checkbox.fill(i % 2 == 0)
            basic_form.form_input1.fill(f'form_individual_{i}')
        individual_time = time.time() - start_time

        # Method 2: Batch fills
        start_time = time.time()
        for i in range(5):  # Multiple iterations
            batch_data = {
                'text_input': f'batch_{i}',
                'number_input': str(200 + i),
                'main_checkbox': i % 2 == 1,
                'form_input1': f'form_batch_{i}'
            }
            basic_form.fill(batch_data)
        batch_time = time.time() - start_time

        # Method 3: Selective fills (only changed values)
        start_time = time.time()
        last_values = basic_form.read()
        for i in range(5):
            new_data = {
                'text_input': f'selective_{i}',
                'number_input': str(300 + i),
                'main_checkbox': i % 2 == 0,
                'form_input1': f'form_selective_{i}'
            }

            # Only fill changed values
            for widget_name, new_value in new_data.items():
                if last_values.get(widget_name) != new_value:
                    widget = getattr(basic_form, widget_name)
                    widget.fill(new_value)

            last_values = basic_form.read()
        selective_time = time.time() - start_time

        return {
            'individual_time': individual_time,
            'batch_time': batch_time,
            'selective_time': selective_time,
            'winner': min([
                ('individual', individual_time),
                ('batch', batch_time),
                ('selective', selective_time)
            ], key=lambda x: x[1])
        }

    performance_results = measure_fill_performance()
    print("\n=== Fill Performance Comparison ===")
    print(f"Individual fills: {performance_results['individual_time']:.3f}s")
    print(f"Batch fills: {performance_results['batch_time']:.3f}s")
    print(f"Selective fills: {performance_results['selective_time']:.3f}s")
    print(f"Fastest method: {performance_results['winner'][0]} ({performance_results['winner'][1]:.3f}s)")

Best Practices for Fill Strategies
==================================

Guidelines for choosing and implementing fill strategies:

**Fill Strategy Decision Matrix**

.. code-block:: python

    class FillStrategyManager:
        """Manager for choosing optimal fill strategies."""

        @staticmethod
        def choose_strategy(form_complexity, data_size, validation_needs, performance_priority):
            """Choose optimal fill strategy based on requirements."""

            # Decision matrix
            if performance_priority == 'high':
                if data_size <= 3:
                    return 'individual'
                else:
                    return 'selective_batch'

            elif validation_needs == 'strict':
                return 'validated_individual'

            elif form_complexity == 'high':
                return 'multi_step'

            elif data_size > 10:
                return 'chunked_batch'

            else:
                return 'standard_batch'

        @staticmethod
        def get_strategy_implementation(strategy_name):
            """Get implementation details for chosen strategy."""
            strategies = {
                'individual': {
                    'description': 'Fill widgets one by one',
                    'pros': ['Fine control', 'Easy debugging', 'Good for small forms'],
                    'cons': ['Slower for large forms', 'More code'],
                    'use_when': 'Few widgets, need precise control'
                },
                'standard_batch': {
                    'description': 'Fill all widgets using View.fill()',
                    'pros': ['Fast', 'Clean code', 'Good for most cases'],
                    'cons': ['Less control', 'All-or-nothing'],
                    'use_when': 'Standard forms, no special requirements'
                },
                'selective_batch': {
                    'description': 'Only fill changed values',
                    'pros': ['Efficient', 'Avoids unnecessary operations'],
                    'cons': ['More complex', 'Requires state tracking'],
                    'use_when': 'Performance critical, large forms'
                },
                'validated_individual': {
                    'description': 'Fill with validation at each step',
                    'pros': ['Robust', 'Early error detection', 'Good UX'],
                    'cons': ['Slower', 'More complex code'],
                    'use_when': 'Critical forms, strict validation'
                },
                'multi_step': {
                    'description': 'Fill in logical steps with validation',
                    'pros': ['Mirrors user workflow', 'Progressive validation'],
                    'cons': ['Complex implementation', 'Slower'],
                    'use_when': 'Complex multi-step forms'
                },
                'chunked_batch': {
                    'description': 'Fill in chunks to avoid timeouts',
                    'pros': ['Handles large datasets', 'Memory efficient'],
                    'cons': ['Complex', 'Potential for partial failures'],
                    'use_when': 'Very large forms, bulk operations'
                }
            }

            return strategies.get(strategy_name, {'description': 'Unknown strategy'})

    # Example usage
    strategy_manager = FillStrategyManager()

    # Determine strategy for different scenarios
    scenarios = [
        {'complexity': 'low', 'size': 3, 'validation': 'basic', 'performance': 'medium'},
        {'complexity': 'high', 'size': 15, 'validation': 'strict', 'performance': 'high'},
        {'complexity': 'medium', 'size': 8, 'validation': 'basic', 'performance': 'low'}
    ]

    print("\n=== Fill Strategy Recommendations ===")
    for i, scenario in enumerate(scenarios, 1):
        strategy = strategy_manager.choose_strategy(
            scenario['complexity'],
            scenario['size'],
            scenario['validation'],
            scenario['performance']
        )

        details = strategy_manager.get_strategy_implementation(strategy)

        print(f"\nScenario {i}: {scenario}")
        print(f"Recommended strategy: {strategy}")
        print(f"Description: {details['description']}")
        print(f"Use when: {details.get('use_when', 'General purpose')}")

**Fill Strategy Best Practices Summary**

.. code-block:: python

    def fill_strategy_best_practices():
        """Summary of fill strategy best practices."""

        practices = {
            'General Guidelines': [
                'Use batch fills for standard forms (3+ widgets)',
                'Use individual fills for complex validation',
                'Always check widget state before filling',
                'Handle errors gracefully with try/catch',
                'Validate data before filling when possible'
            ],

            'Performance Optimization': [
                'Avoid unnecessary fills (check current value first)',
                'Use selective fills for large forms',
                'Batch similar operations together',
                'Consider chunking for very large datasets',
                'Profile different strategies for your use case'
            ],

            'Error Handling': [
                'Validate data format before filling',
                'Check widget existence and state',
                'Provide meaningful error messages',
                'Implement retry mechanisms for flaky elements',
                'Log fill operations for debugging'
            ],

            'Code Organization': [
                'Encapsulate fill logic in view methods',
                'Use fillable objects for dynamic data',
                'Create reusable fill strategies',
                'Document fill behavior and requirements',
                'Test fill operations thoroughly'
            ]
        }

        return practices

    best_practices = fill_strategy_best_practices()
    print("\n=== Fill Strategy Best Practices ===")
    for category, practices_list in best_practices.items():
        print(f"\n{category}:")
        for practice in practices_list:
            print(f"  • {practice}")

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

Fill strategies in Widgetastic.core provide:

* **Flexible Approaches**: Multiple strategies for different scenarios
* **Performance Optimization**: Batch operations and selective filling
* **Robust Validation**: Built-in and custom validation patterns
* **Error Handling**: Comprehensive error management and recovery
* **Scalability**: Strategies that work from simple forms to complex workflows

Key takeaways:
* Choose fill strategy based on form complexity, data size, and requirements
* Use batch operations for efficiency, individual operations for control
* Always validate data and handle errors gracefully
* Profile and optimize fill operations for your specific use cases
* Encapsulate fill logic for reusability and maintainability

This completes the fill strategies tutorial. You now have comprehensive knowledge of form filling patterns and can choose the right approach for any automation scenario.
