"""Sphinx configuration for the Inspyred Dev documentation."""

from inspyred_dev import __version__


project = 'Inspyred Dev'
author = 'Taylor B. | Inspyre-Softworks.'
copyright = '2026, Taylor B. | Inspyre-Softworks.'
version = __version__
release = __version__

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'furo'
html_static_path = ['_static']

autodoc_default_options = {
    'members': True,
    'show-inheritance': True,
}
autodoc_typehints = 'description'
napoleon_google_docstring = False
napoleon_numpy_docstring = True
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'pydantic': ('https://docs.pydantic.dev/latest/', None),
}
