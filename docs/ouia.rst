Open UI Automation
==================

Widgetastic provides a support of `OUIA <https://ouia.readthedocs.io>`_ compatible
components. There are three base classes: :py:class:`widgetastic.ouia.OUIAMixin`, 
:py:class:`widgetastic.ouia.OUIAGenericView` and :py:class:`widgetastic.ouia.OUIAGenericWidget`.

In order to start creating an OUIA compatible widget or view just inherit a respectful class.
Children classes must have the same name as the value of ``data-ouia-component-type`` attribute of
the root HTML element. Besides children classes should define ``OUIA_NAMESPACE`` class attribute if
it's appicable.

Examples:

Consider this html excerpt:

.. code-block:: html

    <button data-ouia-component-type="PF/Button" data-ouia-component-id="This is a button">
        This is a button
    </button>

According to OUIA this is ``Button`` component in ``PF`` namespace with id ``This is a button``.
Basing on that information we can create the following widget:

.. code-block:: python

    from widgetastic.ouia import OUIAGenericWidget

    class Button(OUIAGenericWidget):
        OUIA_NAMESPACE = "PF"
        pass

As you can see you don't need to specify any locator. If a component complies with OUIA spec the
locator can be generated. The only argument you may provide is ``component_id``. After that you can
add this class to some view and use in automation:

.. code-block:: python

    class Details(View):
        ROOT = ".//div[@id='some_id']"
        button = Button("This is a button")

    view = Details(browser)
    view.button.click()
