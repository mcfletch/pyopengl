"""Keeps the sidebar navigation to a size this documentation set can carry.

The theme builds its sidebar from the whole table of contents, expanded, on
every page.  That is the right thing for a set of thirty pages; this one has
several thousand, and the result is most of a megabyte of navigation repeated
on each of them -- a gigabyte of sidebar before any content.

So the tree is asked for again, bounded: collapsed to the branch the reader is
in and two levels deep.  Two levels is what puts the APIs under Reference and
the packages under the API pages while leaving out the thousands of entry
points and modules below them, which are reached from their own index pages.
Hidden toctrees are included, because that depth limit is what does the
bounding and the index pages hide their own toctrees to avoid listing their
contents twice.

The theme's own markup is kept: this hands the smaller tree through the same
function the theme uses, so the expanders and the current-page highlighting
work as they did.  Where that function is not importable -- another theme, or
a furo whose internals have moved -- nothing is replaced and the theme keeps
whatever sidebar it builds for itself.

That bound stops at the packages, which leaves a module page with nothing in
the sidebar naming where it is: ``OpenGL.GL.ARB.base_instance`` is two levels
below where the tree stops.  :func:`neighbourhood` fills that in from the
docnames -- the packages above the page, the modules beside it, and the
modules inside it where the page is a package -- and
``_templates/sidebar/modules.html`` renders it.  What that costs is bounded by
the largest package rather than by the set: 172 links under ``OpenGL.GL.ARB``,
against the several thousand the full tree would carry.
"""

from __future__ import annotations

from typing import Any, Iterable, NamedTuple, Optional

from sphinx.application import Sphinx
from sphinx.util import logging

log = logging.getLogger(__name__)

#: Where the module pages are written, as a docname prefix.
API_PREFIX = 'api/'


class Neighbourhood(NamedTuple):
    """Where a module page sits, for the sidebar to draw.

    ``ancestors`` are ``(dotted name, docname)`` from the root package down to
    the page's parent; ``siblings`` are ``(short name, docname, is this page)``
    for every module in the same package, this one included, so the list reads
    as the package's contents with the reader's place in it; ``children`` are
    ``(short name, docname)`` for what is directly inside this page's module.
    """

    module: str
    ancestors: tuple[tuple[str, str], ...]
    siblings: tuple[tuple[str, str, bool], ...]
    children: tuple[tuple[str, str], ...]


def neighbourhood(pagename: str, docnames: Iterable[str]) -> Optional[Neighbourhood]:
    """Where ``pagename`` sits among the module pages, or None if it is not one.

    Reads the docnames rather than the environment's table of contents: the
    module pages are named for their modules, so the tree is in the names, and
    a page that documents a package needs no toctree of its own to be found
    from the page beside it.
    """
    if not pagename.startswith(API_PREFIX):
        return None
    module = pagename[len(API_PREFIX):]
    if not module or '.' not in module and module == 'index':
        return None
    modules = {
        name[len(API_PREFIX):]: name
        for name in docnames
        if name.startswith(API_PREFIX) and name[len(API_PREFIX):] != 'index'
    }
    if module not in modules:
        return None

    parts = module.split('.')
    ancestors = tuple(
        ('.'.join(parts[:depth]), modules['.'.join(parts[:depth])])
        for depth in range(1, len(parts))
        if '.'.join(parts[:depth]) in modules
    )
    parent = '.'.join(parts[:-1])
    siblings = tuple(
        (name.split('.')[-1], docname, name == module)
        for name, docname in sorted(modules.items())
        if name.rpartition('.')[0] == parent
    )
    children = tuple(
        (name.split('.')[-1], docname)
        for name, docname in sorted(modules.items())
        if name.rpartition('.')[0] == module
    )
    return Neighbourhood(module, ancestors, siblings, children)

#: How many levels of the current branch the sidebar shows.
SIDEBAR_DEPTH = 2

#: Runs after the theme has put its own tree in the context (the theme
#: connects at the default priority, 500).
PRIORITY = 900


def _navigation_tree(html: str) -> str:
    from furo.navigation import get_navigation_tree

    return get_navigation_tree(html)


def bound_the_navigation_tree(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: Any,
) -> None:
    if 'toctree' not in context or 'furo_navigation_tree' not in context:
        return
    html = context['toctree'](
        collapse=True,
        titles_only=True,
        maxdepth=SIDEBAR_DEPTH,
        includehidden=True,
    )
    try:
        context['furo_navigation_tree'] = _navigation_tree(html)
    except ImportError:
        log.info(
            'furo.navigation is not importable; leaving the sidebar as the '
            'theme built it'
        )


def add_the_module_neighbourhood(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: Any,
) -> None:
    """Put this page's neighbourhood in the context for the sidebar template."""
    context['module_neighbourhood'] = neighbourhood(
        pagename, app.project.docnames
    )


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect('html-page-context', bound_the_navigation_tree, priority=PRIORITY)
    app.connect('html-page-context', add_the_module_neighbourhood, priority=PRIORITY)
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
