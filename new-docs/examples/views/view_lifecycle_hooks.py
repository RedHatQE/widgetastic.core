"""View Lifecycle Hooks Example

This example demonstrates using before_fill and after_fill hooks.
"""

from widgetastic.widget import View, TextInput, Checkbox


class FormView(View):
    ROOT = "#normal_view_container"
    name = TextInput(id="normal_name")
    email = TextInput(id="normal_email")
    terms = Checkbox(id="normal_terms")

    def before_fill(self, values):
        """Called right before filling starts."""
        # self.logger.info(f"About to fill form with: {values}")
        print(f"About to fill form with: {values}")

        # You can validate values, prepare the form, etc.
        # Return value is ignored

    def after_fill(self, was_change):
        """Called right after filling completes."""
        if was_change:
            # self.logger.info("Form was successfully filled with new values")
            print("Form was successfully filled with new values")
            # Could wait for form updates, verify changes, etc.
        else:
            # self.logger.debug("No changes were made to the form")
            print("No changes were made to the form")
        # Return value is ignored


form = FormView(browser)  # noqa: F821
form.fill({"name": "John", "email": "john@example.com", "terms": True})
# before_fill is called first, then widgets are filled, then after_fill is called

# Read all fillable widgets in the view
current_values = form.read()
print(current_values)
