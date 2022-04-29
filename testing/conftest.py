import os
from urllib.request import urlopen

import pytest
from podman import PodmanClient
from selenium import webdriver
from wait_for import wait_for

from widgetastic.browser import Browser


OPTIONS = {"firefox": webdriver.FirefoxOptions(), "chrome": webdriver.ChromeOptions()}


def pytest_addoption(parser):
    parser.addoption(
        "--browser-name",
        help="Name of the browser, can also be set in env with BROWSER",
        choices=("firefox", "chrome"),
        default="firefox",
    )


@pytest.fixture(scope="session")
def podman():
    runtime_dir = os.getenv("XDG_RUNTIME_DIR")
    uri = f"unix://{runtime_dir}/podman/podman.sock"
    with PodmanClient(base_url=uri) as client:
        yield client


@pytest.fixture(scope="session")
def pod(podman, worker_id):
    last_oktet = 1 if worker_id == "master" else int(worker_id.lstrip("gw")) + 1
    localhost_for_worker = f"127.0.0.{last_oktet}"
    pod = podman.pods.create(
        f"widgetastic_testing_{last_oktet}",
        portmappings=[
            {"host_ip": localhost_for_worker, "container_port": 5999, "host_port": 5999},
            {"host_ip": localhost_for_worker, "container_port": 4444, "host_port": 4444},
        ],
    )
    pod.start()
    yield pod
    pod.remove(force=True)


@pytest.fixture(scope="session")
def browser_name(pytestconfig):
    return os.environ.get("BROWSER") or pytestconfig.getoption("--browser-name")


@pytest.fixture(scope="session")
def selenium_url(worker_id, podman, pod):
    """Yields a command executor URL for selenium, and a port mapped for the test page to run on"""
    # use the worker id number from gw# to create hosts on loopback
    last_oktet = 1 if worker_id == "master" else int(worker_id.lstrip("gw")) + 1
    localhost_for_worker = f"127.0.0.{last_oktet}"
    container = podman.containers.create(
        image="quay.io/redhatqe/selenium-standalone:ff_91.8.0esr_chrome_101.0.4951.41",
        pod=pod.id,
        remove=True,
        name=f"selenium_{worker_id}",
    )
    container.start()
    yield f"http://{localhost_for_worker}:4444"
    container.remove(force=True)


@pytest.fixture(scope="session")
def testing_page_url(worker_id, podman, pod):
    container = podman.containers.create(
        image="docker.io/library/nginx:alpine",
        pod=pod.id,
        remove=True,
        name=f"web_server_{worker_id}",
        mounts=[
            {
                "source": f"{os.getcwd()}/testing/html",
                "target": "/usr/share/nginx/html",
                "type": "bind",
            }
        ],
    )
    container.start()
    yield "http://127.0.0.1/testing_page.html"
    container.remove(force=True)


@pytest.fixture(scope="session")
def selenium_webdriver(browser_name, selenium_url, testing_page_url):
    wait_for(urlopen, func_args=[selenium_url], timeout=180, handle_exception=True)
    driver = webdriver.Remote(command_executor=selenium_url, options=OPTIONS[browser_name.lower()])
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
