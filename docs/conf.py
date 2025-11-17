import os
import sys
import django


sys.path.insert(0, os.path.abspath('..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'Backend.settings'
django.setup()

project = 'Backend'
author = 'Yo'

extensions = [
    'sphinx.ext.autodoc',  # Importa la documentación desde los docstrings.
    'sphinx.ext.napoleon', # Permite que Sphinx entienda los docstrings de Google.
    'sphinx.ext.viewcode', # Añade enlaces al código fuente en la documentación.
]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_use_admonition_for_examples = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'alabaster'  # Puedes cambiar el tema. 'sphinx_rtd_theme' es muy popular.
html_static_path = ['_static']