# Widgetastic.Core Documentation

This directory contains the comprehensive documentation for widgetastic.core, provide a superior learning experience for developers using this powerful web automation framework.

## 🏗️ Building the Documentation

### Prerequisites

```bash
# For the full documentation experience, install widgetastic.core with doc dependencies.
pip install -e .[docs]
```

### Building HTML Documentation

```bash
cd docs
sphinx-build -b html . _build/html
```

The documentation will be built in `_build/html/`. Open `_build/html/index.html` in your browser to view.

### Live Development Server

For live reloading during development:

```bash
sphinx-autobuild . _build/html --watch ../src
```

This will start a development server at `http://localhost:8000` with automatic rebuilding when files change.

### Building Other Formats

```bash
# PDF documentation
sphinx-build -b latex . _build/latex
cd _build/latex && make

# EPUB format
sphinx-build -b epub . _build/epub

# Single HTML file
sphinx-build -b singlehtml . _build/singlehtml
```
