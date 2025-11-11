"""View Batch Operations Example

This example demonstrates batch fill and read operations on views.
"""

from widgetastic.widget import View, TextInput, Checkbox


class NormalView(View):
    ROOT = "#normal_view_container"

    name = TextInput(id="normal_name")
    email = TextInput(id="normal_email")
    terms = Checkbox(id="normal_terms")


# Fill multiple fillable widgets at once
form = NormalView(browser)  # noqa: F821
form_data = {
    "name": "Foo Bar",
    "email": "foo.bar@example.com",
    "terms": True,
}

print(f"Filling form with: {form_data}")
form.fill(form_data)

# Read all fillable widgets in the view
current_values = form.read()
print(f"Current form values: {current_values}")
