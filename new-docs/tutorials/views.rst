=====
Views
=====

Views are the cornerstone of widgetastic's architecture. They organize widgets into logical groups that represent pages, sections, or components of your application. This tutorial covers different types of views.

.. note::
   **Prerequisites**: Complete :doc:`basic-widgets` tutorial first.

Understanding Views
===================

A **View** is a container that groups related widgets together. Think of it as representing a page, dialog, or section of your web application.
A View descends from the Widget class but it is specifically designed to hold other widgets.


**Basic View Example**

.. literalinclude:: ../examples/views/basic_view.py
   :language: python
   :linenos:

.. note::
   **WidgetDescriptor and Lazy Creation:**

   When you define widgets on a view (e.g., ``main_title = Text(locator= ".//h1[@id='wt-core-title']")``), you're not creating
   an actual widget object immediately. Instead, a ``WidgetDescriptor`` is created. The actual widget
   instance is created lazily when you access it (e.g., ``view.main_title``), at which point the browser
   is automatically prepended to the widget's arguments. This lazy creation mechanism ensures widgets
   are only instantiated when needed and have access to the correct browser context.


View Hierarchy and Nesting
===========================

Views can contain other views, creating hierarchical structures that mirror your application's layout. This allows you to organize complex pages into manageable, reusable components.

There are two approaches to create nested views in widgetastic:

.. note::
   In our testing page, we have a `View Testing` section. Under this section, we have normal view, parametrized view and conditional switchable view.
   Let's see how to create nested views for these sections.

**1. Attribute Assignment**

This approach creates standalone view classes and assigns them as attributes using ``View.nested()``:

.. literalinclude:: ../examples/views/nested_view_attribute_assignment.py
   :language: python
   :linenos:


**2. Inner Classes**

This approach defines view classes as inner classes with the ``@View.nested`` decorator:

.. literalinclude:: ../examples/views/nested_view_inner_classes.py
   :language: python
   :linenos:

.. note::
   **Understanding @View.nested Decorator:**

   The ``@View.nested`` decorator is **not strictly necessary** for basic functionality, but it provides
   important benefits that become critical in certain scenarios:

   * **Widget Ordering**: Views remember the order in which widgets are placed on them, which is
     important for fill/read operations. When you use ``View.nested()`` as an attribute assignment
     (Method 1), the nested view doesn't get wrapped in a ``WidgetDescriptor``, so it won't participate
     in the ordering mechanism. Using the ``@View.nested`` decorator on an inner class ensures the view
     is properly wrapped in a ``WidgetDescriptor`` and maintains correct order for fill/read operations.

   * **Proper Initialization**: Guarantees correct parent-child relationships and browser context propagation

   * **Cleaner Organization**: Keeps related views grouped within the parent class, improving code readability

   **When to use @View.nested**: Use it when widget ordering matters for your fill/read operations, or
   when you want to ensure proper WidgetDescriptor wrapping for consistency with the framework's design.

**ROOT Locator Scoping**

The ``ROOT`` attribute defines the container for a view. All widgets in that view are searched within this container, providing proper scoping:

.. literalinclude:: ../examples/views/root_locator_scoping.py
   :language: python
   :linenos:

.. _parametrized-views:

Parametrized Views
==================
:py:class:`widgetastic.widget.ParametrizedView` are useful when you need to create a view for a repeated pattern on a page that differs only by eg. a title or an id.
For example, if you have a page with a list of items, you can use a parametrized view to create a view for each item.
You can then use the parameters eg. in locators to create a view for each item.

**ParametrizedView Example**

Look at our testing page, Under `Parametrized view testing` section, you can see three similar containers that follow the same pattern but with different identifiers.

* Thing "foo": Container ``<div id="foo">``, input ``name="asdf_foo"``, description ``name="desc_foo"``, checkbox ``name="active_foo"``
* Thing "bar": Container ``<div id="bar">``, input ``name="asdf_bar"``, description ``name="desc_bar"``, checkbox ``name="active_bar"``
* Thing "baz": Container ``<div id="baz">``, input ``name="asdf_baz"``, description ``name="desc_baz"``, checkbox ``name="active_baz"``

Without ParametrizedView, you'd need to create separate view classes for each "thing" or write repetitive code with hardcoded locators for each variation. This becomes unmaintainable when testing multiple similar components.

ParametrizedView solves this by letting you define a single template view that can be reused with different parameters. The ``thing_id`` parameter gets injected into locators and widget definitions at runtime, allowing one view class to handle all "thing" variations on the testing page.

.. literalinclude:: ../examples/views/parametrized_view.py
   :language: python
   :linenos:

**Nested Parametrized View Example**

It is also possible to nest the parametrized view inside another view, parametrized or otherwise.
In this case the invocation of a nested view looks like a method call, instead of looking like a property.
The invocation supports passing the arguments both ways, positional and keyword based.

.. literalinclude:: ../examples/views/nested_parametrized_view.py
   :language: python
   :linenos:


The parametrized views also support list-like access using square braces.
For that to work, you need the `all` classmethod defined on the view so Widgetastic would be aware of all the items.
You can access the parametrized views by member index [i] and slice [i:j].

It is also possible to iterate through all the occurences of the parametrized view.
Let's assume the previous code sample is still loaded and the `thing_container_view` class has the all() defined.
In that case, the code would like like this:

.. literalinclude:: ../examples/views/parametrized_view_iteration.py
   :language: python
   :linenos:

.. note::
   This sample code would go through all the occurences of the parametrization. Remember that the all classmethod **IS REQUIRED** in this case.

You can also pass the :py:class:`widgetastic.utils.ParametrizedString` instance as a constructor parameter into widget instantiation on the view class.
Because it utilizes :ref:`constructor-object-collapsing`, it will resolve itself automatically.

.. _constructor-object-collapsing:


Constructor Object Collapsing
=============================

Constructor object collapsing is a powerful mechanism that allows objects to lazily resolve themselves into different objects during widget instantiation. This is used internally by several widgetastic utilities like :py:class:`widgetastic.utils.VersionPick` for :doc:`version-picking` and :py:class:`widgetastic.utils.ParametrizedString` for parametrized views.

**How It Works**

By using :py:class:`widgetastic.utils.ConstructorResolvable`, you can create an object that can lazily resolve itself into a different object upon widget instantiation. The key is to subclass this class and implement ``.resolve(self, parent_object)`` where ``parent_object`` is the to-be parent of the widget.

**Why It's Useful**

This mechanism enables:

* **Lazy Evaluation**: Objects can decide their final form only when they have full context
* **Dynamic Resolution**: The same constructor parameter can resolve to different values based on runtime conditions
* **Version Picking**: :py:class:`widgetastic.utils.VersionPick` uses this to select appropriate widgets based on browser version
* **Parametrized Strings**: :py:class:`widgetastic.utils.ParametrizedString` uses this to inject parameters during widget construction

.. note::
   Most users won't need to implement their own ``ConstructorResolvable`` classes, as the built-in ones (``VersionPick``, ``ParametrizedString``, ``ParametrizedLocator``) cover most use cases.


.. _switchable-conditional-views:

Conditional Views
=================

Handle dynamic UI sections that change based on application state using conditional views.

If you have forms in your product whose parts change depending on previous selections, you might like to use the :py:class:`widgetastic.widget.ConditionalSwitchableView`.
It will allow you to represent different kinds of views under one widget name.


**ConditionalSwitchableView Example**

Look at our testing page, Under `Conditional view testing` section, you can see a form with a dropdown and three different views.

* Action type 1: Container ``<div id="action_form_1">``, input ``name="action1_widget"``, select ``name="action1_options"``, checkbox ``name="action1_enabled"``
* Action type 2: Container ``<div id="action_form_2">``, input ``name="action2_widget"``, select ``name="action2_priority"``, input ``name="action2_notes"``
* Action type 3: Container ``<div id="action_form_3">``, input ``name="action3_widget"``, input ``name="action3_config"``, select ``name="action3_mode"``

.. literalinclude:: ../examples/views/conditional_switchable_view.py
   :language: python
   :linenos:

You can see it gives you the flexibility of decision based on the values in the view.


**Simple Conditional Widget Registration**

.. literalinclude:: ../examples/views/simple_conditional_widget.py
   :language: python
   :linenos:


View-Level Operations
=====================

**Batch Operations**

Views support batch operations like fill and read on all their widgets.

.. literalinclude:: ../examples/views/batch_operations.py
   :language: python
   :linenos:

**View Lifecycle Hooks**

Views can optionally define ``before_fill(values)`` and ``after_fill(was_change)`` methods to
intercept the fill process:

.. literalinclude:: ../examples/views/view_lifecycle_hooks.py
   :language: python
   :linenos:


**View State Checking**

If we don't specify a ``ROOT`` locator, it will be considered as displayed every time.
but if we specify a ``ROOT`` locator, it will be considered as displayed only when the root locator is present on web page.

.. literalinclude:: ../examples/views/view_state_checking.py
   :language: python
   :linenos:

.. note::
    View ``is_displayed`` property is important to know when you are using views to navigate between pages.
    So it recommended to specify a ``ROOT`` locator for all views. If you don't want to specify a ``ROOT`` locator,
    then tried to add custom ``is_displayed`` property to the view.


Best Practices for Views
=========================

When designing views in widgetastic, following best practices will help you create maintainable, readable, and robust automation code. Here are some key guidelines:

- **Use Descriptive Names**: Name your view classes according to their purpose or the section of the application they represent. This makes your code self-explanatory and easier to navigate.

    .. code-block:: python

        # Good: Clear purpose
        class LoginFormView(View):
            pass

        class UserProfileSettingsView(View):
            pass

        # Avoid: Generic names
        class View1(View):
            pass

- **Group Related Widgets**: Organize widgets within a view so that each view contains only widgets relevant to a specific page, dialog, or component. Avoid mixing unrelated widgets in a single view.

    .. code-block:: python

        # Group related functionality
        class SearchView(View):
            search_input = TextInput(id="search")
            search_button = Button(id="search-btn")
            results_table = Table(id="results")

        # Don't mix unrelated widgets
        class BadView(View):
            login_field = TextInput(id="login")      # Login functionality
            checkout_btn = Button(id="checkout")     # Shopping functionality
            settings_link = Text("a#settings")      # Settings functionality

- **Leverage ROOT Locators**: Always define a ``ROOT`` locator for your views to scope widget searches to the correct section of the page. This prevents accidental matches and improves reliability.

    .. code-block:: python

        # Scope widgets to specific sections
        class SidebarView(View):
            ROOT = "#sidebar"

            menu_item1 = Text("a[href='/dashboard']")
            menu_item2 = Text("a[href='/profile']")

- **Prefer Nested Views for Complex Pages**: For pages with multiple sections or repeated patterns, use nested views or parametrized views to mirror the application's structure. This keeps your code modular and reusable.

    .. code-block:: python

        # Nested views
        class UserProfilePage(View):
            ROOT = "#user-profile"
            @View.nested
            class personal_info(View):
                ROOT = "#personal-section"
                first_name = TextInput("#first_name")
                last_name = TextInput("#last_name")

            @View.nested
            class preferences(View):
                ROOT = "#preferences-section"
                theme = Select("#theme")
                language = Select("#language")

- **Customize is_displayed When Needed**: If a view cannot be reliably detected by a single locator, override the ``is_displayed`` property to implement custom logic using one or more widgets.

    .. code-block:: python

        class CustomView(View):
            ROOT = "#custom-view"
            custom_widget = TextInput("#custom-widget")

            @property
            def is_displayed(self):
                return self.custom_widget.is_displayed


Summary
=======

Views are essential for organizing and structuring your automation code:

* **Basic Views**: Container for related widgets
* **Nested Views**: Hierarchical page structures
* **Parametrized Views**: Handle repeated UI patterns
* **Conditional Views**: Adapt to dynamic content
* **View Operations**: Batch read/fill operations
