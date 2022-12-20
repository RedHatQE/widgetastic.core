import functools
import logging
import time
from typing import Any
from typing import Callable
from typing import cast
from typing import Iterator
from typing import MutableMapping
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union

from .exceptions import DoNotReadThisWidget


null_logger = logging.getLogger("widgetastic_null")
null_logger.addHandler(logging.NullHandler())

F = TypeVar("F", bound=Callable[..., Any])


def call_sig(args: Iterator[Any], kwargs: MutableMapping[str, Any]) -> str:
    """Generates a function-like signature of function called with certain parameters.

    Args:
        args: *args
        kwargs: **kwargs

    Returns:
        A string that contains parameters in parentheses like the call to it.
    """
    arglist = [repr(x) for x in args]
    arglist.extend(f"{k}={v!r}" for k, v in kwargs.items())
    return "({args})".format(
        args=", ".join(arglist),
    )


class PrependParentsAdapter(logging.LoggerAdapter):
    """This class ensures the path to the widget is represented in the log records."""

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> Tuple[str, MutableMapping[str, Any]]:
        assert self.extra is not None  # python 3.10+ type check
        widget_path = cast(str, self.extra["widget_path"])
        # Sanitizing %->%% for formatter working properly
        return (
            "[{}]: {}".format(widget_path.replace("%", "%%"), msg),
            kwargs,
        )

    def __repr__(self) -> str:
        assert self.extra is not None  # python 3.10+ type check
        return "{}({!r}, {!r})".format(type(self).__name__, self.logger, self.extra["widget_path"])


def create_widget_logger(
    widget_path: str, logger: Optional[logging.Logger] = None
) -> PrependParentsAdapter:
    """Create a logger that prepends the ``widget_path`` to the log records.

    Args:
        widget_path: A string indicating the path to the widget
        logger: Specify a logger if you want some output, otherwise a null logger will be used.

    Returns:
        A logger instance.
    """
    return PrependParentsAdapter(logger or null_logger, {"widget_path": widget_path})


def _create_logger_appender(parent_logger: logging.Logger, suffix: str) -> PrependParentsAdapter:
    """Generic name-append logger creator."""
    if isinstance(parent_logger, PrependParentsAdapter):
        widget_path = "{}{}".format(parent_logger.extra["widget_path"], suffix)
        logger = parent_logger.logger
    else:
        widget_path = suffix
        logger = parent_logger
    return PrependParentsAdapter(logger, {"widget_path": widget_path.lstrip("/")})


def create_child_logger(parent_logger: logging.Logger, child_name: str) -> PrependParentsAdapter:
    """Creates a logger for a standard child widget.

    Args:
        parent_logger: Logger of the parent widget (or can be plain, in that case this is the
            top-level widget then.
        child_name: Name under which this child widgets is represented.

    Returns:
        A :py:class:`PrependParentsAdapter` logger instance.
    """
    return _create_logger_appender(parent_logger, f"/{child_name}")


def create_item_logger(
    parent_logger: logging.Logger, item: Union[str, int]
) -> PrependParentsAdapter:
    """Creates a logger for a widget that is inside iteration - referred to by index or key.

    Args:
        parent_logger: Logger of the parent widget (or can be plain, in that case this is the
            top-level widget then.
        item: Index or key name under which this widget is represented.

    Returns:
        A :py:class:`PrependParentsAdapter` logger instance.
    """
    return _create_logger_appender(parent_logger, f"[{item!r}]")


def logged(log_args: bool = False, log_result: bool = False) -> Callable[[F], F]:
    """Decorator that logs entry and exit to a method and also times the execution.

    It assumes that the object where you decorate the methods on has a ``.logger`` attribute.

    :py:meth:`widgetastic.widget.Widget.fill` and :py:meth:`widgetastic.widget.Widget.read` are
    automatically wrapped with this call due to usage of
    :py:class:`widgetastic.widget.WidgetMetaclass` which finds all ``fill`` and ``read`` methods and
    wraps them automatically.

    Args:
        log_args: Whether to log args passed to the method
        log_result: Whether to log the result value returned from the method.
    """

    def g(f):
        @functools.wraps(f)
        def wrapped(self, *args, **kwargs):
            start_time = time.time()
            signature = f.__name__ + (call_sig(args, kwargs) if log_args else "")
            self.logger.debug("%s started", signature)
            try:
                result = f(self, *args, **kwargs)
            except DoNotReadThisWidget:
                elapsed_time = (time.time() - start_time) * 1000.0
                self.logger.warning(
                    "%s - not read on widget's request (elapsed %.0f ms)",
                    signature,
                    elapsed_time,
                )
                raise
            except Exception as e:
                elapsed_time = (time.time() - start_time) * 1000.0
                self.logger.error(
                    "An exception happened during %s call (elapsed %.0f ms)",
                    signature,
                    elapsed_time,
                )
                self.logger.exception(e)
                raise
            else:
                elapsed_time = (time.time() - start_time) * 1000.0
                if log_result:
                    self.logger.info("%s -> %r (elapsed %.0f ms)", signature, result, elapsed_time)
                else:
                    self.logger.info("%s (elapsed %.0f ms)", signature, elapsed_time)
                return result

        wrapped.original_function = f
        return wrapped

    return g


def call_unlogged(method, *args, **kwargs):
    """Calls the original method without logging when ``logged`` is applied.

    In case you pass in an ordinary method that was not decorated, it will work as usual.

    Args:
        method: The method object from the object.
        *args: Args to pass to the method.
        **kwargs: Keyword arguments to pass to the method.

    Returns:
        Whatever that method returns.
    """
    try:
        f = method.original_function
    except AttributeError:
        f = method.__func__

    return f(method.__self__, *args, **kwargs)
