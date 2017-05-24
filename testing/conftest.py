# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest

import codecs
import logging
import os
import sys

from selenium import webdriver

from widgetastic.browser import Browser

selenium_browser = None


# Browser logger
browser_logger = logging.getLogger('widgetastic_browser')
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
out_hdlr.setLevel(logging.DEBUG)
browser_logger.addHandler(out_hdlr)
browser_logger.setLevel(logging.DEBUG)


class CustomBrowser(Browser):
    @property
    def product_version(self):
        return '1.0.0'


@pytest.fixture(scope='session')
def selenium(request):
    driver = webdriver.PhantomJS()
    request.addfinalizer(driver.quit)
    driver.maximize_window()
    global selenium_browser
    selenium_browser = driver
    return driver


@pytest.fixture(scope='function')
def browser(selenium, httpserver, request):
    this_module = sys.modules[__name__]
    path = os.path.dirname(this_module.__file__)
    testfilename = os.path.join(path, 'testing_page.html')
    httpserver.serve_content(codecs.open(testfilename, mode='r', encoding='utf-8').read())
    b = CustomBrowser(selenium, logger=browser_logger)
    b.url = httpserver.url
    return b
