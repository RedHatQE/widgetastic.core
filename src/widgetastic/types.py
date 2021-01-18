from typing import Callable
from typing import Dict
from typing import List
from typing import Tuple
from typing import TYPE_CHECKING
from typing import Union

from selenium.webdriver.remote.webelement import WebElement
from smartloc import Locator
from typing_extensions import Protocol


if TYPE_CHECKING:
    from .browser import Browser
    from .utils import Version
    from .widget.base import View
    from .widget.base import Widget
    from .widget.base import ClickableMixin


class LocatorProtocol(Protocol):
    CHECK_VISIBILITY: bool

    def __locator__(self) -> Union[str, Locator, WebElement]:
        ...


LocatorAlias = Union[str, Dict[str, str], WebElement, LocatorProtocol, "Widget"]

ElementParent = Union[LocatorAlias, "Browser"]

ViewParent = Union["Browser", "View"]

VString = Union[str, "Version", List[Union[int, str]], Tuple[Union[int, str]]]

Handler = Union[str, "ClickableMixin", Callable]
