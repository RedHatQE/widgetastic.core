"""
Widgetastic Core Type Declarations
==================================
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, Union

from playwright.sync_api import ElementHandle, Locator

from .locator import SmartLocator

if TYPE_CHECKING:
    from .browser import Browser
    from .utils import Version
    from .widget.base import ClickableMixin, View, Widget


class LocatorProtocol(Protocol):
    CHECK_VISIBILITY: bool

    def __locator__(self) -> str | SmartLocator | Locator | ElementHandle: ...


LocatorAlias = Union[str, dict[str, str], Locator, ElementHandle, LocatorProtocol, "Widget"]

ElementParent = Union[LocatorAlias, "Browser"]

ViewParent = Union["Browser", "View"]

VString = Union[str, "Version", list[int | str], tuple[int | str]]

Handler = Union[str, "ClickableMixin", Callable]
