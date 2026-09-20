"""Keeps the sidebar navigation to a size this documentation set can carry.

The theme builds its sidebar from the whole table of contents, expanded, on
every page.  That is the right thing for a set of thirty pages; this one has
several thousand, and the result is most of a megabyte of navigation repeated
on each of them -- a gigabyte of sidebar before any content.

So the tree is asked for again, *collapsed*: every branch but the one the
reader is in shows only its top entry, and that branch is expanded the whole
way down.  What a page carries is then the modules beside it at each level from
the root -- the packages under ``OpenGL``, the extension vendors under
``OpenGL.GL``, the 172 extensions under ``OpenGL.GL.ARB`` -- which is the
navigation a reader of ``OpenGL.GL.ARB.base_instance`` wants, and is bounded by
the largest package rather than by the set.

Hidden toctrees are included, because that is how the module pages carry their
children: each package page written by ``dumbpydoc`` ends in a hidden toctree
of the modules inside it, so the hierarchy is there to be walked and only the
listing of it is hidden.

The theme's own markup is kept: this hands the tree through the same function
the theme uses, so the expanders and the current-page highlighting work as they
did.  Where that function is not importable -- another theme, or a furo whose
internals have moved -- nothing is replaced and the theme keeps whatever
sidebar it builds for itself.
"""

from __future__ import annotations

from typing import Any

from sphinx.application import Sphinx
from sphinx.util import logging

log = logging.getLogger(__name__)

#: How deep the current branch is drawn.  The deepest page in the set is an
#: extension module, five levels below the root: the API reference, ``OpenGL``,
#: an API package, a vendor package, the module.  Collapsing is what bounds the
#: size, so this only has to be deep enough to reach the leaves.
SIDEBAR_DEPTH = 6

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


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect('html-page-context', bound_the_navigation_tree, priority=PRIORITY)
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
