Internal structure of Widgetastic
=================================

Widgetastic consists of 2 main parts:

* `Selenium browser wrapper`_
* `Widget system`_

.. `Selenium browser wrapper`:

Selenium browser wrapper
========================

This part of the framework serves the purpose of simplifying the interactions with Selenium and also handling some of the quirks we have discovered during development of our testing framework. It also supports "nesting" of the browsers in relation to specific widgets, so it is then easier in the widget layer to implement the lookup fencing. Majority of this functionality is implemented in :py:class:`widgetastic.browser.Browser`.

Lookup fencing is a technique that enables the programmer to write locators that are relative to its hosting object. When such locator gets resolved, the parent element is resolved first (and it continues recursively until you hit an "unwrapped" browser that is just a browser). This behaviour is not visible to the outside under normal circumstances and it is achieved by :py:class:`widgetastic.browser.BrowserParentWrapper`.

The :py:class:`widgetastic.browser.Browser` class has some convenience features like `Automatic detection of simple CSS locators`_ and `Automatic visibility precedence selection`_.


.. `Automatic detection of simple CSS locators`:

Automatic detection of simple CSS locators
------------------------------------------

By default, all string locators are considered XPath, but in each place where a locator gets passed
into Widgetastic you can leverage automatic simple CSS locator detection. If a string corresponds to
the pattern of `tagname#id.class1.class2` where the tag is optional and at least one `id` or `class`
is present, it considers it a CSS locator.

If you want to use a complex CSS locator or a different lookup type, you can use
`selenium-smart-locator <https://pypi.python.org/pypi/selenium-smart-locator>`_ library that is used
underneath to process all the locators. You can consult the documentation and pass instances of
``Locator`` instead of a string.

This library is already in the requirements, so it is not necessary to install it.

.. `Automatic visibility precedence selection`:

Automatic visibility precedence selection
-----------------------------------------

Under normal circumstances, Selenium's ``find_element`` always returns the first element from the query result. But what if there are multiple such elements matching the query, the first one is invisible for a reason and the second one is displayed?

Widgetastic's :py:meth:`widgetastic.browser.Browser.element` checks for visibility if there are multiple elements as a result of the query. It returns the first visible element, and if none of the elements are visible, it returns the first one as in the raw Selenium.


.. `Widget system`:

Widget system
=============

The widget system consists of number of supporting classes and finally the :py:class:`widgetastic.widget.Widget` class itself.

Let's first talk about how Widgetastic makes sure that although the user "instantiates" the widgets without any additional context, the widgets themselves receive everything they need in a consistent manner.

The important thing is in :py:meth:`widgetastic.widget.Widget.__new__`. ``__new__`` is the dunder method responsible for creating the object from the class and it is called before ``__init__`` gets called. Widgetastic exploits this functionality. The ``Widget`` class needs to know the instance of another ``Widget`` or :py:class:`widgetastic.browser.Browser` to be instantiated. Since we do not know it at the moment of class definition, we need to **defer** it. And that is where :py:class:`widgetastic.widget.WidgetDescriptor` comes into play.


How the WidgetDescriptor works?
-------------------------------

The beforementioned ``__new__`` method checks if the first argument or the ``parent`` kwargument is specified. If yes, it then lets python create the object as usual. If it is not passed, an instance of :py:class:`widgetastic.widget.WidgetDescriptor` is returned instead. The descriptor class contains these three most important informations:

* The class object (*yes, class, not an instance*)
* args
* kwargs

The ``WidgetDescriptor`` is named a descriptor for a reason. Because it implements the ``__get__`` method, it is a Python descriptor. Descriptors allow you to be in the access loop when you access an attribute on an object. This brings us to the deferring and how it is done.

Simply said, once you access the widget (``view.widget``), the descriptor implementation in the ``WidgetDescriptor`` just instantiates the class with the args and kwargs that were stored on definition and returns it instead of returning itself.

In real implementation, caching and other things make this process more complex, but under the hood this is what happens.

:py:class:`widgetastic.widget.WidgetDescriptor` is also ordinal. Each one has a unique ``_seq_id`` attribute which increments for each new :py:class:`widgetastic.widget.WidgetDescriptor` created. Therefore although it is not possible with pure Python facilities, Widgetastic can order the widgets in the order as they were defined.

All this also means that if you are playing with single widgets in eg. IPython, you always need to stick a browser obejct or another widget as the first parameter. You also need to make sure ``parent`` and ``logger`` are passed to ``super()`` so the widget object can be properly initialized.

.. code-block:: python

    class MyNewWidget(Widget):
        def __init__(self, parent, myarg1, logger=None):
            Widget.__init__(self, parent, logger=logger)
            self.myarg1 = myarg1


The magic of metaclasses
------------------------

:py:class:`widgetastic.widget.Widget` class has a custom metaclass - :py:class:`widgetastic.widget.WidgetMetaclass`. Metaclasses create classes the same way classes create instances. :py:class:`widgetastic.widget.WidgetMetaclass` processes the class definition and builds a couple of helper attributes to facilitate eg. name resolution, since the widget definition cannot know by itself what was the name you assigned it on the class. It also wraps fill/read with logging, generates a :py:meth:`widgetastic.widget.Widget.__locator__` if ``ROOT`` is present, ...


Caching of widgets
------------------

Widget instances are cached on the hosting widget. Only plain widgets get cached, because the caching system is too simple so far to support parametrized views and such advanced functionality. The descriptor object is used as the cache key, the widget instance is the value.


``__locator__()`` and ``__element__()`` protocol
------------------------------------------------

To ensure good structure, a protocol of two methods was introduced. Let's talk a bit about them.

``__locator__()`` method is not implemented by default on ``Widget`` class. Its sole purpose is to
serve a locator of the object itself, so when the object is thrown in element lookup, it returns the
result for the locator returned by this method. This method must return a locator, be it a valid
locator string, tuple or another locatable object. If a webelement is returned by ``__locator__()``,
a warning will be produced into the log.

``__locator__()`` is auto-generated when ``ROOT`` attribute is present on the class with a valid
locator.

``__element__()`` method has a default implementation on every widget. Its purpose is to look up the
root element from ``__locator__()``. It is present because the machinery that digests the objects
for element lookup will try it first. ``__element__()``'s default implementation looks up the
``__locator__()`` in the *parent browser*. That is important, because that allows simpler structure
for the browser wrapper.

Combination of these methods ensures, that while the widget's root element is looked up in parent
browser, which fences the lookup into the parent widget, all lookups inside the widget, like child
widgets or other browser operations operate within the widget's root element, eliminating the need
of passing the parent element.
