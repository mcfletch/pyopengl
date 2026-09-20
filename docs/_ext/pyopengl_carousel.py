"""A rotating screenshot display for the documentation set.

``.. carousel::`` puts a panel on the page that shows one picture at a time,
with its caption, and moves to the next every few seconds.  The records come
either from the directive's own body or from a JSON file:

.. code-block:: rst

    .. carousel::
       :source: screenshots.json
       :interval: 5000
       :height: 320

Each record is an object with ``url``, and optionally ``description`` (the
caption, which is also the image's alt text) and ``link`` (where clicking the
caption goes).  A ``url`` that names a scheme is used as it stands; anything
else is a path relative to the documentation root, resolved against whatever
page the carousel lands on.

A local ``url`` naming a file that is not in the source tree is reported as a
warning and the record is dropped, so a renamed screenshot is a build message
rather than a hole in the page.  Without JavaScript the panel shows the first
picture and a list of the rest, so the content is still reachable.
"""

from __future__ import annotations

import json
import os
import posixpath
from typing import Any

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.osutil import relative_uri

__all__ = ['carousel', 'CarouselDirective', 'setup']

log = logging.getLogger(__name__)

#: Schemes a record's ``url`` may name to be left alone.
EXTERNAL_PREFIXES = ('http://', 'https://', '//', 'data:')


class carousel(nodes.General, nodes.Element):
    """The panel itself; ``records`` holds the pictures to rotate through."""


def _is_external(url: str) -> bool:
    return url.startswith(EXTERNAL_PREFIXES)


class CarouselDirective(Directive):
    has_content = True
    option_spec = {
        'source': directives.unchanged,
        'interval': directives.positive_int,
        'height': directives.positive_int,
        'class': directives.class_option,
    }

    def run(self) -> list[nodes.Node]:
        env = self.state.document.settings.env
        try:
            records = self._records(env)
        except ValueError as err:
            return [
                self.state.document.reporter.error(str(err), line=self.lineno)
            ]
        node = carousel()
        node['records'] = records
        node['interval'] = self.options.get('interval', 5000)
        node['height'] = self.options.get('height', 320)
        node['classes'] = ['pyopengl-carousel'] + self.options.get('class', [])
        self._check_local(env, records)
        return [node]

    def _records(self, env: Any) -> list[dict[str, str]]:
        """The records, from the directive body or from ``:source:``."""
        source = self.options.get('source')
        if source and self.content:
            raise ValueError(
                'carousel takes its records from :source: or from its body, '
                'not from both'
            )
        if source:
            path = os.path.join(os.path.dirname(env.doc2path(env.docname)), source)
            if not os.path.isfile(path):
                raise ValueError('carousel source %s does not exist' % (source,))
            env.note_dependency(path)
            with open(path, encoding='utf-8') as fh:
                raw = fh.read()
        else:
            raw = '\n'.join(self.content)
        try:
            records = json.loads(raw)
        except ValueError as err:
            raise ValueError('carousel records are not JSON: %s' % (err,)) from err
        if not isinstance(records, list):
            raise ValueError('carousel records must be a JSON list of objects')
        for record in records:
            if not isinstance(record, dict) or 'url' not in record:
                raise ValueError('every carousel record needs a "url"')
        return records

    def _check_local(self, env: Any, records: list[dict[str, str]]) -> None:
        """Warn about a local picture the source tree does not have."""
        kept = []
        for record in records:
            url = record['url']
            if _is_external(url):
                kept.append(record)
                continue
            path = os.path.join(env.srcdir, url)
            if os.path.isfile(path):
                kept.append(record)
            else:
                log.warning(
                    'carousel: no such screenshot: %s', url, location=env.docname
                )
        records[:] = kept


def _resolve(builder: Any, docname: str, url: str) -> str:
    """The URL to write into the page for ``url`` seen from ``docname``."""
    if _is_external(url):
        return url
    here = builder.get_target_uri(docname)
    return relative_uri(here, url) or posixpath.basename(url)


def visit_carousel_html(self: Any, node: carousel) -> None:
    builder = self.builder
    docname = builder.current_docname
    records = [
        dict(record, url=_resolve(builder, docname, record['url']))
        for record in node['records']
    ]
    classes = ' '.join(node['classes'])
    self.body.append(
        '<div class="%s" data-interval="%d" style="--carousel-height: %dpx">'
        % (classes, node['interval'], node['height'])
    )
    self.body.append(
        '<script type="application/json" class="carousel-records">%s</script>'
        % (json.dumps(records).replace('</', '<\\/'),)
    )
    self.body.append('<div class="carousel-frame"></div>')
    self.body.append('<div class="carousel-caption"></div>')
    self.body.append('<noscript>')
    for record in records:
        alt = self.encode(record.get('description', ''))
        self.body.append(
            '<figure><img src="%s" alt="%s" />' % (self.encode(record['url']), alt)
        )
        if record.get('description'):
            link = record.get('link')
            caption = (
                '<a href="%s">%s</a>' % (self.encode(link), alt) if link else alt
            )
            self.body.append('<figcaption>%s</figcaption>' % (caption,))
        self.body.append('</figure>')
    self.body.append('</noscript>')
    self.body.append('</div>')
    raise nodes.SkipNode


def visit_carousel_text(self: Any, node: carousel) -> None:
    """Every builder but HTML gets the captions as a list."""
    for record in node['records']:
        description = record.get('description') or record['url']
        self.add_text('* %s\n' % (description,))
    raise nodes.SkipNode


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_node(
        carousel,
        html=(visit_carousel_html, None),
        text=(visit_carousel_text, None),
        latex=(visit_carousel_text, None),
        man=(visit_carousel_text, None),
        texinfo=(visit_carousel_text, None),
    )
    app.add_directive('carousel', CarouselDirective)
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
