# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import time
from six import wraps, get_method_function, get_method_self

from .exceptions import DoNotReadThisWidget


null_logger = logging.getLogger('widgetastic_null')
null_logger.addHandler(logging.NullHandler())


def call_sig(args, kwargs):
    """Generates a function-like signature of function called with certain parameters.

    Args:
        args: *args
        kwargs: **kwargs

    Returns:
        A string that contains parameters in parentheses like the call to it.
    """
    arglist = [repr(x) for x in args]
    arglist.extend("{0}={1!r}".format(k, v) for k, v in kwargs.items())
    return "({args})".format(
        args=', '.join(arglist),
    )


class PrependParentsAdapter(logging.LoggerAdapter):
    """This class ensures the path to the widget is represented in the log records."""
    def process(self, msg, kwargs):
        return '[{}]: {}'.format(self.extra['widget_path'], msg), kwargs


def create_widget_logger(widget_path, logger=None):
    """Create a logger that prepends the ``widget_path`` to the log records.

    Args:
        widget_path: A string indicating the path to the widget
        logger: Specify a logger if you want some output, otherwise a null logger will be used.

    Returns:
        A logger instance.
    """
    return PrependParentsAdapter(
        logger or null_logger,
        {'widget_path': widget_path})


def logged(log_args=False, log_result=False):
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
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            start_time = time.time()
            signature = f.__name__ + (call_sig(args, kwargs) if log_args else '')
            self.logger.debug('%s started', signature)
            try:
                result = f(self, *args, **kwargs)
            except DoNotReadThisWidget:
                elapsed_time = (time.time() - start_time) * 1000.0
                self.logger.info(
                    '%s not read on widget\'s request (elapsed %.0f ms)',
                    signature, elapsed_time)
                raise
            except Exception as e:
                elapsed_time = (time.time() - start_time) * 1000.0
                self.logger.error(
                    'An exception happened during %s call (elapsed %.0f ms)',
                    signature, elapsed_time)
                self.logger.exception(e)
                raise
            else:
                elapsed_time = (time.time() - start_time) * 1000.0
                if log_result:
                    self.logger.info('%s -> %r (elapsed %.0f ms)', signature, result, elapsed_time)
                else:
                    self.logger.info('%s (elapsed %.0f ms)', signature, elapsed_time)
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
        f = get_method_function(method)

    return f(get_method_self(method), *args, **kwargs)
