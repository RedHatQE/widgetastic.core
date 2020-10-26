from widgetastic.utils import ParametrizedLocator
from widgetastic.xpath import quote
from widgetastic.widget.base import Widget
from widgetastic.widget.base import View
from widgetastic.widget.base import ClickableMixin


class OUIABase:
    """
    Base class for ``OUIA`` support. According to the spec ``OUIA`` compatible components may
    have the following attributes in the root level HTML element:

    * data-ouia-component-type
    * data-ouia-component-id
    * data-ouia-safe

    https://ouia.readthedocs.io/en/latest/README.html#ouia-component
    """

    ROOT = ParametrizedLocator(".//*[@data-ouia-component-type={@component_type}{@component_id}]")

    def __init__(self, component_type, component_id=None, namespace=None, **kwargs):
        component_type = f"{namespace}/{component_type}" if namespace else component_type
        self.component_type = quote(component_type)
        component_id = f" and @data-ouia-component-id={quote(component_id)}" if component_id else ""
        self.component_id = component_id
        self.locator = self.ROOT.locator
        super().__init__(**kwargs)

    @property
    def is_safe(self):
        """
        An attribute called data-ouia-safe, which is True only when the component is in a static
        state, i.e. no animations are occurring. At all other times, this value MUST be False.
        """
        return "true" in self.browser.get_attribute("data-ouia-safe", self)

    def __locator__(self):
        return self.ROOT


class OUIAGenericView(OUIABase, View):
    """A base class for any OUIA compatible view.

    Children classes must have the same name as the value of ``data-ouia-component-type`` attribute
    of the root HTML element. Besides children classes should define ``OUIA_NAMESPACE`` attribute if
    it's appicable.

    Args:
        component_id: value of data-ouia-component-id attribute.
    """

    OUIA_NAMESPACE = None

    def __init__(self, parent, component_id=None, logger=None, **kwargs):
        super().__init__(
            parent=parent,
            logger=logger,
            component_type=type(self).__name__,
            component_id=component_id,
            namespace=self.OUIA_NAMESPACE,
            **kwargs
        )


class OUIAGenericWidget(OUIABase, Widget, ClickableMixin):
    """A base class for any OUIA compatible widget.

    Children classes must have the same name as the value of ``data-ouia-component-type`` attribute
    of the root HTML element. Besides children classes should define ``OUIA_NAMESPACE`` attribute if
    it's appicable.

    Args:
        component_id: value of data-ouia-component-id attribute.
    """

    OUIA_NAMESPACE = None

    def __init__(self, parent, component_id=None, logger=None):
        super().__init__(
            parent=parent,
            logger=logger,
            component_type=type(self).__name__,
            component_id=component_id,
            namespace=self.OUIA_NAMESPACE,
        )
