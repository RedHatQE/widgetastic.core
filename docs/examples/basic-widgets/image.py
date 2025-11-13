"""Image Widget Example

This example demonstrates accessing HTML image elements.
"""

from widgetastic.widget import Image

full_image = Image(browser, locator="#test-image-full")  # noqa: F821

# Check image visibility
print(f"Image is displayed: {full_image.is_displayed}")

# Accessing image attributes
print(f"Image src: {full_image.src}")
print(f"Image alt: {full_image.alt}")
print(f"Image title: {full_image.title}")
