from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Protocol, Tuple, Union

from selenium.webdriver.remote.webelement import WebElement
from smartloc import Locator

if TYPE_CHECKING:
    from .browser import Browser
    from .utils import Version
    from .widget.base import ClickableMixin, View, Widget


class LocatorProtocol(Protocol):
    CHECK_VISIBILITY: bool

    def __locator__(self) -> str | Locator | WebElement: ...


LocatorAlias = Union[str, Dict[str, str], WebElement, LocatorProtocol, "Widget"]

ElementParent = Union[LocatorAlias, "Browser"]

ViewParent = Union["Browser", "View"]

VString = Union[str, "Version", List[Union[int, str]], Tuple[Union[int, str]]]

Handler = Union[str, "ClickableMixin", Callable]
