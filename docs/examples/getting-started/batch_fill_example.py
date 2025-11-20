"""Batch Fill Example

This example demonstrates filling a form in a single operation.
This is a code snippet that assumes form_view is already created.
See first_script.py for the complete example.
"""

# We can fill the form at single shot. Widgetastic will fill the form in the order of the widgets.
# This example assumes form_view is already created (see first_script.py for full context)
data = {
    "custname": "John Doe",
    "telephone": "1234567890",
    "email": "john.doe@example.com",
    "pizza_size": {"small": True},
    "pizza_toppings": {"bacon": True},
    "delivery_instructions": "Hello from Widgetastic!",
}
# form_view.fill(data)  # Uncomment when form_view is available
