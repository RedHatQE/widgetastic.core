# Widgetastic.Core Documentation

This directory contains the comprehensive documentation for widgetastic.core, completely redesigned to provide a superior learning experience for developers using this powerful web automation framework.

## 📖 Documentation Overview

The new documentation structure provides:

### 🚀 **Getting Started** - Your First Steps
- **Installation**: Complete setup guide with troubleshooting
- **Core Concepts**: Essential widgetastic concepts explained clearly
- **First Steps**: Your first working automation script

### ⚡ **Quick Start** - Immediate Practical Examples
- **Basic Example**: Complete automation workflows
- **Common Patterns**: Real-world usage patterns and best practices

### 🎓 **Tutorials** - Step-by-Step Learning
- **Basic Widgets**: Master all fundamental widget types
- **Views & Navigation**: Page organization and structure
- **Advanced Features**: Complex scenarios and patterns
- **Testing Integration**: Framework integration patterns

### 📚 **User Guide** - Comprehensive Reference
- **Widgets**: Complete widget documentation
- **Views**: Advanced view patterns
- **Browser**: Browser automation features
- **Advanced Topics**: Version picking, conditional views, OUIA

### 📋 **API Reference** - Complete Technical Documentation
- **Browser API**: All browser methods and properties
- **Widget API**: Every widget class and method
- **View API**: View system documentation
- **Utilities**: Helper classes and functions

### 💡 **Examples** - Real-World Implementations
- **Form Automation**: Complete form handling examples
- **Table Operations**: Data extraction and manipulation
- **Testing Patterns**: Integration with testing frameworks
- **Best Practices**: Production-ready automation patterns

## 🏗️ Building the Documentation

### Prerequisites

```bash
# Install Sphinx and dependencies
pip install sphinx sphinx_rtd_theme

# For the full documentation experience, install widgetastic.core
pip install widgetastic.core
```

### Building HTML Documentation

```bash
cd new-docs
sphinx-build -b html . _build/html
```

The documentation will be built in `_build/html/`. Open `_build/html/index.html` in your browser to view.

### Live Development Server

For live reloading during development:

```bash
pip install sphinx-autobuild
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

## 📁 Documentation Structure

```
new-docs/
├── index.rst                     # Main documentation index
├── conf.py                       # Sphinx configuration
├── _static/
│   └── custom.css                # Custom styling
├── _templates/                   # Custom templates
├── getting-started/
│   ├── installation.rst         # Installation guide
│   ├── concepts.rst              # Core concepts
│   └── first-steps.rst          # First automation script
├── quickstart/
│   ├── index.rst                # Quick start overview
│   ├── basic-example.rst        # Complete working example
│   └── common-patterns.rst      # Common usage patterns
├── tutorials/
│   ├── index.rst                # Tutorial overview
│   ├── basic-widgets.rst        # Basic widget tutorial
│   ├── views-and-navigation.rst # View system tutorial
│   ├── advanced-widgets.rst     # Advanced widget patterns
│   └── ... (more tutorials)
├── user-guide/
│   ├── index.rst                # User guide overview
│   ├── widgets.rst              # Widget user guide
│   ├── views.rst                # View user guide
│   └── ... (more guides)
├── api-reference/
│   ├── index.rst                # API reference overview
│   ├── browser.rst              # Browser API documentation
│   ├── widgets.rst              # Widget API documentation
│   └── ... (more API docs)
├── examples/
│   └── ... (practical examples)
├── advanced/
│   └── ... (advanced topics)
├── migration/
│   └── ... (migration guides)
└── faq/
    └── ... (frequently asked questions)
```

## 🎨 Design Philosophy

This documentation follows modern documentation best practices:

### **Progressive Disclosure**
- Start simple, add complexity gradually
- Each section builds on previous knowledge
- Clear learning paths for different user types

### **Learning by Doing**
- Every concept includes working code examples
- Complete, runnable examples in tutorials
- Real-world scenarios rather than toy examples

### **Multiple Learning Styles**
- **Quick Start**: For hands-on learners who want immediate results
- **Tutorials**: For step-by-step learners who prefer guided instruction
- **User Guide**: For reference-oriented learners who need comprehensive coverage
- **API Reference**: For developers who need technical details

### **Accessibility and Usability**
- Clear navigation and structure
- Searchable content
- Mobile-responsive design
- Print-friendly styling
- Dark mode support

## 🔧 Customization

### Themes

The documentation uses the `sphinx_rtd_theme` with extensive customizations in `_static/custom.css`. Key features:

- **Enhanced Typography**: Improved readability with modern font stacks
- **Color Scheme**: Consistent branding with widgetastic colors
- **Code Highlighting**: Better syntax highlighting for Python and web technologies
- **Responsive Grid**: Card-based layouts for better organization
- **Interactive Elements**: Hover effects and visual feedback

### Configuration

Key configuration in `conf.py`:

```python
# Theme and extensions
html_theme = 'sphinx_rtd_theme'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
]

# Autodoc configuration
autodoc_member_order = 'bysource'
autosummary_generate = True

# Cross-referencing
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'playwright': ('https://playwright.dev/python/', None),
}
```

## 📝 Contributing to Documentation

### Writing Guidelines

1. **Examples First**: Start with working code, then explain
2. **Complete Context**: Provide full, runnable examples
3. **Progressive Complexity**: Build from simple to advanced
4. **Cross-References**: Link related concepts liberally
5. **User Perspective**: Write from the user's point of view

### Content Standards

- **Code Quality**: All examples must be tested and functional
- **Consistency**: Use consistent terminology and patterns
- **Clarity**: Prefer clear, simple explanations over clever ones
- **Completeness**: Cover edge cases and error scenarios

### Style Guide

```rst
Page Title (Using = Above and Below)
====================================

Section Heading (Using -)
--------------------------

Subsection (Using ^)
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
   :caption: Example caption
   :linenos:

   # Well-commented, complete examples
   from widgetastic.widget import View, TextInput

   class MyView(View):
       username = TextInput("#username")

.. note::
   Use admonitions sparingly but effectively

.. tip::
   Pro tips help users avoid common pitfalls
```

### Adding New Content

1. **New Tutorials**: Follow the structure in `tutorials/basic-widgets.rst`
2. **New Examples**: Place in appropriate examples subdirectory
3. **API Documentation**: Use autodoc for consistency
4. **Cross-References**: Update related sections with links

## 🚀 Deployment

### GitHub Pages

The documentation can be deployed to GitHub Pages:

```bash
# Build documentation
sphinx-build -b html . _build/html

# Deploy to gh-pages branch
# (Use your preferred GitHub Pages deployment method)
```

### Read the Docs

For automatic building and hosting on Read the Docs:

1. Connect your repository to Read the Docs
2. Configure the build settings:
   - Python version: 3.10+
   - Requirements file: `docs/requirements.txt` (create if needed)
   - Sphinx configuration file: `new-docs/conf.py`

### Docker Deployment

```dockerfile
FROM sphinxdoc/sphinx

COPY requirements.txt /docs/
RUN pip install -r /docs/requirements.txt

COPY . /docs
WORKDIR /docs

RUN sphinx-build -b html . _build/html

EXPOSE 8000
CMD ["python", "-m", "http.server", "8000", "--directory", "_build/html"]
```

## 📊 Analytics and Feedback

### User Analytics

Consider integrating:
- Google Analytics for usage tracking
- Hotjar for user behavior insights
- Search analytics to improve content discoverability

### Feedback Collection

- GitHub issues for bug reports and suggestions
- Community forums for questions and discussions
- Survey forms for structured feedback
- Comment systems for page-specific feedback

## 🔍 Quality Assurance

### Documentation Testing

```bash
# Check for broken links
sphinx-build -b linkcheck . _build/linkcheck

# Test code examples
# (Run pytest on extracted code examples)

# Check spelling
sphinx-build -b spelling . _build/spelling
```

### Review Checklist

- [ ] All code examples tested and working
- [ ] Cross-references and links functional
- [ ] Consistent terminology throughout
- [ ] Mobile-responsive layout verified
- [ ] Search functionality working
- [ ] Print layout acceptable
- [ ] Dark mode rendering correct

## 📈 Success Metrics

Track these metrics to measure documentation success:

- **Discovery**: Search rankings, referral traffic
- **Engagement**: Time on page, bounce rate, page views
- **Effectiveness**: Task completion rates, support ticket reduction
- **Satisfaction**: User surveys, feedback sentiment
- **Adoption**: Framework usage growth, community activity

## 🤝 Community

- **Discussions**: [GitHub Discussions](https://github.com/RedHatQE/widgetastic.core/discussions)
- **Issues**: [Bug Reports & Feature Requests](https://github.com/RedHatQE/widgetastic.core/issues)
- **Contributing**: See `CONTRIBUTING.md` for development guidelines
- **Chat**: Join our community chat for real-time discussion

---

This documentation represents a complete reimagining of how developers learn and use widgetastic.core. It's designed to scale from beginner tutorials to advanced architectural patterns, providing value at every stage of the learning journey.

**Happy documenting!** 📚✨
