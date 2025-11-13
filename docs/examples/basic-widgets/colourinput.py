"""ColourInput Widget Example

This example demonstrates HTML5 color picker operations.
"""

from widgetastic.widget import ColourInput

colour_input = ColourInput(browser, id="colourinput")  # noqa: F821

# Color operations
colour_input.fill("#ff0000")
print(f"After fill('#ff0000'), read returns: {colour_input.read()}")

# Set different colors with colour setter property
colour_input.colour = "#00ff00"
print(f"After setting colour to '#00ff00': {colour_input.colour}")
