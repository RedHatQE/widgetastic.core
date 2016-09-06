# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest

import codecs
import os
import sys

from selenium import webdriver

from widgetastic.core.browser import Browser


@pytest.fixture(scope='function')
def browser(httpserver, request):
    this_module = sys.modules[__name__]
    path = os.path.dirname(this_module.__file__)
    testfilename = path + '/testing_page.html'
    httpserver.serve_content(codecs.open(testfilename, mode='r', encoding='utf-8').read())
    driver = webdriver.PhantomJS()
    request.addfinalizer(driver.quit)
    driver.maximize_window()
    driver.get(httpserver.url)
    return Browser(driver)
