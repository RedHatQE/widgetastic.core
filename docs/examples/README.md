# Documentation Examples

Executable Python examples for Widgetastic.Core documentation.

## Running Examples

```bash
# Run all examples just like normal pytest run.
pytest docs/examples

# with headless mode
pytest docs/examples --headless
```

## How It Works

**`conftest.py`** collects all `.py` files and runs them as tests:

- **Regular examples**: Get `browser` instance from `browser_setup.py`
- **Standalone examples** (with `sync_playwright`): Run in subprocess with their own browser setup
