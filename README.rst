================
widgetastic.core
================

.. image:: https://travis-ci.org/RedHatQE/widgetastic.core.svg?branch=master
    :target: https://travis-ci.org/RedHatQE/widgetastic.core

.. image:: https://coveralls.io/repos/github/RedHatQE/widgetastic.core/badge.svg?branch=master
    :target: https://coveralls.io/github/RedHatQE/widgetastic.core?branch=master

.. image:: https://readthedocs.org/projects/widgetasticcore/badge/?version=latest
    :target: http://widgetasticcore.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://www.quantifiedcode.com/api/v1/project/2f1c121257cc44acb1241aa640c4d266/badge.svg
  :target: https://www.quantifiedcode.com/app/project/2f1c121257cc44acb1241aa640c4d266
  :alt: Code issues

Widgetastic - Making testing of UIs **fantastic**.

Written originally by Milan Falesnik (mfalesni@redhat.com, http://www.falesnik.net/) and
other contributors since 2016.

Licensed under Apache license, Version 2.0

*WARNING:* Until this library reaches v1.0, the interfaces may change!

Introduction
------------

Widgetastic is a Python library designed to abstract out web UI widgets into a nice object-oriented
layer. This library includes the core classes and some basic widgets that are universal enough to
exist in this core repository.

Features
--------

- Individual interactive and non-interactive elements on the web pages are represented as widgets;
  that is, classes with defined behaviour. A good candidate for a widget might be something
  a like custom HTML button.
- Widgets are grouped on Views. A View descends from the Widget class but it is specifically designed
  to hold other widgets.
- All Widgets (including Views because they descend from them) have a read/fill interface useful for
  filling in forms etc. This interface works recursively.
- Views can be nested.
- Widgets defined on Views are read/filled in exact order that they were defined. The only exception
  to this default behaviour is for nested Views as there is limitation in the language. However, this
  can be worked around by using ``View.nested`` decorator on the nested View.
- Includes a wrapper around selenium functionality that tries to make the experience as hassle-free
  as possible including customizable hooks and built-in "JavaScript wait" code.
- Views can define their root locators and those are automatically honoured in the element lookup
  in the child Widgets.
- Supports `Parametrized views`_.
- Supports `Version picking`_.

Projects using widgetastic
--------------------------
- ManageIQ integration_tests: https://github.com/ManageIQ/integration_tests

Installation
------------

.. code-block:: bash

    pip install -U widgetastic.core


Contributing
------------
- Fork
- Clone
- Create a branch in your repository for your feature or fix
- Write the code, make sure you add unit tests.
- Run ``tox`` to ensure your change does not break other things
- Push
- Create a pull request

Basic usage
-----------

.. code-block:: python

    from selenium import webdriver
    from widgetastic.browser import Browser
    from widgetastic.widget import View, Text, TextInput


    # Subclass the default browser, add product_version property, plug in the hooks ...
    class CustomBrowser(Browser):
        pass

    # Create a view that represents a page
    class MyView(View):
        a_text = Text('.//h3[@id="title"]')
        an_input = TextInput(name='my_input')

        # Or a portion of it
        @View.nested  # not necessary but you need it if you need to keep things ordered
        class my_subview(View):
            # You can specify a root locator, then this view responds to is_displayed and can be
            # used as a parent for widget lookup
            ROOT = 'div#somediv'
            another_text = Text('#h2')  # Whatever takes a locator can automatically detect simple CSS locators

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


.. `Version picking`:

Version picking
------------------
By version picking you can tackle the challenge of widgets changing between versions.

In order to use this feature, you have to provide ``product_version`` property in the Browser which
should return the current version (ideally ``utils.Version``, otherwise you would need to redefine
the ``VERSION_CLASS`` on ``utils.VersionPick`` to point at you version handling class of choice)
of the product tested.

Then you can version pick widgets on a view for example:

.. code-block:: python

    from widgetastic.utils import Version, VersionPick
    from widgetastic.widget import View, TextInput

    class MyVerpickedView(View):
        hostname = VersionPick({
            # Version.lowest will match anything lower than 2.0.0 here.
            Version.lowest(): TextInput(name='hostname'),
            '2.0.0': TextInput(name='host_name'),
        })

When you instantiate the ``MyVerpickedView`` and then subsequently access ``hostname`` it will
automatically pick the right widget under the hood.

``VersionPick`` is not limited to resolving widgets and can be used for anything.

.. `Parametrized views`:

Parametrized views
------------------

If there is a repeated pattern on a page that differs only by eg. a title or an id, widgetastic has
a solution for that. You can use a ``ParametrizedView`` that takes an arbitrary number of parameters
and then you can use the parameters eg. in locators.

.. code-block:: python

    from widgetastic.utils import ParametrizedLocator, ParametrizedString
    from widgetastic.widget import ParametrizedView, TextInput

    class MyParametrizedView(ParametrizedView):
        # Defining one parameter
        PARAMETERS = ('thing_id', )
        # ParametrizedLocator coerces to a string upon access
        # It follows similar formatting syntax as .format
        # You can use the xpath quote filter as shown
        ROOT = ParametrizedLocator('.//thing[@id={thing_id|quote}]')

        # Widget definition *args and values of **kwargs (only the first level) are processed as well
        widget = TextInput(name=ParametrizedString('#asdf_{thing_id}'))

    # Then for invoking this:
    view = MyParametrizedView(browser, additional_context={'thing_id': 'foo'})

It is also possible to nest the parametrized view inside another view, parametrized or otherwise.
In this case the invocation of a nested view looks like a method call, instead of looking like a
property. The invocation supports passing the arguments both ways, positional and keyword based.

.. code-block:: python

    from widgetastic.utils import ParametrizedLocator, ParametrizedString
    from widgetastic.widget import ParametrizedView, TextInput, View

    class MyView(View):
        class this_is_parametrized(ParametrizedView):
            # Defining one parameter
            PARAMETERS = ('thing_id', )
            # ParametrizedLocator coerces to a string upon access
            # It follows similar formatting syntax as .format
            # You can use the xpath quote filter as shown
            ROOT = ParametrizedLocator('.//thing[@id={thing_id|quote}]')

            # Widget definition *args and values of **kwargs (only the first level) are processed as well
            the_widget = TextInput(name=ParametrizedString('#asdf_{thing_id}'))

    # We create the root view
    view = MyView(browser)
    # Now if it was an ordinary nested view, view.this_is_parametrized.the_widget would give us the
    # nested view instance directly and then the the_widget widget. But this is a parametrized view
    # and it will give us an intermediate object whose task is to collect the parameters upon
    # calling and then pass them through into the real view object.
    # This example will be invoking the parametrized view with the exactly same param like the
    # previous example:
    view.this_is_parametrized('foo')
    # So, when we have that view, you can use it as you are used to
    view.this_is_parametrized('foo').the_widget.do_something()
    # Or with keyword params
    view.this_is_parametrized(thing_id='foo').the_widget.do_something()
