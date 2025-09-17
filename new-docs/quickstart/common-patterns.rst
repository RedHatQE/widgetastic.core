===============
Common Patterns
===============

This guide covers the most frequently used widgetastic patterns. Master these and you'll handle 90% of automation scenarios efficiently.

Form Automation Patterns
=========================

**Pattern 1: Simple Form Fill**

.. code-block:: python

    from widgetastic.widget import View, TextInput, Button, Checkbox

    class ContactForm(View):
        name = TextInput("#name")
        email = TextInput("#email")
        message = TextInput("#message")
        subscribe = Checkbox("#newsletter")
        submit = Button("#submit")

    # Usage
    form = ContactForm(browser)
    form.fill({
        "name": "John Doe",
        "email": "john@example.com",
        "message": "Hello there!",
        "subscribe": True
    })
    form.submit.click()

**Pattern 2: Conditional Form Fields**

.. code-block:: python

    class RegistrationForm(View):
        user_type = Select("#userType")
        email = TextInput("#email")
        password = TextInput("#password")

        # Conditional fields
        company_name = TextInput("#companyName")  # Only for business users
        personal_code = TextInput("#personalCode")  # Only for personal users

    def smart_fill(form, user_data):
        """Fill form intelligently based on user type."""

        # Fill basic fields first
        form.fill({
            "user_type": user_data["type"],
            "email": user_data["email"],
            "password": user_data["password"]
        })

        # Fill conditional fields based on selection
        if user_data["type"] == "business":
            if form.company_name.is_displayed:
                form.company_name.fill(user_data["company"])
        elif user_data["type"] == "personal":
            if form.personal_code.is_displayed:
                form.personal_code.fill(user_data["code"])

**Pattern 3: Form Validation Handling**

.. code-block:: python

    class ValidatedForm(View):
        email = TextInput("#email")
        password = TextInput("#password")
        submit = Button("#submit")

        # Validation messages
        email_error = Text("#email-error")
        password_error = Text("#password-error")
        general_error = Text(".alert-danger")
        success_message = Text(".alert-success")

    def submit_with_validation(form, data):
        """Submit form and handle validation errors."""

        form.fill(data)
        form.submit.click()

        # Check for field-specific errors
        errors = {}
        if form.email_error.is_displayed:
            errors["email"] = form.email_error.text
        if form.password_error.is_displayed:
            errors["password"] = form.password_error.text
        if form.general_error.is_displayed:
            errors["general"] = form.general_error.text

        if errors:
            return False, errors

        # Check for success
        if form.success_message.is_displayed:
            return True, form.success_message.text

        return True, "Form submitted successfully"

Data Extraction Patterns
=========================

**Pattern 1: Table Data Extraction**

.. code-block:: python

    from widgetastic.widget import Table

    class DataTable(View):
        users_table = Table("#users-table")

        # Pagination controls
        next_page = Button(".pagination .next")
        page_info = Text(".pagination .info")

    def extract_all_table_data(view):
        """Extract data from paginated table."""

        all_data = []
        page = 1

        while True:
            print(f"Extracting page {page}...")

            # Get current page data
            page_data = view.users_table.read()
            all_data.extend(page_data if isinstance(page_data, list) else [page_data])

            # Check if there's a next page
            if not view.next_page.is_displayed or not view.next_page.is_enabled:
                break

            view.next_page.click()
            page += 1

            # Wait for page to load
            view.users_table.wait_displayed()

        return all_data

**Pattern 2: Dynamic Content Extraction**

.. code-block:: python

    class DashboardView(View):
        # Stats that update in real-time
        total_users = Text("#total-users")
        active_sessions = Text("#active-sessions")
        system_status = Text("#system-status")

        # Dynamic lists
        recent_activities = Text(".activity-item")  # Multiple elements

    def monitor_dashboard(view, duration=60):
        """Monitor dashboard metrics over time."""

        import time

        metrics_history = []
        start_time = time.time()

        while time.time() - start_time < duration:
            # Capture current metrics
            metrics = {
                "timestamp": time.time(),
                "total_users": int(view.total_users.text),
                "active_sessions": int(view.active_sessions.text),
                "system_status": view.system_status.text
            }

            metrics_history.append(metrics)

            # Wait before next sample
            time.sleep(5)

        return metrics_history

**Pattern 3: Complex Data Structures**

.. code-block:: python

    class ProductCatalog(View):

        class product_card(ParametrizedView):
            PARAMETERS = ("product_id",)
            ROOT = ParametrizedLocator("[data-product-id='{product_id}']")

            name = Text(".product-name")
            price = Text(".product-price")
            rating = Text(".product-rating")
            availability = Text(".product-availability")
            image = Image(".product-image")

        search_results = Text(".search-results .product-item")

    def extract_product_catalog(view, search_term):
        """Extract structured product data."""

        # Search for products
        search_box = TextInput("#search")
        search_box.fill(search_term)

        # Wait for results
        view.search_results.wait_displayed()

        # Get all product IDs from search results
        product_elements = browser.elements(".product-item")
        product_ids = [browser.get_attribute("data-product-id", el) for el in product_elements]

        # Extract data for each product
        products = []
        for product_id in product_ids:
            product = view.product_card(product_id=product_id)
            products.append(product.read())

        return products

Navigation Patterns
===================

**Pattern 1: Multi-Step Workflows**

.. code-block:: python

    class CheckoutWorkflow:

        class cart_page(View):
            items_table = Table("#cart-items")
            total_price = Text("#total")
            proceed_button = Button("#proceed-checkout")

        class shipping_page(View):
            address = TextInput("#address")
            city = TextInput("#city")
            zip_code = TextInput("#zip")
            continue_button = Button("#continue")

        class payment_page(View):
            card_number = TextInput("#card-number")
            expiry = TextInput("#expiry")
            cvv = TextInput("#cvv")
            complete_button = Button("#complete-order")

        class confirmation_page(View):
            order_number = Text("#order-number")
            order_total = Text("#order-total")

    def complete_checkout(browser, checkout_data):
        """Complete multi-step checkout process."""

        workflow = CheckoutWorkflow()

        # Step 1: Review cart
        browser.goto("/cart")
        cart = workflow.cart_page(browser)

        cart_total = cart.total_price.text
        print(f"Cart total: {cart_total}")
        cart.proceed_button.click()

        # Step 2: Shipping information
        shipping = workflow.shipping_page(browser)
        shipping.fill(checkout_data["shipping"])
        shipping.continue_button.click()

        # Step 3: Payment
        payment = workflow.payment_page(browser)
        payment.fill(checkout_data["payment"])
        payment.complete_button.click()

        # Step 4: Confirmation
        confirmation = workflow.confirmation_page(browser)
        confirmation.order_number.wait_displayed()

        return {
            "order_number": confirmation.order_number.text,
            "total": confirmation.order_total.text
        }

**Pattern 2: Menu Navigation**

.. code-block:: python

    class MainNavigation(View):
        # Top-level menu items
        products_menu = Button("#nav-products")
        services_menu = Button("#nav-services")
        support_menu = Button("#nav-support")

        # Dropdown submenus (appear on hover)
        class products_submenu(View):
            ROOT = "#products-dropdown"

            laptops = Button("a[href='/laptops']")
            desktops = Button("a[href='/desktops']")
            accessories = Button("a[href='/accessories']")

    def navigate_to_product_category(nav, category):
        """Navigate through dropdown menus."""

        # Hover over main menu to show dropdown
        nav.products_menu.hover()

        # Wait for submenu to appear
        nav.products_submenu.laptops.wait_displayed()

        # Click on specific category
        if category == "laptops":
            nav.products_submenu.laptops.click()
        elif category == "desktops":
            nav.products_submenu.desktops.click()
        # ... etc

**Pattern 3: Breadcrumb Navigation**

.. code-block:: python

    class BreadcrumbNavigation(View):
        breadcrumb_items = Text(".breadcrumb .item")  # Multiple elements

    def get_current_path(nav):
        """Extract current navigation path."""

        # Get all breadcrumb elements
        items = browser.elements(".breadcrumb .item")
        return [browser.text(item) for item in items]

    def navigate_up_one_level(nav):
        """Go up one level in navigation."""

        items = browser.elements(".breadcrumb .item a")  # Clickable items only
        if len(items) > 1:
            # Click the second-to-last item (parent)
            items[-2].click()

Wait and Timing Patterns
========================

**Pattern 1: Smart Waiting**

.. code-block:: python

    from widgetastic.exceptions import NoSuchElementException

    def wait_for_page_load(view, indicator_widget, timeout=10):
        """Wait for page to load using a loading indicator."""

        try:
            # Wait for loading indicator to appear
            indicator_widget.wait_displayed(timeout="2s")
            print("Loading indicator appeared...")

            # Wait for loading indicator to disappear
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not indicator_widget.is_displayed:
                    print("Page loaded successfully!")
                    return True
                time.sleep(0.5)

        except NoSuchElementException:
            # No loading indicator, assume page is ready
            pass

        return False

**Pattern 2: Content Change Detection**

.. code-block:: python

    def wait_for_content_change(widget, timeout=10):
        """Wait for widget content to change."""

        initial_content = widget.text
        start_time = time.time()

        while time.time() - start_time < timeout:
            current_content = widget.text
            if current_content != initial_content:
                return current_content
            time.sleep(0.5)

        raise TimeoutError(f"Content did not change within {timeout} seconds")

**Pattern 3: Batch Operations with Delays**

.. code-block:: python

    def process_items_with_delay(items_list, process_func, delay=1.0):
        """Process multiple items with delays to avoid rate limiting."""

        results = []

        for i, item in enumerate(items_list):
            print(f"Processing item {i+1}/{len(items_list)}: {item}")

            try:
                result = process_func(item)
                results.append(result)

                # Add delay between operations
                if i < len(items_list) - 1:  # Don't delay after last item
                    time.sleep(delay)

            except Exception as e:
                print(f"Error processing {item}: {e}")
                results.append(None)

        return results

Error Handling Patterns
=======================

**Pattern 1: Graceful Degradation**

.. code-block:: python

    def safe_widget_operation(widget, operation, default=None):
        """Safely perform widget operations with fallbacks."""

        try:
            if hasattr(widget, operation):
                return getattr(widget, operation)()
            else:
                print(f"Widget {widget} doesn't support {operation}")
                return default

        except NoSuchElementException:
            print(f"Widget {widget} not found")
            return default

        except Exception as e:
            print(f"Operation {operation} failed: {e}")
            return default

    # Usage
    text_content = safe_widget_operation(widget, 'text', default="N/A")
    is_visible = safe_widget_operation(widget, 'is_displayed', default=False)

**Pattern 2: Retry Logic**

.. code-block:: python

    def retry_operation(operation, max_attempts=3, delay=1.0):
        """Retry an operation with exponential backoff."""

        for attempt in range(max_attempts):
            try:
                return operation()

            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e  # Re-raise on final attempt

                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"Attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

    # Usage
    def click_submit():
        form.submit_button.click()

    retry_operation(click_submit, max_attempts=3)

**Pattern 3: Context Managers for Cleanup**

.. code-block:: python

    from contextlib import contextmanager

    @contextmanager
    def modal_dialog(view, trigger_button):
        """Context manager for modal dialog operations."""

        # Open modal
        trigger_button.click()
        modal = view.modal_dialog
        modal.wait_displayed()

        try:
            yield modal
        finally:
            # Always close modal, even if operation fails
            try:
                if modal.close_button.is_displayed:
                    modal.close_button.click()
            except:
                # Force close with Escape key if button fails
                browser.page.keyboard.press("Escape")

    # Usage
    with modal_dialog(view, view.open_settings_button) as modal:
        modal.theme_select.fill("dark")
        modal.save_button.click()

Testing Integration Patterns
============================

**Pattern 1: Page Object Model**

.. code-block:: python

    class BasePage(View):
        """Common elements for all pages."""

        header = HeaderView()
        footer = FooterView()
        loading_spinner = Text(".loading-spinner")

        def wait_for_page_ready(self):
            """Wait for page to be fully loaded."""
            try:
                # Wait for loading spinner to disappear
                if self.loading_spinner.is_displayed:
                    self.loading_spinner.wait_not_displayed(timeout="10s")
            except NoSuchElementException:
                pass  # No spinner, page probably ready

    class LoginPage(BasePage):
        ROOT = "#login-page"

        username = TextInput("#username")
        password = TextInput("#password")
        login_button = Button("#login")
        error_message = Text(".error")

        def login(self, username, password):
            """Perform login operation."""
            self.wait_for_page_ready()
            self.fill({"username": username, "password": password})
            self.login_button.click()

            if self.error_message.is_displayed:
                return False, self.error_message.text
            return True, "Login successful"

**Pattern 2: Test Data Management**

.. code-block:: python

    class TestDataFactory:
        """Factory for generating test data."""

        @staticmethod
        def create_user(user_type="standard"):
            """Create test user data."""

            base_data = {
                "first_name": "Test",
                "last_name": "User",
                "email": f"test.user+{int(time.time())}@example.com"
            }

            if user_type == "admin":
                base_data.update({
                    "role": "administrator",
                    "permissions": "all"
                })
            elif user_type == "premium":
                base_data.update({
                    "subscription": "premium",
                    "features": ["advanced_analytics", "priority_support"]
                })

            return base_data

    # Usage in tests
    def test_user_registration():
        user_data = TestDataFactory.create_user("premium")
        registration = RegistrationView(browser)
        success = registration.register(user_data)
        assert success

Next Steps
==========

These patterns form the foundation of effective widgetastic automation. To continue learning:

1. **Practice**: Implement these patterns in your own applications
2. **Combine**: Mix and match patterns for complex scenarios
3. **Extend**: Create your own patterns based on your specific needs
4. **Share**: Contribute patterns back to the community

**Advanced Topics to Explore**

* :doc:`../tutorials/advanced-widgets` - Complex widget creation
* :doc:`../tutorials/version-picking` - Handling application evolution
* :doc:`../tutorials/custom-widgets` - Build your own widgets
* :doc:`../tutorials/index` - Complete tutorial collection

Remember: Good automation is not just about making things work, but making them maintainable, reliable, and easy to understand!
