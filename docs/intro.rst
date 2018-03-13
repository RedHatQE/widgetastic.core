Introduction
============

Widgetastic is a Python library designed to abstract out web UI widgets into a nice object-oriented
layer. This library includes the core classes and some basic widgets that are universal enough to
exist in this core repository.

Features
--------

- Individual interactive and non-interactive elements on the web pages are represented as widgets;
  that is, classes with defined behaviour. A good candidate for a widget might be something
  a like custom HTML button.
- Widgets are grouped on Views. A View descends from the Widget class but it is specifically designed
  to hold other widgets.
- All Widgets (including Views because they descend from them) have a read/fill interface useful for
  filling in forms etc. This interface works recursively.
- Views can be nested.
- Widgets defined on Views are read/filled in exact order that they were defined. The only exception
  to this default behaviour is for nested Views as there is limitation in the language. However, this
  can be worked around by using ``View.nested`` decorator on the nested View.
- Includes a wrapper around selenium functionality that tries to make the experience as hassle-free
  as possible including customizable hooks and built-in "JavaScript wait" code.
- Views can define their root locators and those are automatically honoured in the element lookup
  in the child Widgets.
- Supports :ref:`parametrized-views`.
- Supports :ref:`switchable-conditional-views`.
- Supports :ref:`widget-including`.
- Supports :ref:`version-picking`.
- Supports automatic :ref:`constructor-object-collapsing` for objects passed into the widget constructors.
- Supports :ref:`fillable-objects` that can coerce themselves into an appropriate filling value.
- Supports many Pythons! 2.7, 3.5, 3.6 and PyPy are officially supported and unit-tested in CI.

What this project does NOT do
-----------------------------

- A complete testing solution. In spirit of modularity, we have intentionally designed our testing
  system modular, so if a different team likes one library, but wants to do other things different
  way, the system does not stand in its way.
- UI navigation. As per previous bullet, it is up to you what you use. In CFME QE, we use a library
  called `navmazing <https://pypi.python.org/pypi/navmazing>`_, which is an evolution of the system
  we used before. You can devise your own system, use ours, or adapt something else.
- UI models representation. Doing nontrivial testing usually requires some sort of representation
  of the stuff in the product in the testing system. Usually, people use classes and instances of
  these with their methods corresponding to the real actions you can do with the entities in the UI.
  Widgetastic offers integration for such functionality (:ref:`Fillable objects`), but does not provide
  any framework to use.
- Test execution. We use pytest to drive our testing system. If you put the two previous bullets
  together and have a system of representing, navigating and interacting, then writing a simple
  boilerplate code to make the system's usage from pytest straightforward is the last and possibly
  simplest thing to do.
