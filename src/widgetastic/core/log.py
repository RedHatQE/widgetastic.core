# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import time
from six import wraps


def create_base_logger(name):
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s] %(message)s")
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    logger.addHandler(ch)

    return logger


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
