.. _widgetastic-usage-guidelines:

Widgetastic usage guidelines
----------------------------

Anyone using this library should consult these guidelines whether one is not violating any of them.

- While writing new widgets:
  
  - They must have the standard read/fill interface
    
    - ``read()`` -> ``object``
      
      - Whatever is returned from ``read()`` must be compatible with ``fill()``. Eg. ``obj.fill(obj.read())`` must work at any time.
      
      - ``read()`` may throw a ``DoNotReadThisWidget`` exception if reading the widget is pointless (eg. in current form state it is hidden). That is achieved by invoking the ``do_not_read_this_widget()`` function.
    
    - ``fill(value)`` -> ``True|False``
      
      - ``fill(value)`` must be able to ingest whatever was returned by ``read()``. Eg. ``obj.fill(obj.read())`` must work at any time.
        
        - An exception to this rule is only acceptable in the case where this 1:1 direct mapping would cause severe inconvenience.
      
      - ``fill`` MUST return ``True`` if it changed anything during filling
      
      - ``fill`` MUST return ``False`` if it has not changed anything during filling
    
    - Any of these methods may be omitted if it is appropriate based on the UI widget interactions.
    
    - It is recommended that all widgets have at least ``read()`` but in cases like buttons where you don't read or fill, it is understandable that there is neither of those.
  - ``__init__`` must be in accordance to the concept
    
    - If you want your widget to accept parameters ``a`` and ``b``, you have to create signature like this:
      
      - ``__init__(self, parent, a, b, logger=None)``

    - The first line of the widget must call out to the root class in order to set things up properly:
      
      - ``Widget.__init__(self, parent, logger=logger)``

  - Widgets MUST define ``__locator__`` in some way. Views do not have to, but can do it to fence the element lookup in its child widgets.
    
    - You can write ``__locator__`` method yourself. It should return anything that can be turned into a locator by ``smartloc.Locator``

      - ``'#foo'``
      
      - ``'//div[@id="foo"]'``
      
      - ``smartloc.Locator(xpath='...')``
      
      - et cetera
    
    - ``__locator__`` MUST NOT return ``WebElement`` instances to prevent ``StaleElementReferenceException``
    
    - If you use a ``ROOT`` class attribute, especially in combination with ``ParametrizedLocator``, a ``__locator__`` is generated automatically for you.
  
  - Widgets should keep its internal state in reasonable size. Ideally none, but eg. caching header names of tables is perfectly acceptable. Saving ``WebElement`` instances in the widget instance is not recommended.

    - Think about what to cache and when to invalidate

    - Never store ``WebElement`` objects.

    - Try to shorten the lifetime of any single ``WebElement`` as much as possible

      - This will help against ``StaleElementReferenceException``
  
  - Widgets shall log using ``self.logger``. That ensures the log message is prefixed with the widget name and location and gives more insight about what is happening.

- When using Widgets (and Views)
  
  - Bear in mind that when you do ``MySuperWidget('foo', 'bar')`` in ipython, you are not getting an actual widget object, but rather an instance of WidgetDescriptor

  - In order to create a real widget object, you have to have widgetastic ``Browser`` instance around and prepend it to the arguments, so the call to create a real widget instance would look like:
    
    - ``MySuperWidget(wt_browser, 'foo', 'bar')``
  
  - This browser prepending is done automatically by ``WidgetDescriptor`` when you access it on a ``View`` or another ``Widget``
    
    - All of these means that the widget objects are created lazily.

  - Views can be nested

    - Filling and reading nested views is simple, each view is read/filled as a dictionary, so the required dictionary structure is exactly the same as the nested class structure

  - Views remember the order in which the Widgets were placed on it. Each ``WidgetDescriptor`` has a sequential number on it. This is used when filling or reading widgets, ensuring proper filling order.
    
    - This would normally also apply to Views since they are also descendants of ``Widget``, but since you are not instantiating the view when creating nested views, this mechanism does not work.

      - You can ensure the ``View`` gets wrapped in a ``WidgetDescriptor`` and therefore in correct order by placing a ``@View.nested`` decorator on the nested view.

  - Views can optionally define ``before_fill(values)`` and ``after_fill(was_change)``

    - ``before_fill`` is invoked right before filling gets started. You receive the filling dictionary in the values parameter and you can act appropriately.

    - ``after_fill`` is invoked right after the fill ended, ``was_change`` tells you whether there was any change or not.

- When using ``Browser`` (also applies when writing Widgets)

  - Ensure you don't invoke methods or attributes on the ``WebElement`` instances returned by ``element()`` or ``elements()``

  - Eg. instead of ``element.text`` use ``browser.text(element)`` (applies for all such circumstances). These calls usually do not invoke more than their original counterparts. They only invoke some workarounds if some know issue arises. Check what the ``Browser`` (sub)class offers and if you miss something, create a PR 

  - You don't necessarily have to specify ``self.browser.element(..., parent=self)`` when you are writing a query inside a widget implementation as widgetastic figures this out and does it automatically.

  - Most of the methods that implement the getters, that would normally be on the element object, take an argument or two for themselves and the rest of ``*args`` and ``**kwargs`` is shoved inside ``element()`` method for resolution, so constructs like ``self.browser.get_attribute('id', self.browser.element('locator', parent=foo))`` are not needed. Just write ``self.browser.get_attribute('id', 'locator', parent=foo)``. Check the method definitions on the ``Browser`` class to see that.

  - ``element()`` method tries to apply a rudimentary intelligence on the element it resolves. If a locator resolves to a single element, it returns it. If the locator resolves to multiple elements, it tries to filter out the invisible elements and return the first visible one. If none of them is visible, it just returns the first one. Under normal circumstances, standard selenium resolution always returns the first of the resolved elements.
  
  - DO NOT use ``element.find_elements_by_<method>('locator')``, use ``self.browser.element('locator', parent=element)``. It is about as same long and safer.

    - Eventually I might wrap the elements as well but I decided to not complicate things for now.

*No current exceptions are to be taken as a precedent.*