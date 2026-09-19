"""Writing reStructuredText, and turning DocBook into it.

Two things live here.  :class:`Writer` accumulates lines with an indentation
stack, which is what makes nested directives and definition lists readable to
write.  :class:`DocBookRenderer` walks a Khronos reference page and renders it,
one method per element type.

The renderer is given the page it is rendering and a *links* object that
answers two questions: where does a named entry point's page live, and is this
name one of the parameters this page documents.  Everything specific to the
PyOpenGL documentation set is in that object rather than here.
"""

from __future__ import annotations

import contextlib
import re
import textwrap
from typing import Any, Callable, Iterator, Protocol

__all__ = [
    'Writer',
    'DocBookRenderer',
    'LinkResolver',
    'escape',
    'heading',
    'literal',
    'collapse',
    'squeeze',
]

DOCBOOK_NS = 'http://docbook.org/ns/docbook'
MML_NS = 'http://www.w3.org/1998/Math/MathML'
XLINK_NS = 'http://www.w3.org/1999/xlink'

#: The characters that start inline markup at the beginning of a word, and so
#: have to be escaped when they are meant literally.
_ESCAPE = re.compile(r'([\\*`|_])')

#: reStructuredText recognises the start of inline markup only after
#: whitespace or one of these characters, and the end of it only before
#: whitespace or one of the closers below.  Anywhere else the markup is not
#: markup, which is how ``GL_CLIP_PLANE``\ *i* and a cross-reference followed
#: by ``[0]`` turn into a warning and a page of visible backquotes.
_OPENERS = frozenset("-:/'\"<([{")
_CLOSERS = frozenset("-.,:;!?\\/'\")]}>")

#: Underline characters, outermost first.  A reference page uses the first two;
#: the rest are here so a deeply nested DocBook section still renders.
UNDERLINES = '=-~^"+'


def escape(text: str) -> str:
    """``text`` as reST that renders as itself."""
    return _ESCAPE.sub(r'\\\1', text)


def literal(text: str) -> str:
    """``text`` as an inline literal.

    A literal cannot contain a run of two backquotes, and nothing in the
    reference pages does; a stray one is rendered as text rather than dropped.
    """
    if '``' in text:
        return escape(text)
    return '``%s``' % (text,)


def heading(text: str, level: int = 0) -> str:
    """``text`` underlined as a section title at ``level``."""
    char = UNDERLINES[min(level, len(UNDERLINES) - 1)]
    return '%s\n%s' % (text, char * max(len(text), 3))


def join_inline(before: str, markup: str, after: str) -> str:
    """Put ``markup`` between two runs of text, separating where reST needs it.

    Where the source runs text straight into marked-up text, or one marked-up
    run straight into the next, the gap is written as a backslash followed by a
    space.  That is reST's way of saying "no space here": it separates the
    markup from its neighbour and renders as nothing.
    """
    if not markup:
        return before + after
    result = before
    if result and not result[-1].isspace() and result[-1] not in _OPENERS:
        result += '\\ '
    result += markup
    if after and not after[0].isspace() and after[0] not in _CLOSERS:
        result += '\\ '
    return result + after


class Writer:
    """Accumulates reST lines under an indentation stack."""

    def __init__(self) -> None:
        self.lines: list[str] = []
        self.prefix = ''

    def line(self, text: str = '') -> None:
        if not text:
            self.blank()
            return
        for raw in text.split('\n'):
            self.lines.append((self.prefix + raw).rstrip() if raw else '')

    def blank(self) -> None:
        if self.lines and self.lines[-1] != '':
            self.lines.append('')

    def paragraph(self, text: str, width: int = 79) -> None:
        text = text.strip()
        if not text:
            return
        self.blank()
        wrapped = textwrap.fill(
            text,
            width=max(width - len(self.prefix), 30),
            break_long_words=False,
            break_on_hyphens=False,
        )
        self.line(wrapped)
        self.blank()

    def raw_block(self, text: str, language: str = 'html') -> None:
        self.blank()
        self.line('.. raw:: %s' % (language,))
        self.blank()
        with self.indent():
            for raw in text.split('\n'):
                self.line(raw)
        self.blank()

    def literal_block(self, text: str, language: str = 'text') -> None:
        text = text.rstrip()
        if not text.strip():
            return
        self.blank()
        self.line('.. code-block:: %s' % (language,))
        self.blank()
        with self.indent():
            for raw in textwrap.dedent(text).split('\n'):
                self.line(raw)
        self.blank()

    def directive(
        self, name: str, argument: str = '', options: dict[str, str] | None = None
    ) -> None:
        self.blank()
        self.line('.. %s:: %s' % (name, argument) if argument else '.. %s::' % (name,))
        for key, value in (options or {}).items():
            self.line('   :%s: %s' % (key, value) if value else '   :%s:' % (key,))
        self.blank()

    def target(self, label: str) -> None:
        self.blank()
        self.line('.. _%s:' % (label,))
        self.blank()

    def heading(self, text: str, level: int = 0) -> None:
        self.blank()
        self.line(heading(text, level))
        self.blank()

    @contextlib.contextmanager
    def indent(self, by: str = '   ') -> Iterator[None]:
        previous = self.prefix
        self.prefix = previous + by
        try:
            yield
        finally:
            self.prefix = previous

    def render(self) -> str:
        text = '\n'.join(self.lines).rstrip()
        # Two blank lines in a row say nothing reST can use, and a page built
        # from many small renderers collects them at every join.
        return re.sub(r'\n{3,}', '\n\n', text) + '\n'


class LinkResolver(Protocol):
    """What the renderer needs to know about the rest of the doc set."""

    def entry_point_page(self, name: str) -> str | None:
        """The docname for ``name``'s reference page, or ``None``."""

    def parameter_label(self, name: str) -> str | None:
        """The label for parameter ``name`` on the page being rendered."""


class DocBookRenderer:
    """Renders one Khronos reference page's DocBook into reStructuredText.

    Block-level elements are written through a :class:`Writer`; inline ones are
    returned as text.  An element with no handler is treated as a transparent
    container, so an unexpected tag loses its markup rather than its content.
    """

    #: Rendered as a run of inline text rather than as a block.
    INLINE_TAGS = frozenset(
        [
            'citerefentry',
            'code',
            'command',
            'constant',
            'emphasis',
            'envar',
            'firstterm',
            'function',
            'inlineequation',
            'link',
            'literal',
            'modifier',
            'parameter',
            'phrase',
            'replaceable',
            'subscript',
            'superscript',
            'symbol',
            'trademark',
            'type',
            'ulink',
            'varname',
        ]
    )

    def __init__(self, links: LinkResolver, level: int = 1) -> None:
        self.links = links
        self.level = level
        #: Set when the page turns out to contain MathML, so that the caller
        #: can say so.
        self.used_math = False

    # ------------------------------------------------------------------
    # block level

    def render(self, element: Any, writer: Writer, level: int | None = None) -> None:
        """Write ``element``'s children as blocks into ``writer``."""
        if level is None:
            level = self.level
        text = (element.text or '').strip()
        if text:
            writer.paragraph(escape(text))
        for child in element:
            self.render_block(child, writer, level)

    def render_block(self, element: Any, writer: Writer, level: int) -> None:
        tag = local_name(element)
        if tag in self.INLINE_TAGS or is_math(element):
            # An inline element on its own between blocks is still a paragraph.
            writer.paragraph(self.inline_children_of(element, wrapper=element))
            return
        handler: Callable[..., None] | None = getattr(self, 'block_%s' % (tag,), None)
        if handler is not None:
            handler(element, writer, level)
        else:
            self.render(element, writer, level)
        tail = (element.tail or '').strip()
        if tail:
            writer.paragraph(escape(tail))

    def block_para(self, element: Any, writer: Writer, level: int) -> None:
        writer.paragraph(self.inline_children_of(element, wrapper=element))

    def block_title(self, element: Any, writer: Writer, level: int) -> None:
        title = self.inline_children_of(element, wrapper=element).strip()
        if title:
            writer.heading(title, level)

    def block_refsect1(self, element: Any, writer: Writer, level: int) -> None:
        for child in element:
            if local_name(child) == 'title':
                self.block_title(child, writer, level)
            else:
                self.render_block(child, writer, level + 1)

    block_refsect2 = block_refsect1
    block_section = block_refsect1

    def block_programlisting(self, element: Any, writer: Writer, level: int) -> None:
        writer.literal_block(all_text(element), language='c')

    block_screen = block_programlisting
    block_synopsis = block_programlisting

    def block_blockquote(self, element: Any, writer: Writer, level: int) -> None:
        inner = Writer()
        self.render(element, inner, level)
        writer.blank()
        with writer.indent():
            writer.line(inner.render().rstrip())
        writer.blank()

    def block_itemizedlist(self, element: Any, writer: Writer, level: int) -> None:
        self._list(element, writer, level, marker=lambda _index: '- ')

    def block_orderedlist(self, element: Any, writer: Writer, level: int) -> None:
        self._list(element, writer, level, marker=lambda _index: '#. ')

    def _list(
        self,
        element: Any,
        writer: Writer,
        level: int,
        marker: Callable[[int], str],
    ) -> None:
        writer.blank()
        for index, item in enumerate(element):
            if local_name(item) != 'listitem':
                continue
            inner = Writer()
            self.render(item, inner, level)
            body = inner.render().strip()
            if not body:
                continue
            bullet = marker(index)
            first, _, rest = body.partition('\n')
            writer.line(bullet + first)
            if rest:
                with writer.indent(' ' * len(bullet)):
                    writer.line(rest)
            writer.blank()

    def block_variablelist(self, element: Any, writer: Writer, level: int) -> None:
        writer.blank()
        for entry in element:
            if local_name(entry) != 'varlistentry':
                continue
            terms = [
                self.inline_children_of(term, wrapper=term).strip()
                for term in entry
                if local_name(term) == 'term'
            ]
            terms = [term for term in terms if term]
            if not terms:
                continue
            inner = Writer()
            for item in entry:
                if local_name(item) == 'listitem':
                    self.render(item, inner, level)
            body = inner.render().strip()
            writer.line(', '.join(terms))
            with writer.indent():
                writer.line(body or 'Undocumented.')
            writer.blank()

    def block_informaltable(self, element: Any, writer: Writer, level: int) -> None:
        rows: list[tuple[bool, list[str]]] = []
        for group in element:
            for part in group:
                kind = local_name(part)
                if kind not in ('thead', 'tbody'):
                    continue
                for row in part:
                    if local_name(row) != 'row':
                        continue
                    cells = []
                    spans = False
                    for cell in row:
                        if local_name(cell) != 'entry':
                            continue
                        if cell.get('spanname') or cell.get('namest'):
                            spans = True
                        cells.append(
                            self.inline_children_of(cell, wrapper=cell).strip()
                        )
                    if cells:
                        rows.append((kind == 'thead', cells, spans))
        if not rows:
            return
        rows = self._rectangular(rows)
        header_rows = sum(1 for is_header, _ in rows if is_header)
        options = {'widths': 'auto'}
        if header_rows:
            options['header-rows'] = str(header_rows)
        writer.directive('list-table', options=options)
        with writer.indent():
            for _is_header, cells in rows:
                for index, cell in enumerate(cells):
                    lead = '* - ' if index == 0 else '  - '
                    body = cell or r'\ '
                    first, _, rest = body.partition('\n')
                    writer.line(lead + first)
                    if rest:
                        with writer.indent(' ' * len(lead)):
                            writer.line(rest)
        writer.blank()

    block_table = block_informaltable

    @staticmethod
    def _rectangular(
        rows: list[tuple[bool, list[str], bool]]
    ) -> list[tuple[bool, list[str]]]:
        """``rows`` with every row the same width, as a list table needs.

        A list table has no cell spanning, so a row that is short because one
        of its cells spans several columns cannot be rendered as it stands.
        The version-support tables carry one such row, a banner reading
        "OpenGL Version" over the columns the next row names one by one; it is
        dropped, since the row under it says the same thing per column.  A row
        that is short for any other reason is padded, which loses nothing.
        """
        width = max(len(cells) for _is_header, cells, _spans in rows)
        result = []
        for is_header, cells, spans in rows:
            if spans and len(cells) < width:
                continue
            result.append((is_header, cells + [''] * (width - len(cells))))
        return result

    def block_informalequation(self, element: Any, writer: Writer, level: int) -> None:
        for child in element:
            if is_math(child):
                self.used_math = True
                writer.raw_block(serialize(child))

    block_equation = block_informalequation

    def block_footnote(self, element: Any, writer: Writer, level: int) -> None:
        inner = Writer()
        self.render(element, inner, level)
        body = inner.render().strip()
        if body:
            writer.blank()
            writer.line('.. note::')
            with writer.indent():
                writer.line(body)
            writer.blank()

    # ------------------------------------------------------------------
    # inline level

    def inline_children_of(self, element: Any, wrapper: Any = None) -> str:
        """``element``'s content as one run of inline reST."""
        result = escape(collapse(element.text or ''))
        for child in element:
            result = join_inline(
                result,
                self.inline(child),
                escape(collapse(child.tail or '')),
            )
        return result.strip()

    def inline(self, element: Any) -> str:
        if is_math(element):
            self.used_math = True
            return ':raw-html:`%s`' % (serialize(element),)
        tag = local_name(element)
        handler: Callable[[Any], str] | None = getattr(
            self, 'inline_%s' % (tag,), None
        )
        if handler is not None:
            return handler(element)
        return self.inline_children_of(element)

    def inline_constant(self, element: Any) -> str:
        return literal(squeeze(all_text(element)))

    inline_code = inline_constant
    inline_command = inline_constant
    inline_envar = inline_constant
    inline_literal = inline_constant
    inline_symbol = inline_constant
    inline_type = inline_constant
    inline_varname = inline_constant
    inline_modifier = inline_constant

    def inline_emphasis(self, element: Any) -> str:
        body = self.inline_children_of(element).strip()
        return '*%s*' % (body,) if body else ''

    inline_firstterm = inline_emphasis
    inline_replaceable = inline_emphasis

    def inline_phrase(self, element: Any) -> str:
        return self.inline_children_of(element)

    #: What ``<trademark class="...">`` stands for.  The element is often
    #: empty, the class being the whole of its content.
    TRADEMARK_SYMBOLS = {
        'copyright': '©',
        'registered': '®',
        'service': '℠',
        'trade': '™',
    }

    def inline_trademark(self, element: Any) -> str:
        symbol = self.TRADEMARK_SYMBOLS.get(element.get('class', 'trade'), '™')
        body = self.inline_children_of(element).strip()
        return '%s%s' % (body, symbol) if body else symbol

    def inline_subscript(self, element: Any) -> str:
        return ':subscript:`%s`' % (squeeze(all_text(element)),)

    def inline_superscript(self, element: Any) -> str:
        return ':superscript:`%s`' % (squeeze(all_text(element)),)

    def inline_parameter(self, element: Any) -> str:
        name = squeeze(all_text(element))
        if not name:
            return ''
        label = self.links.parameter_label(name)
        if label:
            return ':ref:`%s <%s>`' % (name, label)
        return '*%s*' % (escape(name),)

    def inline_function(self, element: Any) -> str:
        return self._entry_point_reference(reference_name(element))

    def inline_citerefentry(self, element: Any) -> str:
        return self._entry_point_reference(reference_name(element))

    def _entry_point_reference(self, name: str) -> str:
        name = squeeze(name)
        if not name:
            return ''
        page = self.links.entry_point_page(name)
        if page:
            return ':doc:`%s <%s>`' % (name, page)
        return literal(name)

    def inline_link(self, element: Any) -> str:
        href = element.get('{%s}href' % (XLINK_NS,)) or element.get('href')
        body = self.inline_children_of(element).strip() or href or ''
        if href:
            return '`%s <%s>`__' % (body, href)
        return body

    def inline_ulink(self, element: Any) -> str:
        href = element.get('url') or element.get('{%s}href' % (XLINK_NS,))
        body = self.inline_children_of(element).strip() or href or ''
        if href:
            return '`%s <%s>`__' % (body, href)
        return body

    def inline_inlineequation(self, element: Any) -> str:
        for child in element:
            if is_math(child):
                self.used_math = True
                return ':raw-html:`%s`' % (serialize(child),)
        return self.inline_children_of(element)


# ----------------------------------------------------------------------
# element helpers


def local_name(element: Any) -> str:
    """``element``'s tag with its namespace removed."""
    tag = element.tag
    if not isinstance(tag, str):
        return ''
    return tag.rsplit('}', 1)[-1]


def is_math(element: Any) -> bool:
    tag = element.tag
    return isinstance(tag, str) and tag == '{%s}math' % (MML_NS,)


def all_text(element: Any) -> str:
    """Every character of text under ``element``, its tail excluded."""
    parts = [element.text or '']
    for child in element:
        parts.append(all_text(child))
        parts.append(child.tail or '')
    return ''.join(parts)


def collapse(text: str) -> str:
    """``text`` with each run of whitespace turned into one space.

    A leading or trailing space is kept: in running prose it is the space
    between a word and the marked-up run beside it, and losing it is what turns
    "one of ``GL_RGBA``" into "one of``GL_RGBA``".
    """
    return re.sub(r'\s+', ' ', text)


def squeeze(text: str) -> str:
    """:func:`collapse`, with the edges trimmed as well."""
    return collapse(text).strip()


def reference_name(element: Any) -> str:
    """The name a ``function`` or ``citerefentry`` refers to.

    ``citerefentry`` wraps the name in ``refentrytitle``; ``function`` holds it
    directly, except for the one page that wraps it the other way about.
    """
    if len(element):
        for child in element:
            if local_name(child) in ('refentrytitle', 'function'):
                return squeeze(all_text(child))
    return squeeze(all_text(element))


def serialize(element: Any) -> str:
    """``element`` as one line of XML, for a raw HTML block.

    The MathML namespace is written as the default so that the result is what
    an HTML parser expects to see inside a page.
    """
    import copy as copy_module

    import lxml.etree as ET

    copied = copy_module.deepcopy(element)
    copied.tail = None
    for node in copied.iter():
        if isinstance(node.tag, str) and node.tag.startswith('{%s}' % (MML_NS,)):
            node.tag = local_name(node)
    ET.cleanup_namespaces(copied)
    text = ET.tostring(copied, encoding='unicode', method='xml')
    if '<math' in text and 'xmlns' not in text.split('>', 1)[0]:
        text = text.replace('<math', '<math xmlns="%s"' % (MML_NS,), 1)
    return squeeze(text)
