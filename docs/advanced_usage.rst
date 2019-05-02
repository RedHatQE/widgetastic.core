Advanced usage
==============

Simplified nested form fill
---------------------------

When you want to separate widgets into logical groups but you don't want to have a visual clutter in
the code, you can use dots in fill keys to signify the dictionary boundaries:

.. code-block:: python

    # This:
    view.fill({
        'x': 1,
        'foo.bar': 2,
        'foo.baz': 3,
    })

    # Is equivalent to this:
    view.fill({
        'x': 1,
        'foo': {
            'bar': 2,
            'baz': 3,
        }
    })


.. _version-picking:

Version picking
------------------
By version picking you can tackle the challenge of widgets changing between versions.

In order to use this feature, you have to provide ``product_version`` property in the Browser which
should return the current version (ideally :py:class:`widgetastic.utils.Version`, otherwise you would need to redefine
the :py:attr:`widgetastic.utils.VersionPick.VERSION_CLASS` to point at you version handling class of choice)
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

:py:class:`widgetastic.utils.VersionPick` is not limited to resolving widgets and can be used for anything.

You can also pass the :py:class:`widgetastic.utils.VersionPick` instance as a constructor parameter into widget instantiation
on the view class. Because it utilizes :ref:`constructor-object-collapsing`, it will resolve itself
automatically.

.. _parametrized-views:

Parametrized views
------------------

If there is a repeated pattern on a page that differs only by eg. a title or an id, widgetastic has
a solution for that. You can use a :py:class:`widgetastic.widget.ParametrizedView` that takes an
arbitrary number of parameters and then you can use the parameters eg. in locators.

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

The parametrized views also support list-like access using square braces. For that to work, you need
the ``all`` classmethod defined on the view so Widgetastic would be aware of all the items. You can
access the parametrized views by member index ``[i]`` and slice ``[i:j]``.

It is also possible to iterate through all the occurences of the parametrized view. Let's assume the
previous code sample is still loaded and the ``this_is_parametrized`` class has the ``all()``
defined. In that case, the code would like like this:

.. code-block:: python

    for p_view in view.this_is_parametrized:
        print(p_view.the_widget.read())

This sample code would go through all the occurences of the parametrization. Remember that the
``all`` classmethod IS REQUIRED in this case.

You can also pass the :py:class:utils`ParametrizedString` instance as a constructor parameter into widget instantiation
on the view class. Because it utilizes :ref:`constructor-object-collapsing`, it will resolve itself
automatically.

.. _constructor-object-collapsing:

Constructor object collapsing
-----------------------------

By using :py:class:`widgetastic.utils.ConstructorResolvable` you can create an object that can lazily resolve
itself into a different object upon widget instantiation. This is used eg. for the :ref:`version-picking`
where :py:class:`widgetastic.utils.VersionPick` descends from this class or for the parametrized strings. Just subclass this
class and implement ``.resolve(self, parent_object)`` where ``parent_object`` is the to-be parent
of the widget.

.. _fillable-objects:

Fillable objects
----------------

I bet that if you have ever used modelling approach to the entities represented in the product, you
have come across filling values in the UI and if you wanted to select the item representing given
object in the UI, you had to pick a correct attribute and know it. So you had to do something like
this (simplified example)

.. code-block:: python

    some_form.item.fill(o.description)

If you let the class of ``o`` implement :py:class:`widgetastic.utils.Fillable``, you can implement the method
``.as_fill_value`` which should return such value that is used in the UI. In that case, the
simplification is as follows.

.. code-block:: python

    some_form.item.fill(o)

You no longer have to care, the object itself know how it will be displayed in the UI. Unfortunately
this does not work the other way (automatic instantiation of objects based on values read) as that
would involve knowledge of metadata etc. That is a possible future feature.


.. _widget-including:

Widget including
----------------

DRY is useful, right? Widgetastic thinks so, so it supports including widgets into other widgets.
Think about it more like C-style include, what it does is that it makes the receiving widget aware
of the other widgets that are going to be included and generates accessors for the widgets in
included widgets so if "flattens" the structure. All the ordering is kept. A simple example.

.. code-block:: python

    class FormButtonsAdd(View):
        add = Button('Add')
        reset = Button('Reset')
        cancel = Button('Cancel')

    class ItemAddForm(View):
        name = TextInput(...)
        description = TextInput(...)

        # ...
        # ...

        buttons = View.include(FormButtonsAdd)

This has the same effect like putting the buttons directly in ``ItemAddForm``.

You **ABSOLUTELY MUST** be aware that in background this is not including in its literal sense. It
does not take the widget definitions and put them in the receiving class. If you access the widget
that has been included, what happens is that you actually access a descriptor proxy that looks up
the correct included hosting widget where the requested widget is hosted (it actually creates it on
demand), then the correct widget is returned. This has its benefit in the fact that any logical
structure that is built inside the included class is retained and works as one would expect, like
parametrized locators and such.

All the included widgets in the structure share their parent with the widget where you started
including. So when instantiated, the underlying ``FormButtonsAdd`` has the same parent widget as
the ``ItemAddForm``. I did not think it would be wise to make the including widget a parent for the
included widgets due to the fact widgetastic fences the element lookup if ``ROOT`` is present on a
widget/view. However, :py:class:`widgetastic.widget.View.include` supports ``use_parent=True`` option which makes included
widgets use including widget as a parent for rare cases when it is really necessary.


.. _switchable-conditional-views:

Switchable conditional views
----------------------------

If you have forms in your product whose parts change depending on previous selections, you might
like to use the :py:class:`widgetastic.widget.ConditionalSwitchableView`. It will allow you to represent different kinds of
views under one widget name. An example might be a view of items that can use icons, table, or
something else. You can make views that have the same interface for all the variants and then
put them together using this tool. That will allow you to interact with the different views the
same way. They display the same informations in the end.

.. code-block:: python

    class SomeForm(View):
        foo = Input('...')
        action_type = Select(name='action_type')

        action_form = ConditionalSwitchableView(reference='action_type')

        # Simple value matching. If Action type 1 is selected in the select, use this view.
        # And if the action_type value does not get matched, use this view as default
        @action_form.register('Action type 1', default=True)
        class ActionType1Form(View):
            widget = Widget()

        # You can use a callable to declare the widget values to compare
        @action_form.register(lambda action_type: action_type == 'Action type 2')
        class ActionType2Form(View):
            widget = Widget()

        # With callable, you can use values from multiple widgets
        @action_form.register(
            lambda action_type, foo: action_type == 'Action type 2' and foo == 2)
        class ActionType2Form(View):
            widget = Widget()

You can see it gives you the flexibility of decision based on the values in the view.

This example as shown (with Views) will behave like the ``action_form`` was a nested view. You can
also make a switchable widget. You can use it like this:

.. code-block:: python

    class SomeForm(View):
        foo = Input('...')
        bar = Select(name='bar')

        switched_widget = ConditionalSwitchableView(reference='bar')

        switched_widget.register('Action type 1', default=True, widget=Widget())

Then instead of switching views, it switches widgets.

IFrame support is views
-----------------------------

If some html page has embedded iframes, those can be covered using regular view.
You just need to set FRAME property for it. FRAME should point out to appropriate iframe and can be xpath and whatever supported by widgetastic.

Since iframe is another page, all its bits consider iframe as root. This has to be taken into account during creating object structure.

If regular views and iframe views are mixed, widgetastic takes care of switching between frames on widget access. 
User doesn't need to undertake any actions.

Below is example of usage. More examples can be found in unit tests.

.. code-block:: python

    class FirstIFrameView(View):
        FRAME = '//iframe[@name="some_iframe"]'
        
        h3 = Text('.//h3')
        select1 = Select(id='iframe_select1')
        select2 = Select(name='iframe_select2')

        class RegularView(View):
            h3 = Text('//h3[@id="someid-1"]')
            checkbox1 = Checkbox(id='checkbox-1')

            class SecondIFrameView(View):
                FRAME = './/iframe[@name="another_iframe"]'

                widget1 = Widget()
                widget2 = Widget()
 
