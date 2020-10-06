# -*- coding: utf-8 -*-
import codecs
import os
import sys
import subprocess
from urllib.request import urlopen

import pytest
from pytest_localserver.http import ContentServer, Request, Response
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import urlsplit
from wait_for import wait_for

from widgetastic.browser import Browser


# Begging, borrowing, and stealing from @quarkster
# https://github.com/RedHatQE/widgetastic.patternfly4/blob/master/testing/conftest.py#L21


def pytest_addoption(parser):
    parser.addoption(
        "--browser-name",
        help="Name of the browser, can also be set in env with BROWSER",
        choices=("firefox", "chrome"),
        default="firefox",
    )
    parser.addoption(
        "--selenium-host",
        default=None,
        help="Use the given host for selenium, (hostname only, defaults to http and port 4444)"
             "instead of running selenium container automatically")


@pytest.fixture(scope="session")
def browser_name(pytestconfig):
    return os.environ.get("BROWSER") or pytestconfig.getoption("--browser-name")


@pytest.fixture(scope="session")
def selenium_url(pytestconfig, worker_id):
    """Yields a command executor URL for selenium, and a port mapped for the test page to run on"""
    given_host = pytestconfig.getoption("--selenium-host")

    webdriver_url = "http://{}:4444/wd/hub"
    if given_host:
        yield webdriver_url.format(given_host)
    else:
        # use the worker id number from gw# to create hosts on loopback
        last_octet = 1 if worker_id == "master" else int(worker_id.lstrip("gw")) + 1
        localhost_for_worker = f"127.0.0.{last_octet}"
        ps = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--network",  # for the ephemeral port mapping back to ContentServer
                "host",
                "--shm-size=2g",
                "quay.io/redhatqe/selenium-standalone:latest",
            ],
            stdout=subprocess.PIPE,
        )

        yield webdriver_url.format(localhost_for_worker)
        container_id = ps.stdout.decode("utf-8").strip()
        subprocess.run(["docker", "kill", container_id], stdout=subprocess.DEVNULL)


@pytest.fixture(scope="module")
def selenium_webdriver(browser_name, selenium_url):
    wait_for(urlopen, func_args=[selenium_url], timeout=180, handle_exception=True)
    if browser_name == "firefox":
        desired_capabilities = DesiredCapabilities.FIREFOX.copy()
    else:
        desired_capabilities = DesiredCapabilities.CHROME.copy()
        desired_capabilities["chromeOptions"] = {
            "args": [
                "no-sandbox",
                "disable-infobars"
                "start-maximized",
            ]
        }

    driver = webdriver.Remote(
        command_executor=selenium_url,
        desired_capabilities=desired_capabilities
    )
    yield driver
    driver.quit()


class SampleContentServer(ContentServer):
    def __init__(self, *args, **kwargs):
        this_module = sys.modules[__name__]
        self.path = os.path.join(os.path.dirname(this_module.__file__), 'html')
        super(SampleContentServer, self).__init__(*args, **kwargs)

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
            content = f"wrong url {request.url}"
            code = 404

        response = Response(status=code)
        response.headers.clear()
        response.headers.extend(self.headers)

        response.data = content
        return response(environ, start_response)


@pytest.fixture(scope='module')
def test_server(selenium_url):
    server = SampleContentServer()
    server.start()
    yield server
    server.stop()


class CustomBrowser(Browser):
    @property
    def product_version(self):
        return '1.0.0'


@pytest.fixture(scope='function')
def browser(selenium_webdriver, test_server):
    cb = CustomBrowser(selenium_webdriver)
    selenium_webdriver.get(test_server.url)
    yield cb
    selenium_webdriver.refresh()
