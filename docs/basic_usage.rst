Basic usage
-----------

**ATTENTION!**: Read the :ref:`widgetastic-usage-guidelines` carefully before starting out.

This sample only represents simple UI interaction.

.. code-block:: python

    from selenium import webdriver
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput


    # Subclass the default browser, add product_version property, plug in the hooks ...
    class CustomBrowser(Browser):
        pass

    # Create a view that represents a page
    class MyView(View):
        a_text = Text(locator='.//h3[@id="title"]')
        an_input = TextInput(name='my_input')

        # Or a portion of it
        @View.nested  # not necessary but you need it if you need to keep things ordered
        class my_subview(View):
            # You can specify a root locator, then this view responds to is_displayed and can be
            # used as a parent for widget lookup
            ROOT = 'div#somediv'
            another_text = Text(locator='#h2')  # See "Automatic simple CSS locator detection"

    selenium = webdriver.Firefox()  # For example
    browser = CustomBrowser(selenium)

    # Now we have the widgetastic browser ready for work
    # Let's instantiate a view.
    a_view = MyView(browser)
    # ^^ you would typically come up with some way of integrating this in your framework.

    # The defined widgets now work as you would expect
    a_view.read()  # returns a recursive dictionary of values that all widgets provide via read()
    a_view.a_text.text  # Accesses the text
    # but the .text is widget-specific, so you might like to use just .read()
    a_view.fill({'an_input': 'foo'})  # Fills an_input with foo and returns boolean whether anything changed
    # Basically equivalent to:
    a_view.an_input.fill('foo')  # Since views just dispatch fill to the widgets based on the order
    a_view.an_input.is_displayed


Typically, you want to incorporate a system that would do the navigation (like
`navmazing <https://pypi.python.org/pypi/navmazing>`_ for example), as Widgetastic only facilitates
UI interactions.

An example of such integration is currently **TODO**, but it will eventually appear here once a PoC
for a different project will happen.
