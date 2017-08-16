# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import time
from six import wraps, get_method_function, get_method_self, string_types

from .exceptions import DoNotReadThisWidget
from .utils import crop_string_middle


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

    def __repr__(self):
        return '{}({!r}, {!r})'.format(type(self).__name__, self.logger, self.extra['widget_path'])


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


def _create_logger_appender(parent_logger, suffix):
    """Generic name-append logger creator."""
    if isinstance(parent_logger, PrependParentsAdapter):
        widget_path = '{}{}'.format(parent_logger.extra['widget_path'], suffix)
        logger = parent_logger.logger
    else:
        widget_path = suffix
        logger = parent_logger
    return PrependParentsAdapter(logger, {'widget_path': widget_path.lstrip('/')})


def create_child_logger(parent_logger, child_name):
    """Creates a logger for a standard child widget.

    Args:
        parent_logger: Logger of the parent widget (or can be plain, in that case this is the
            top-level widget then.
        child_name: Name under which this child widgets is represented.

    Returns:
        A :py:class:`PrependParentsAdapter` logger instance.
    """
    return _create_logger_appender(parent_logger, '/{}'.format(child_name))


def create_item_logger(parent_logger, item):
    """Creates a logger for a widget that is inside iteration - referred to by index or key.

    Args:
        parent_logger: Logger of the parent widget (or can be plain, in that case this is the
            top-level widget then.
        item: Index or key name under which this widget is represented.

    Returns:
        A :py:class:`PrependParentsAdapter` logger instance.
    """
    return _create_logger_appender(parent_logger, '[{!r}]'.format(item))


def logged(
        log_args=False, log_result=False, only_after=False, debug_only=False,
        log_full_exception=True, string_crop=64):
    """Decorator that logs entry and exit to a method and also times the execution.

    It assumes that the object where you decorate the methods on has a ``.logger`` attribute.

    :py:meth:`widgetastic.widget.Widget.fill` and :py:meth:`widgetastic.widget.Widget.read` are
    automatically wrapped with this call due to usage of
    :py:class:`widgetastic.widget.WidgetMetaclass` which finds all ``fill`` and ``read`` methods and
    wraps them automatically.

    Args:
        log_args: Whether to log args passed to the method
        log_result: Whether to log the result value returned from the method.
        only_after: Whether to log only after the method finished.
        debug_only: Use only debug log level at max.
        log_full_exception: Whether to log the full exceptions.
        string_crop: Length to which to crop the strings if they are return values
    """
    def g(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            if debug_only:
                info_logger = self.logger.debug
            else:
                info_logger = self.logger.info
            start_time = time.time()
            signature = f.__name__ + (call_sig(args, kwargs) if log_args else '')
            if not only_after:
                self.logger.debug('%s started', signature)
            try:
                result = f(self, *args, **kwargs)
            except DoNotReadThisWidget:
                elapsed_time = (time.time() - start_time) * 1000.0
                info_logger(
                    '%s not read on widget\'s request (elapsed %.0f ms)',
                    signature, elapsed_time)
                raise
            except Exception as e:
                elapsed_time = (time.time() - start_time) * 1000.0
                if log_full_exception:
                    self.logger.exception(
                        'An exception happened during %s call (elapsed %.0f ms)',
                        signature, elapsed_time)
                else:
                    self.logger.error(
                        'An exception %s happened during %s call (elapsed %.0f ms)',
                        str(e), signature, elapsed_time)
                raise
            else:
                elapsed_time = (time.time() - start_time) * 1000.0
                if log_result:
                    result_to_log = result
                    if isinstance(result_to_log, string_types):
                        result_to_log = crop_string_middle(result_to_log, length=string_crop)
                    info_logger(
                        '%s -> %r (elapsed %.0f ms)',
                        signature, result_to_log, elapsed_time)
                else:
                    info_logger('%s (elapsed %.0f ms)', signature, elapsed_time)
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
