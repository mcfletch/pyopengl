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
author = 'Mike C. Fletcher and Contributors'
#: 2005 is where ``license.txt`` starts, this being one work with it.  The end
#: is the year the set is built, so a rebuild keeps it current and nobody has
#: to remember to.
copyright = '2005-%s, %s' % (datetime.date.today().year, author)
release = __version__
version = '.'.join(__version__.split('.')[:2])

extensions = [
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'pyopengl_carousel',
    'pyopengl_sidebar',
]

# `sphinx.ext.viewcode` is deliberately absent.  Most of the packages is built
# from the declaration tables rather than written out, so a source page for it
# shows the loader rather than the entry point; and it follows imports into the
# standard library, writing a highlighted copy of `tkinter`, `typing` and
# `logging` into the set.  The repository is a click away in the header.

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

#: The equations in the reference pages are MathML, which is what the Khronos
#: sources carry and what every current browser renders without help, so they
#: are written through as raw HTML rather than translated to LaTeX.
rst_prolog = """
.. role:: raw-html(raw)
   :format: html
"""

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

#: Where to find the project, shown as badges at the foot of the sidebar.
#: `_templates/sidebar/badges.html` renders these.
PROJECT_LINKS = [
    (
        'https://pypi.org/project/PyOpenGL/',
        'https://img.shields.io/pypi/v/PyOpenGL',
        'PyOpenGL on PyPI',
    ),
    (
        'https://pepy.tech/project/pyopengl',
        'https://img.shields.io/pepy/dt/PyOpenGL',
        'Total downloads from PyPI',
    ),
    (
        'https://github.com/mcfletch/pyopengl/actions/workflows/test.yml',
        'https://img.shields.io/github/actions/workflow/status'
        '/mcfletch/pyopengl/test.yml?branch=develop&label=tests',
        'The test suite on develop',
    ),
]

#: Where the source is, for the link in the top-right icon row.
PROJECT_URL = 'https://github.com/mcfletch/pyopengl'

html_theme_options = {
    # One button in the top-right icon row.  It is the project link rather
    # than an edit link: `_templates/components/edit-this-page.html` is what
    # the theme includes for it, and that is what it renders.  `source_*` are
    # deliberately unset, since those are what would make it an edit link.
    'top_of_page_buttons': ['edit'],
}

#: What the two templates above read.  A template sees `html_context`, not
#: this module.
html_context = {
    'project_url': PROJECT_URL,
    'project_badges': PROJECT_LINKS,
}

#: Furo's own list, from its `theme.conf`, with the badges added after
#: `scroll-end` so they sit below the navigation rather than scrolling with
#: it.  Naming one sidebar means naming them all.
html_sidebars = {
    '**': [
        'sidebar/brand.html',
        'sidebar/search.html',
        'sidebar/scroll-start.html',
        'sidebar/navigation.html',
        'sidebar/ethical-ads.html',
        'sidebar/scroll-end.html',
        'sidebar/badges.html',
        'sidebar/variant-selector.html',
    ]
}

#: Screenshots for the front-page carousel.  Each record wants a ``url`` and
#: takes an optional ``description`` and ``link``; see the ``carousel``
#: directive in ``_ext/pyopengl_carousel.py``.
carousel_sources = os.path.join(HERE, '_static', 'screenshots.json')
