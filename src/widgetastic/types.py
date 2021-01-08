from typing import Callable
from typing import Dict
from typing import List
from typing import Tuple
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import Union

from selenium.webdriver.remote.webelement import WebElement
from smartloc import Locator
from typing_extensions import Protocol

from .browser import DefaultPlugin

if TYPE_CHECKING:
    from .browser import Browser
    from .utils import Version
    from .widget.base import Widget
    from .widget.base import ClickableMixin


class LocatorProtocol(Protocol):
    def __locator__(self) -> Union[str, Locator, WebElement]:
        ...


DefaultPluginType = TypeVar("DefaultPluginType", bound=DefaultPlugin)

LocatorAlias = Union[str, Dict[str, str], WebElement, LocatorProtocol, "Widget"]

ElementParent = Union[LocatorAlias, "Browser"]

ViewParent = ["Browser", "View"]

VString = Union[str, "Version", List[Union[int, str]], Tuple[Union[int, str]]]

Handler = Union[str, ClickableMixin, Callable]
