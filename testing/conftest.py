import os
from urllib.request import urlopen

import pytest
from podman import PodmanClient
from selenium import webdriver
from wait_for import wait_for

from widgetastic.browser import Browser
from playwright.sync_api import sync_playwright, Page


OPTIONS = {
    "firefox": webdriver.FirefoxOptions(),
    "chrome": webdriver.ChromeOptions(),
    "chromium": webdriver.ChromeOptions(),
}


def pytest_addoption(parser):
    parser.addoption(
        "--browser-name",
        help="Name of the browser, can also be set in env with BROWSER",
        choices=("firefox", "chromium"),
        default="chromium",
    )
    parser.addoption(
        "--engine",
        help="Browser automation engine to use: Selenium or Playwright",
        choices=("selenium", "playwright"),
        default="selenium",
    )
    parser.addoption(
        "--trace_view",
        action="store_true",
        help="Enable tracing for Playwright tests",
        default=False,
    )
    parser.addoption(
        "--record_video",
        action="store_true",
        help="Enable video recording for Playwright tests",
        default=False,
    )
    parser.addoption(
        "--headless", action="store_true", help="Run the browser in headless mode", default=False
    )


@pytest.fixture(scope="session")
def podman():
    runtime_dir = os.getenv("XDG_RUNTIME_DIR")
    uri = f"unix://{runtime_dir}/podman/podman.sock"
    uri = "http://localhost:8080"
    with PodmanClient(base_url=uri) as client:
        yield client


@pytest.fixture(scope="session")
def pod(podman, worker_id):
    last_oktet = 1 if worker_id == "master" else int(worker_id.lstrip("gw")) + 1
    localhost_for_worker = f"127.0.0.{last_oktet}"
    pod = podman.pods.create(
        f"widgetastic_testing_{last_oktet}",
        portmappings=[
            {"host_ip": localhost_for_worker, "container_port": 7900, "host_port": 7900},
            {"host_ip": localhost_for_worker, "container_port": 4444, "host_port": 4444},
            {"host_ip": localhost_for_worker, "container_port": 80, "host_port": 8081},
        ],
    )
    pod.start()
    yield pod
    pod.remove(force=True)


@pytest.fixture(scope="session")
def browser_type(pytestconfig):
    return os.environ.get("BROWSER") or pytestconfig.getoption("--browser-name")


@pytest.fixture(scope="session")
def engine_url(worker_id, browser_type, podman, pod, request):
    """Yields a command executor URL for Selenium or Playwright based on the engine selection."""
    engine = request.config.getoption("--engine")

    if engine == "selenium":
        # Set up Selenium container
        last_oktet = 1 if worker_id == "master" else int(worker_id.lstrip("gw")) + 1
        localhost_for_worker = f"127.0.0.{last_oktet}"
        container = podman.containers.create(
            image=f"docker.io/selenium/standalone-{browser_type}:latest",
            pod=pod.id,
            remove=True,
            name=f"selenium_{worker_id}",
            environment={"SE_VNC_NO_PASSWORD": "1"},
        )
        container.start()
        yield f"http://{localhost_for_worker}:4444"
        container.remove(force=True)
    else:
        # Skip Selenium setup if Playwright is used
        yield None


@pytest.fixture(scope="session")
def testing_page_url(request, worker_id, podman, pod):
    engine = request.config.getoption("--engine")
    port = "8081" if engine == "playwright" else "80"
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
                "relabel": "Z",
            }
        ],
    )
    container.start()
    yield f"http://127.0.0.1:{port}/testing_page.html"
    container.remove(force=True)


@pytest.fixture(scope="session")
def engine_driver(browser_type, engine_url, testing_page_url, request):
    """Initialize and yield either Selenium WebDriver or Playwright browser based on the engine selection."""
    engine = request.config.getoption("--engine")

    if engine == "selenium":
        # Wait for Selenium container to be ready
        wait_for(urlopen, func_args=[engine_url], timeout=180, handle_exception=True)
        driver = webdriver.Remote(
            command_executor=engine_url, options=OPTIONS[browser_type.lower()]
        )
        driver.maximize_window()
        driver.get(testing_page_url)
        yield driver
        driver.quit()
    elif engine == "playwright":
        # Initialize Playwright browser
        enable_trace = request.config.getoption("--trace_view")
        enable_video = request.config.getoption("--record_video")
        headless = request.config.getoption("--headless")

        with sync_playwright() as p:
            # Select the browser engine
            browser = getattr(p, browser_type.lower()).launch(headless=headless)

            # Set up context options based on flags
            context_options = {}
            if enable_video:
                context_options = {
                    "record_video_dir": "videos/",
                    "record_video_size": {"width": 640, "height": 480},
                }
            context = browser.new_context(**context_options)

            # Start tracing if enabled
            if enable_trace:
                context.tracing.start(screenshots=True, snapshots=True, sources=True)

            page = context.new_page()
            page.goto(testing_page_url)
            yield page

            # Cleanup
            if enable_trace:
                context.tracing.stop(path="trace.zip")
            page.close()
            context.close()
            browser.close()


class CustomBrowser(Browser):
    @property
    def product_version(self):
        return "1.0.0"


@pytest.fixture(scope="session")
def custom_browser(engine_driver):
    if isinstance(engine_driver, Page):  # this is for playwright
        return CustomBrowser(page=engine_driver)
    return CustomBrowser(engine_driver)


@pytest.fixture(scope="function")
def browser(engine_driver, custom_browser):
    yield custom_browser
    if isinstance(engine_driver, Page):
        engine_driver.reload()
    else:
        engine_driver.refresh()
