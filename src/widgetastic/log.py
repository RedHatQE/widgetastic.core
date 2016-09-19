# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import time
from six import wraps


null_logger = logging.getLogger('widgetastic_null')
null_logger.addHandler(logging.NullHandler())


class PrependParentsAdapter(logging.LoggerAdapter):
    """This class ensures the path to the widget is represented in the log records."""
    def process(self, msg, kwargs):
        return '[{}]: {}'.format(self.extra['widget_path'], msg), kwargs


def create_widget_logger(widget_path, logger=None):
    """Create a logger that prepends the ``widget_path`` to the log records."""
    return PrependParentsAdapter(
        logger or null_logger,
        {'widget_path': widget_path})


def logged(log_args=False, log_result=False):
    def g(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            start_time = time.time()
            if log_args:
                signature = '{}{!r}{!r}'.format(f.__name__, args, kwargs)
            else:
                signature = f.__name__
            self.logger.debug('%s started', signature)
            result = f(self, *args, **kwargs)
            elapsed_time = (time.time() - start_time) * 1000.0
            if log_result:
                self.logger.info('%s -> %r (elapsed %.0f ms)', signature, result, elapsed_time)
            else:
                self.logger.info('%s (elapsed %.0f ms)', signature, elapsed_time)
            return result

        return wrapped

    return g
