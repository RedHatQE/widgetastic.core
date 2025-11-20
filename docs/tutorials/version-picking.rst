.. _version-picking:

===============
Version picking
===============

This tutorial demonstrates version picking in Widgetastic.core, a powerful feature for handling application evolution and multiple product versions.
You'll learn to create version-aware widgets/views that adapt to different application versions automatically.



Understanding Version Picking
=============================

Version picking allows widgets and views to adapt their behavior based on the application version being tested:

**Why Version Picking is Important**

* **Application Evolution**: UI changes between software versions
* **Backward Compatibility**: Support testing multiple versions simultaneously
* **Maintenance Efficiency**: Single test suite for multiple product versions
* **Gradual Migration**: Smooth transitions between widget implementations

Setting Up Version Picking Environment
======================================

.. literalinclude:: ../examples/version-picking/version_picking.py
   :language: python
   :start-after: # Example: Setting Up Version Picking Environment
   :end-before: # End of Example: Setting Up Version Picking Environment


Basic Version Picking
=====================

Start with simple version-dependent widget definitions:

**Simple Version Pick Example**

In this example, we want to select input and click button for different versions.

* Default/fallback (v1.x): TextInput (name=fill_with_1) and Button (id=#fill_with_button_1)
* Version 2.0.0+ (v2.x): TextInput (name=fill_with_2) and Button (id=#fill_with_button_2)

.. literalinclude:: ../examples/version-picking/version_picking.py
   :language: python
   :start-after: # Example: Basic Version Picking
   :end-before: # End of Example: Basic Version Picking
