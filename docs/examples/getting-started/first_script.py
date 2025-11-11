"""Complete First Script Example

This is a complete, working example that demonstrates core widgetastic concepts.
"""

# first_script.py
import json

from playwright.sync_api import sync_playwright
from widgetastic.browser import Browser
from widgetastic.widget import View, Text, TextInput, Checkbox


# Define your widgets and views i.e. Modeling of the testing page.
class DemoFormView(View):
    # Define the form elements as widgets
    custname = TextInput(locator='.//input[@name="custname"]')
    telephone = TextInput(locator='.//input[@name="custtel"]')
    email = TextInput(locator='.//input[@name="custemail"]')

    @View.nested
    class pizza_size(View):  # noqa
        small = Checkbox(locator=".//input[@value='small']")
        medium = Checkbox(locator=".//input[@value='medium']")
        large = Checkbox(locator=".//input[@value='large']")

    @View.nested
    class pizza_toppings(View):  # noqa
        bacon = Checkbox(locator=".//input[@value='bacon']")
        extra_cheese = Checkbox(locator=".//input[@value='cheese']")
        onion = Checkbox(locator=".//input[@value='onion']")
        mushroom = Checkbox(locator=".//input[@value='mushroom']")

    delivery_instructions = TextInput(locator='.//textarea[@name="comments"]')
    submit_order = Text(".//button[text()='Submit order']")

    response = Text(
        ".//body"
    )  # After submitting the form, we will get the response in the body of the page.


# Step: Main automation logic where actualy we are interacting with the page.
def main():
    with sync_playwright() as playwright:
        # Launch browser using Playwright
        browser = playwright.chromium.launch(headless=False)  # headless=False to see it in action
        # browser = playwright.chromium.launch(headless=False, slow_mo=500)  # uncomment this to see the slow motion in action.
        page = browser.new_page()

        # Create widgetastic browser instance
        wt_browser = Browser(page)

        # Navigate to the testing page.
        wt_browser.url = "https://httpbin.org/forms/post"

        # Initialize the view i.e. Model of the testing page.
        form_view = DemoFormView(wt_browser)

        # Fill individual fields
        form_view.custname.fill("John Doe")
        form_view.telephone.fill("1234567890")
        form_view.email.fill("john.doe@example.com")
        form_view.pizza_size.small.fill(True)
        form_view.pizza_toppings.bacon.fill(True)
        form_view.delivery_instructions.fill("Hello from Widgetastic!")

        form_view.submit_order.click()

        response_data = json.loads(form_view.response.text)
        print("Response data:")
        print(json.dumps(response_data, indent=4))
        # Close the browser
        browser.close()


if __name__ == "__main__":
    main()
