"""Stub pages at the 3.x URLs, pointing at where each page is now.

The 3.x site published a page per entry point at
``documentation/manual/<name>.html``.  Those URLs are bookmarked, linked to
from mailing lists and Stack Overflow answers, and indexed by search engines,
and the set that replaces them addresses the same pages as
``reference/<api>/<name>.html``.  So every old URL keeps a file: a stub that
redirects to the new address and carries a link for a reader the redirect does
not move.

The list of old pages is :data:`LEGACY_PAGES`, captured from the published site
and shipped here.  The 3.x site is not changing, so neither is the list.

``build-docs.py`` writes the stubs into the built site after Sphinx has run.
They are not Sphinx pages: a stub in the source tree would be a second page for
every entry point in the search index and the table of contents.
"""

from __future__ import annotations

import html
import os
from typing import Iterable, Mapping, Optional

__all__ = (
    'LEGACY_PAGES',
    'built_pages',
    'read_manifest',
    'MANUAL_PREFIX',
    'NARRATIVE',
    'legacy_names',
    'resolve',
    'stub',
    'write_redirects',
)

HERE = os.path.dirname(os.path.abspath(__file__))

#: The pages the 3.x site published, one name per line.
LEGACY_PAGES = os.path.join(HERE, 'legacy-pages.txt')

#: Where those pages were, relative to the site root.
MANUAL_PREFIX = 'documentation/manual'

#: Where a page with no counterpart at all is sent.
FALLBACK = 'reference/index'

#: The APIs searched for a page, in order.  The 3.x manual was desktop GL, GLU
#: and GLUT; the few ES pages that reached it are documented under ES here, so
#: those come last rather than ahead of a desktop page of the same name.
API_ORDER = ('gl', 'glu', 'glut', 'gle', 'glx', 'gles3', 'gles2', 'gles1')

#: The 3.x narrative pages, and the page each became.  Keyed by the whole old
#: URL, since these were not all in one directory.
NARRATIVE = {
    'documentation/index.html': 'index',
    'documentation/installation.html': 'installation',
    'documentation/development.html': 'development',
    'documentation/opengl_diffs.html': 'opengl-programmers',
    'documentation/manual/index.html': 'reference/index',
}

STUB = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=%(target)s">
<link rel="canonical" href="%(target)s">
<title>%(name)s has moved</title>
</head>
<body>
<p><code>%(name)s</code> is now documented at
<a href="%(target)s">%(target)s</a>.</p>
<p>If your browser does not follow the link, select it.</p>
</body>
</html>
"""


def legacy_names() -> list[str]:
    """The page names the 3.x site published, in the order the file lists them."""
    names = []
    with open(LEGACY_PAGES, encoding='utf-8') as handle:
        for line in handle:
            line = line.rstrip('\n')
            if line and not line.startswith('#'):
                names.append(line)
    return names


def resolve(
    name: str,
    entry_points: Mapping[str, str],
    pages: Iterable[str],
) -> Optional[str]:
    """The ``<api>/<page>`` documenting ``name``, or None where nothing does.

    ``entry_points`` is the reference generator's manifest, name to page, which
    answers for an entry point.  A 3.x page named for a *family* -- ``glGet``,
    ``glFog``, ``glTexParameter`` -- is not an entry point and is not in it, so
    the page names themselves are searched as well.  ``, `` in an old file name
    joined two entry points, and is an underscore in the page that replaced it.
    """
    found = entry_points.get(name)
    if found:
        return found
    pages = set(pages)
    for api in API_ORDER:
        for candidate in (name, name.replace(', ', '_')):
            page = '%s/%s' % (api, candidate)
            if page in pages:
                return page
    return None


def stub(name: str, target: str) -> str:
    """The HTML written at an old URL, sending a reader to ``target``."""
    return STUB % {'name': html.escape(name), 'target': html.escape(target)}


def _relative(depth: int, target: str) -> str:
    """``target`` as a URL from a page ``depth`` directories below the root."""
    return '../' * depth + target + '.html'


def write_redirects(
    output: str,
    names: Optional[Iterable[str]] = None,
    entry_points: Optional[Mapping[str, str]] = None,
    pages: Optional[Iterable[str]] = None,
    narrative: Optional[Mapping[str, str]] = None,
    manifest: Optional[str] = None,
) -> int:
    """Write a stub at every 3.x URL under ``output``; returns how many.

    ``names`` defaults to :func:`legacy_names` and ``narrative`` to
    :data:`NARRATIVE`.  The entry points are read from ``manifest``, the
    reference generator's ``entrypoints.json``, and the pages from the built
    site under ``output``.
    """
    if names is None:
        names = legacy_names()
    if narrative is None:
        narrative = NARRATIVE
    if entry_points is None:
        entry_points = read_manifest(manifest)
    if pages is None:
        pages = built_pages(output)

    written = 0
    directory = os.path.join(output, *MANUAL_PREFIX.split('/'))
    os.makedirs(directory, exist_ok=True)
    depth = len(MANUAL_PREFIX.split('/'))
    for name in names:
        # The manifest and the page names are relative to `reference/`, which
        # is where the built pages are; the fallback already names its own.
        found = resolve(name, entry_points, pages)
        page = 'reference/%s' % (found,) if found else FALLBACK
        path = os.path.join(directory, name + '.html')
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(stub(name, _relative(depth, page)))
        written += 1

    for url, page in narrative.items():
        parts = url.split('/')
        path = os.path.join(output, *parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(stub(parts[-1], _relative(len(parts) - 1, page)))
        written += 1
    return written


#: The packages the manifest is read for, in the order a name is claimed.  A
#: 3.x page was desktop GL, GLU or GLUT, so those answer first for a name that
#: several APIs declare.
MANIFEST_ORDER = (
    'OpenGL.GL', 'OpenGL.GLU', 'OpenGL.GLUT', 'OpenGL.GLE', 'OpenGL.GLX',
    'OpenGL.GLES3', 'OpenGL.GLES2', 'OpenGL.GLES1',
)

#: Where the reference generator leaves its manifest, relative to this file.
DEFAULT_MANIFEST = os.path.join(
    os.path.dirname(HERE), 'docs', 'reference', 'entrypoints.json'
)


def read_manifest(path: Optional[str] = None) -> dict[str, str]:
    """Entry point name to page, from the reference generator's manifest.

    Twenty-one of the 3.x pages are named for an entry point the set documents
    on a page of another name -- ``glDrawBuffers`` on ``glDrawBuffer``,
    ``glGetShaderiv`` on ``glGetShader`` -- and the manifest is what knows.
    Empty where the manifest has not been written, which leaves those names to
    the page search.
    """
    import json

    path = path or DEFAULT_MANIFEST
    if not os.path.isfile(path):
        return {}
    with open(path, encoding='utf-8') as handle:
        declared = json.load(handle).get('entry_points', {})
    entry_points: dict[str, str] = {}
    for api in MANIFEST_ORDER:
        for name, page in declared.get(api, {}).items():
            entry_points.setdefault(name, page)
    return entry_points


def built_pages(output: str) -> set[str]:
    """``<api>/<page>`` for every reference page in the site built in ``output``."""
    pages = set()
    reference = os.path.join(output, 'reference')
    if not os.path.isdir(reference):
        return pages
    for api in os.listdir(reference):
        directory = os.path.join(reference, api)
        if not os.path.isdir(directory):
            continue
        for entry in os.listdir(directory):
            if entry.endswith('.html'):
                pages.add('%s/%s' % (api, entry[:-5]))
    return pages
