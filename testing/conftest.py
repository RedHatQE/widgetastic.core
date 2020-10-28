# -*- coding: utf-8 -*-
import os
import socket
import subprocess
from urllib.request import urlopen

import pytest
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
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
        "instead of running selenium container automatically",
    )


@pytest.fixture(scope="session")
def ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


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
                "podman",
                "run",
                "--rm",
                f"--name=selenium_{last_octet}",
                "-d",
                "-p",
                f"{localhost_for_worker}:4444:4444",
                "-p",
                f"{localhost_for_worker}:5999:5999",
                "--shm-size=2g",
                "quay.io/redhatqe/selenium-standalone:latest",
            ],
            stdout=subprocess.PIPE,
        )

        yield webdriver_url.format(localhost_for_worker)
        container_id = ps.stdout.decode("utf-8").strip()
        subprocess.run(["podman", "kill", container_id], stdout=subprocess.DEVNULL)


@pytest.fixture(scope="session")
def testing_page_url(worker_id, ip):
    port_number = 8080 if worker_id == "master" else int(worker_id.lstrip("gw")) + 8080
    nginx_address = f"{ip}:{port_number}"
    ps = subprocess.run(
        [
            "podman",
            "run",
            "--rm",
            "-d",
            "-p",
            f"{nginx_address}:80",
            "-v",
            f"{os.getcwd()}/testing/html:/usr/share/nginx/html:ro",
            "docker.io/library/nginx:alpine",
        ],
        stdout=subprocess.PIPE,
    )

    yield f"http://{nginx_address}/testing_page.html"
    container_id = ps.stdout.decode("utf-8").strip()
    subprocess.run(["podman", "kill", container_id], stdout=subprocess.DEVNULL)


@pytest.fixture(scope="session")
def selenium_webdriver(browser_name, selenium_url, testing_page_url):
    wait_for(urlopen, func_args=[selenium_url], timeout=180, handle_exception=True)
    if browser_name == "firefox":
        desired_capabilities = DesiredCapabilities.FIREFOX.copy()
    else:
        desired_capabilities = DesiredCapabilities.CHROME.copy()
        desired_capabilities["chromeOptions"] = {"args": ["--no-sandbox"]}

    driver = webdriver.Remote(
        command_executor=selenium_url, desired_capabilities=desired_capabilities
    )
    driver.maximize_window()
    driver.get(testing_page_url)
    yield driver
    driver.quit()


class CustomBrowser(Browser):
    @property
    def product_version(self):
        return "1.0.0"


@pytest.fixture(scope="session")
def custom_browser(selenium_webdriver):
    return CustomBrowser(selenium_webdriver)


@pytest.fixture(scope="function")
def browser(selenium_webdriver, custom_browser):
    yield custom_browser
    selenium_webdriver.refresh()
