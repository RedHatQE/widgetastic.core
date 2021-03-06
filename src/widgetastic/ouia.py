from logging import Logger
from typing import Any
from typing import MutableMapping
from typing import Optional

from widgetastic.browser import Browser
from widgetastic.types import ViewParent
from widgetastic.utils import ParametrizedLocator
from widgetastic.widget.base import ClickableMixin
from widgetastic.widget.base import View
from widgetastic.widget.base import Widget
from widgetastic.xpath import quote


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
    browser: Browser

    def _set_attrs(
        self,
        component_type: str,
        component_id: Optional[str] = None,
    ) -> None:
        self.component_type = quote(component_type)
        component_id = f" and @data-ouia-component-id={quote(component_id)}" if component_id else ""
        self.component_id = component_id
        self.locator = self.ROOT.locator

    @property
    def is_safe(self) -> bool:
        """
        An attribute called data-ouia-safe, which is True only when the component is in a static
        state, i.e. no animations are occurring. At all other times, this value MUST be False.
        """
        return "true" in self.browser.get_attribute("data-ouia-safe", self)

    def __locator__(self) -> ParametrizedLocator:
        return self.ROOT


class OUIAGenericView(OUIABase, View):
    """A base class for any OUIA compatible view.

    Children classes must have the same name as the value of ``data-ouia-component-type`` attribute
    of the root HTML element. Besides children classes should define ``OUIA_NAMESPACE`` attribute if
    it's appicable.

    Args:
        component_id: value of data-ouia-component-id attribute.
    """

    OUIA_COMPONENT_TYPE: str

    def __init__(
        self,
        parent: ViewParent,
        component_id: Optional[str] = None,
        logger: Optional[Logger] = None,
        **kwargs: MutableMapping[str, Any],
    ) -> None:
        self._set_attrs(
            component_type=self.OUIA_COMPONENT_TYPE or type(self).__name__,
            component_id=component_id,
        )
        super().__init__(
            parent=parent,
            logger=logger,
            **kwargs,
        )


class OUIAGenericWidget(OUIABase, Widget, ClickableMixin):
    """A base class for any OUIA compatible widget.

    Children classes must have the same name as the value of ``data-ouia-component-type`` attribute
    of the root HTML element. Besides children classes should define ``OUIA_NAMESPACE`` attribute if
    it's appicable.

    Args:
        component_id: value of data-ouia-component-id attribute.
    """

    OUIA_COMPONENT_TYPE: str

    def __init__(
        self,
        parent: ViewParent,
        component_id: Optional[str] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self._set_attrs(
            component_type=self.OUIA_COMPONENT_TYPE or type(self).__name__,
            component_id=component_id,
        )
        super().__init__(parent=parent, logger=logger)
