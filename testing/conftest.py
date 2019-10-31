# -*- coding: utf-8 -*-
import pytest

import codecs
import os
import sys

from pytest_localserver.http import ContentServer, Request, Response
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import urlsplit

from widgetastic.browser import Browser

selenium_browser = None


class CustomBrowser(Browser):
    @property
    def product_version(self):
        return '1.0.0'


@pytest.fixture(scope="module")
def selenium():
    if os.environ["BROWSER"] == "firefox":
        driver = webdriver.Remote(desired_capabilities=DesiredCapabilities.FIREFOX)
    elif os.environ["BROWSER"] == "chrome":
        caps = DesiredCapabilities.CHROME.copy()
        caps["chromeOptions"] = {"args": ["--no-sandbox", "--disable-infobars"]}
        driver = webdriver.Remote(desired_capabilities=caps)
    global selenium_browser
    selenium_browser = driver
    yield driver
    driver.quit()


@pytest.fixture(scope='module')
def test_server(request):
    class TestContentServer(ContentServer):

        def __init__(self, *args, **kwargs):
            this_module = sys.modules[__name__]
            self.path = os.path.join(os.path.dirname(this_module.__file__), 'html')
            super(TestContentServer, self).__init__(*args, **kwargs)

        def __call__(self, environ, start_response):
            """
            This is the WSGI application.
            """
            request = Request(environ)
            self.requests.append(request)

            code = 200
            if request.url.endswith('/'):
                file = os.path.join(self.path, 'testing_page.html')
            elif request.url.endswith('.html'):
                url_path = urlsplit(request.url).path
                filename = os.path.split(url_path)[-1]
                file = os.path.join(self.path, filename)
            else:
                file = ''
                code = 404

            if os.path.exists(file):
                content = codecs.open(file, mode='r', encoding='utf-8').read()
            else:
                content = "wrong url {}".format(request.url)
                code = 404

            response = Response(status=code)
            response.headers.clear()
            response.headers.extend(self.headers)

            response.data = content
            return response(environ, start_response)

    server = TestContentServer()
    server.start()
    request.addfinalizer(server.stop)
    return server


@pytest.fixture(scope='function')
def browser(selenium, test_server):
    selenium.maximize_window()
    b = CustomBrowser(selenium)
    b.url = test_server.url
    return b
