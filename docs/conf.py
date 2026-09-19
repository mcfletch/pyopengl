"""Sphinx configuration for the PyOpenGL documentation set.

The narrative pages are written by hand in this directory.  Two directories
beside them are written by generators and are not in version control:

``reference/``
    the OpenGL man pages with PyOpenGL's call signatures added, written by
    ``directdocs/generate.py`` from the Khronos DocBook sources.

``api/``
    a page per Python module, written by ``directdocs/dumbpydoc.py`` from the
    installed packages.

``python build-docs.py`` runs both and then calls Sphinx.
"""

import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.dirname(HERE)

sys.path.insert(0, os.path.join(HERE, '_ext'))
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from OpenGL.version import __version__  # noqa: E402

project = 'PyOpenGL'
author = 'Mike C. Fletcher'
copyright = '%s, %s' % (datetime.date.today().year, author)
release = __version__
version = '.'.join(__version__.split('.')[:2])

extensions = [
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'pyopengl_carousel',
]

templates_path = ['_templates']
exclude_patterns = ['_build', '_ext', 'Thumbs.db', '.DS_Store']

#: The reference pages name each entry point in the Python domain, so a bare
#: ``glBegin`` in any page resolves to the page that documents it.
default_role = 'py:obj'
primary_domain = 'py'

#: 2900-odd module pages and 700-odd reference pages take a while to write
#: twice.  Sphinx only needs the cross-reference inventory, which it has from
#: the domain directives.
add_module_names = False
python_use_unqualified_type_names = True

nitpicky = False
suppress_warnings = [
    # The reference pages and the module pages both mention an entry point;
    # the reference page declares it and the module page links to it, so a
    # name defined in two OpenGL versions is the only duplicate left.
    'autosectionlabel.*',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
}

extlinks = {
    'khronos': ('https://registry.khronos.org/OpenGL/extensions/%s', '%s'),
    'issue': ('https://github.com/mcfletch/pyopengl/issues/%s', 'issue #%s'),
}

html_theme = 'furo'
html_title = 'PyOpenGL %s' % (version,)
html_static_path = ['_static']
html_css_files = ['pyopengl.css', 'carousel.css']
html_js_files = ['carousel.js']
html_logo = 'images/pyopengl_icon.jpg'
html_favicon = 'images/pyopengl_icon.jpg'

#: Every page would otherwise carry a copy of its own source, which is most of
#: a second copy of the generated half of the set.
html_copy_source = False
html_show_sourcelink = False

html_theme_options = {
    'source_repository': 'https://github.com/mcfletch/pyopengl/',
    'source_branch': 'develop',
    'source_directory': 'docs/',
}

#: Screenshots for the front-page carousel.  Each record wants a ``url`` and
#: takes an optional ``description`` and ``link``; see the ``carousel``
#: directive in ``_ext/pyopengl_carousel.py``.
carousel_sources = os.path.join(HERE, '_static', 'screenshots.json')
