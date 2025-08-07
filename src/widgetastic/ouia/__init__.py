from logging import Logger
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

    ROOT = ParametrizedLocator(
        ".//*[contains(@data-ouia-component-type,{@component_type}){@component_id_suffix}]"
    )
    browser: Browser

    def _set_attrs(
        self,
        component_type: str,
        component_id: str = "",
    ) -> None:
        self.component_type = quote(component_type)
        self.component_id = quote(component_id)
        component_id = f" and @data-ouia-component-id={quote(component_id)}" if component_id else ""
        self.component_id_suffix = component_id
        self.locator = self.ROOT.locator

    @property
    def is_safe(self) -> bool:
        """
        An attribute called data-ouia-safe, which is True only when the component is in a static
        state, i.e. no animations are occurring. At all other times, this value MUST be False.
        """
        return "true" == self.browser.get_attribute("data-ouia-safe", self)

    def __locator__(self) -> ParametrizedLocator:
        return self.ROOT

    def __repr__(self):
        component_id_suffix = f"; ouia id: {self.component_id}" if self.component_id else ""
        desc = f"ouia type: {self.component_type}{component_id_suffix}"
        return f"<{type(self).__name__}; {desc}>"


class OUIAGenericView(OUIABase, View):
    """A base class for any OUIA compatible view.

    Children classes must have the same name as the value of ``data-ouia-component-type`` attribute
    of the root HTML element.

    Args:
        component_id: value of data-ouia-component-id attribute.
        component_type: value of data-ouia-component-type attribute.
    """

    OUIA_COMPONENT_TYPE: str
    OUIA_ID: Optional[str]

    def __init__(
        self,
        parent: ViewParent,
        component_id: str = "",
        logger: Optional[Logger] = None,
        **kwargs,
    ) -> None:
        component_type: Optional[str] = kwargs.pop("component_type", None)
        self._set_attrs(
            component_type=component_type or self.OUIA_COMPONENT_TYPE or type(self).__name__,
            component_id=getattr(self, "OUIA_ID", component_id),
        )
        super().__init__(
            parent=parent,
            logger=logger,
            **kwargs,
        )


class OUIAGenericWidget(OUIABase, Widget, ClickableMixin):
    """A base class for any OUIA compatible widget.

    Children classes must have the same name as the value of ``data-ouia-component-type`` attribute
    of the root HTML element.

    Args:
        component_id: value of data-ouia-component-id attribute.
        component_type: value of data-ouia-component-type attribute.
    """

    OUIA_COMPONENT_TYPE: str

    def __init__(
        self,
        parent: ViewParent,
        component_id: str = "",
        logger: Optional[Logger] = None,
        component_type: Optional[str] = None,
    ) -> None:
        self._set_attrs(
            component_type=component_type or self.OUIA_COMPONENT_TYPE or type(self).__name__,
            component_id=component_id,
        )
        super().__init__(parent=parent, logger=logger)
