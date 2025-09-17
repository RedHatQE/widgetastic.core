=============
Basic Example
=============

This comprehensive example demonstrates the most common widgetastic patterns through a realistic
web application automation scenario. We'll build a complete automation script step by step.

The Complete Example
====================

Let's automate a user registration and profile management workflow:

.. code-block:: python

    """
    Complete Widgetastic Example: User Registration and Profile Management

    This example demonstrates:
    - Form automation with validation
    - Navigation between pages
    - Data reading and verification
    - Error handling and debugging
    - Multiple widget types
    """

    import logging
    from playwright.sync_api import sync_playwright
    from widgetastic.browser import Browser
    from widgetastic.widget import (
        View, Text, TextInput, Button, Select, Checkbox, Table
    )
    from widgetastic.exceptions import NoSuchElementException

    # Configure logging to see what's happening
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(levelname)s - %(message)s')

    class CustomBrowser(Browser):
        """Enhanced browser with version info for advanced features."""

        @property
        def product_version(self):
            return "1.0.0"

    # ================================
    # STEP 1: Define Page Views
    # ================================

    class RegistrationView(View):
        """User registration form."""

        # Form fields
        first_name = TextInput("#firstName")
        last_name = TextInput("#lastName")
        email = TextInput("#email")
        password = TextInput("#password")
        confirm_password = TextInput("#confirmPassword")
        country = Select("#country")
        agree_terms = Checkbox("#agreeTerms")

        # Actions
        register_button = Button("#registerBtn")
        login_link = Button("a[href='/login']")

        # Feedback
        success_message = Text(".alert-success")
        error_message = Text(".alert-danger")

    class LoginView(View):
        """User login form."""

        email = TextInput("#loginEmail")
        password = TextInput("#loginPassword")
        remember_me = Checkbox("#rememberMe")
        login_button = Button("#loginBtn")
        forgot_password = Button("a[href='/forgot']")

        # Status messages
        welcome_message = Text(".welcome")
        error_message = Text(".login-error")

    class ProfileView(View):
        """User profile management."""

        # Display information
        welcome_text = Text("#welcomeUser")

        # Profile sections using nested views
        class personal_info(View):
            ROOT = "#personalInfo"

            display_name = Text(".display-name")
            email = Text(".email")
            member_since = Text(".member-since")

        class preferences(View):
            ROOT = "#userPreferences"

            theme = Select("#themeSelect")
            notifications = Checkbox("#emailNotifications")
            language = Select("#languageSelect")
            save_button = Button("#savePreferences")

        # Navigation
        logout_button = Button("#logoutBtn")
        edit_profile_button = Button("#editProfileBtn")

    # ================================
    # STEP 2: Automation Functions
    # ================================

    def register_new_user(browser, user_data):
        """Complete user registration workflow."""

        print(f"🔧 Starting registration for {user_data['email']}")

        # Navigate to registration page
        browser.goto("https://demo.widgetastic.com/register")  # Example URL

        # Create the registration view
        registration = RegistrationView(browser)

        # Verify we're on the right page
        if not registration.register_button.is_displayed:
            raise Exception("Registration page not loaded properly")

        # Fill the registration form
        print("📝 Filling registration form...")
        form_changed = registration.fill(user_data)
        print(f"Form data changed: {form_changed}")

        # Read back the form to verify (good practice)
        current_data = registration.read()
        print("📖 Current form data:")
        for field, value in current_data.items():
            if value and field != 'password':  # Don't log passwords
                print(f"  {field}: {value}")

        # Submit the form
        print("🚀 Submitting registration...")
        registration.register_button.click()

        # Check for success or errors
        try:
            if registration.success_message.is_displayed:
                print(f"✅ Registration successful: {registration.success_message.text}")
                return True
            elif registration.error_message.is_displayed:
                print(f"❌ Registration failed: {registration.error_message.text}")
                return False
        except NoSuchElementException:
            print("⚠️ No clear success/error message found")

        return False

    def login_user(browser, email, password):
        """User login workflow."""

        print(f"🔑 Logging in user: {email}")

        browser.goto("https://demo.widgetastic.com/login")

        login = LoginView(browser)

        # Fill login form
        login.fill({
            "email": email,
            "password": password,
            "remember_me": True  # Convenience feature
        })

        login.login_button.click()

        # Check login result
        try:
            if login.welcome_message.is_displayed:
                print(f"✅ Login successful: {login.welcome_message.text}")
                return True
            elif login.error_message.is_displayed:
                print(f"❌ Login failed: {login.error_message.text}")
                return False
        except NoSuchElementException:
            # Maybe we were redirected to profile page
            return True  # Assume success if no error message

        return False

    def manage_user_profile(browser):
        """User profile management workflow."""

        print("👤 Managing user profile...")

        browser.goto("https://demo.widgetastic.com/profile")

        profile = ProfileView(browser)

        # Read current profile information
        print("📋 Current profile information:")
        if profile.welcome_text.is_displayed:
            print(f"  Welcome: {profile.welcome_text.text}")

        if profile.personal_info.display_name.is_displayed:
            print(f"  Name: {profile.personal_info.display_name.text}")
            print(f"  Email: {profile.personal_info.email.text}")
            print(f"  Member since: {profile.personal_info.member_since.text}")

        # Update preferences
        print("⚙️ Updating user preferences...")
        preferences_data = {
            "theme": "dark",
            "notifications": True,
            "language": "en"
        }

        changed = profile.preferences.fill(preferences_data)
        if changed:
            print("Preferences updated, saving...")
            profile.preferences.save_button.click()
            print("✅ Preferences saved successfully")
        else:
            print("ℹ️ No preferences changes needed")

        # Read final preferences state
        final_prefs = profile.preferences.read()
        print("📖 Final preferences:")
        for pref, value in final_prefs.items():
            print(f"  {pref}: {value}")

    # ================================
    # STEP 3: Main Execution
    # ================================

    def main():
        """Main automation workflow."""

        print("🚀 Starting Widgetastic Automation Demo")
        print("=" * 50)

        # Sample user data
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "country": "United States",
            "agree_terms": True
        }

        with sync_playwright() as playwright:
            # Launch browser (visible for demo)
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # Create widgetastic browser
            wt_browser = CustomBrowser(page)

            try:
                # Execute the complete workflow
                print("Phase 1: User Registration")
                print("-" * 30)

                registration_success = register_new_user(wt_browser, user_data)

                if registration_success:
                    print("\nPhase 2: User Login")
                    print("-" * 30)

                    login_success = login_user(
                        wt_browser,
                        user_data["email"],
                        user_data["password"]
                    )

                    if login_success:
                        print("\nPhase 3: Profile Management")
                        print("-" * 30)

                        manage_user_profile(wt_browser)

                        print("\n🎉 All workflows completed successfully!")
                    else:
                        print("⚠️ Login failed, skipping profile management")
                else:
                    print("⚠️ Registration failed, skipping remaining steps")

            except Exception as e:
                print(f"💥 Automation failed with error: {e}")
                import traceback
                traceback.print_exc()

            finally:
                print("\n🧹 Cleaning up...")
                context.close()
                browser.close()
                print("✨ Demo completed!")

    if __name__ == "__main__":
        main()

Running the Example
====================

**Prerequisites**

.. code-block:: bash

    # Install dependencies
    pip install widgetastic.core
    playwright install chromium

    # Save the code as 'complete_example.py'
    python complete_example.py

**Expected Output**

.. code-block:: text

    🚀 Starting Widgetastic Automation Demo
    ==================================================
    Phase 1: User Registration
    ------------------------------
    🔧 Starting registration for john.doe@example.com
    📝 Filling registration form...
    Form data changed: True
    📖 Current form data:
      first_name: John
      last_name: Doe
      email: john.doe@example.com
      country: United States
      agree_terms: True
    🚀 Submitting registration...
    ✅ Registration successful: Account created successfully!

    Phase 2: User Login
    ------------------------------
    🔑 Logging in user: john.doe@example.com
    ✅ Login successful: Welcome back, John!

    Phase 3: Profile Management
    ------------------------------
    👤 Managing user profile...
    📋 Current profile information:
      Welcome: Welcome, John Doe!
      Name: John Doe
      Email: john.doe@example.com
      Member since: January 2024
    ⚙️ Updating user preferences...
    Preferences updated, saving...
    ✅ Preferences saved successfully

    🎉 All workflows completed successfully!

Key Learning Points
===================

**1. View Organization**

.. code-block:: python

    # Each page/section gets its own view class
    class RegistrationView(View):
        # Group related widgets logically
        first_name = TextInput("#firstName")
        register_button = Button("#registerBtn")

**2. Nested Views for Complex Pages**

.. code-block:: python

    class ProfileView(View):
        # Nested views for page sections
        class personal_info(View):
            ROOT = "#personalInfo"  # Scope widgets to this section
            display_name = Text(".display-name")

**3. Bulk Operations vs Individual Access**

.. code-block:: python

    # Bulk fill - efficient for forms
    view.fill({"field1": "value1", "field2": "value2"})

    # Individual access - for specific operations
    view.submit_button.click()

**4. Robust Error Handling**

.. code-block:: python

    try:
        if view.success_message.is_displayed:
            # Handle success case
    except NoSuchElementException:
        # Element not found, handle gracefully

**5. State Validation**

.. code-block:: python

    # Always verify form state
    current_data = view.read()

    # Check element states before interaction
    if button.is_displayed and button.is_enabled:
        button.click()

Customizing the Example
=======================

**Add Your Own Widgets**

.. code-block:: python

    class MyView(View):
        # Date picker
        birth_date = TextInput("#birthDate")

        # File upload
        avatar = FileInput("#avatarUpload")

        # Multi-select
        interests = Select("#interests")  # Can handle multiple selections

**Add Validation Logic**

.. code-block:: python

    def validate_registration_data(data):
        """Validate user data before submission."""
        errors = []

        if not data.get("email") or "@" not in data["email"]:
            errors.append("Invalid email address")

        if len(data.get("password", "")) < 8:
            errors.append("Password must be at least 8 characters")

        if data["password"] != data["confirm_password"]:
            errors.append("Passwords do not match")

        return errors

**Add Wait Strategies**

.. code-block:: python

    # Wait for elements to appear
    registration.success_message.wait_displayed(timeout="10s")

    # Wait for page transitions
    browser.page.wait_for_url("**/profile")

Common Adaptations
==================

**For React/Angular Apps**

.. code-block:: python

    # Handle dynamic content
    from widgetastic.utils import WaitFillViewStrategy

    class MyView(View):
        fill_strategy = WaitFillViewStrategy(wait_widget="5s")

**For Testing Frameworks**

.. code-block:: python

    import pytest

    class TestUserWorkflow:
        def test_complete_user_journey(self, browser):
            # Use the same view classes
            registration = RegistrationView(browser)
            # ... test assertions

**For Data-Driven Testing**

.. code-block:: python

    # Load test data from files
    import json

    with open("test_users.json") as f:
        test_users = json.load(f)

    for user in test_users:
        register_new_user(browser, user)

Next Steps
==========

Now that you've seen a complete example:

1. **Try It**: Run the code and modify it for your application
2. **Learn Patterns**: Check out :doc:`common-patterns` for more techniques
3. **Go Deeper**: Explore :doc:`../tutorials/index` for specific topics
4. **Build Your Own**: Apply these patterns to your own web applications

**Pro Tips**

- Start with simple views and add complexity gradually
- Use logging to understand what widgetastic is doing
- Test your views with different data sets
- Create reusable view components for common UI patterns
- Always handle both success and error cases
