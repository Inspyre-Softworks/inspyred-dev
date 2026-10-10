Versioning
==========

The ``__version__`` value in ``src/inspyred_dev/__init__.py`` is the single
source of truth for the project version. Hatch reads it when building wheel and
source distributions, the installed package exposes it at runtime, and Sphinx
uses it for the documentation release value.

To prepare a release, change only that value and rebuild the distribution.
