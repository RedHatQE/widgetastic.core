"""
Widgetastic Core Type Declarations
==================================
"""

from typing import Callable
from typing import Dict
from typing import List
from typing import Protocol
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

from playwright.sync_api import ElementHandle
from playwright.sync_api import Locator

from .locator import SmartLocator

if TYPE_CHECKING:
    from .browser import Browser
    from .utils import Version
    from .widget.base import View
    from .widget.base import Widget
    from .widget.base import ClickableMixin


class LocatorProtocol(Protocol):
    CHECK_VISIBILITY: bool

    def __locator__(self) -> Union[str, SmartLocator, Locator, ElementHandle]: ...


LocatorAlias = Union[str, Dict[str, str], Locator, ElementHandle, LocatorProtocol, "Widget"]

ElementParent = Union[LocatorAlias, "Browser"]

ViewParent = Union["Browser", "View"]

VString = Union[str, "Version", List[Union[int, str]], Tuple[Union[int, str]]]

Handler = Union[str, "ClickableMixin", Callable]
