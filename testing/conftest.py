# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import allure
import pytest

import codecs
import os
import sys

from selenium import webdriver

from widgetastic.browser import Browser

selenium_browser = None


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
    testfilename = path + '/testing_page.html'
    httpserver.serve_content(codecs.open(testfilename, mode='r', encoding='utf-8').read())
    selenium.get(httpserver.url)
    return CustomBrowser(selenium)


def pytest_exception_interact(node, call, report):
    if selenium_browser is not None:
        allure.attach(
            'Error screenshot', selenium_browser.get_screenshot_as_png(), allure.attach_type.PNG)
        allure.attach('Error traceback', str(report.longrepr), allure.attach_type.TEXT)
