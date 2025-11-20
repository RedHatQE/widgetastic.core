"""Pytest configuration for documentation examples."""

import os
import pytest
from pathlib import Path
import sys

EXCLUDED_NAMES = {"__init__.py", "conftest.py"}

# Add project source to Python path for widgetastic imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Add examples directory to path for browser_setup import
examples_dir = Path(__file__).parent
sys.path.insert(0, str(examples_dir))


def pytest_addoption(parser):
    """Add command-line options for example tests."""
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run tests in headless mode (no browser window). Default is headed mode locally, headless in CI.",
    )


def pytest_ignore_collect(collection_path, config):
    """Ignore standard Python files - we collect them manually."""
    if not isinstance(collection_path, Path):
        collection_path = Path(collection_path)

    if collection_path.name in EXCLUDED_NAMES:
        return True

    if collection_path.suffix == ".py":
        return True

    return False


def pytest_collect_directory(path, parent):
    """Collect example files from directories."""
    if not isinstance(path, Path):
        path = Path(path)

    try:
        path.relative_to(Path(examples_dir))
    except ValueError:
        return None

    return ExampleDirectory.from_parent(parent, path=path)


class ExampleDirectory(pytest.Directory):
    """Directory collector for example files."""

    def collect(self):
        for py_file in self.path.glob("*.py"):
            if py_file.name not in EXCLUDED_NAMES:
                yield ExampleItem.from_parent(self, name=py_file.name, example_file=py_file)

        for subdir in self.path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith(("_", ".")):
                yield ExampleDirectory.from_parent(self, path=subdir)


class ExampleItem(pytest.Item):
    """Test item for a single example file."""

    def __init__(self, name, parent, example_file):
        super().__init__(name, parent)
        self.example_file = (
            Path(example_file) if not isinstance(example_file, Path) else example_file
        )

    def runtest(self):
        """Execute the example file."""
        import subprocess

        with open(self.example_file, "r") as f:
            code = f.read()

        has_own_browser = "sync_playwright" in code

        if has_own_browser:
            # Validate the file path is within the examples directory for security
            try:
                resolved_path = self.example_file.resolve()
                examples_path = Path(examples_dir).resolve()
                resolved_path.relative_to(examples_path)
            except (ValueError, OSError):
                raise ValueError(
                    f"Example file path {self.example_file} is outside the examples directory"
                )

            # Ensure it's a Python file
            if resolved_path.suffix != ".py":
                raise ValueError(f"Example file must be a Python file: {self.example_file}")

            result = subprocess.run(
                [sys.executable, str(resolved_path)],
                cwd=str(resolved_path.parent),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise Exception(
                    f"Example failed with exit code {result.returncode}\n"
                    f"STDOUT:\n{result.stdout}\n"
                    f"STDERR:\n{result.stderr}"
                )
            if result.stdout:
                print(result.stdout, end="")
            return

        namespace = {
            "__name__": "__main__",
            "__file__": str(self.example_file),
            "__builtins__": __builtins__,
            "browser": self.session.config._browser_instance,
        }

        exec(compile(code, str(self.example_file), "exec"), namespace)

    def repr_failure(self, excinfo):
        return f"Example {self.name} failed: {excinfo.value}"

    def reportinfo(self):
        return self.example_file, 0, f"example: {self.name}"


def pytest_configure(config):
    """Setup browser instance for all tests."""
    # Determine headless mode: --headless flag OR CI environment
    headless = config.getoption("--headless") or os.getenv("CI", "false").lower() == "true"

    # Set environment variable for browser_setup to use
    os.environ["PLAYWRIGHT_HEADLESS"] = str(headless).lower()

    from browser_setup import browser

    browser.refresh(wait_until="load")
    config._browser_instance = browser
