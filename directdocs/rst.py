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
import inspect
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
    'write_docstring',
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
# docstrings


#: A docstring that uses a role wrote itself as reStructuredText.
_RST_ROLE = re.compile(r':[a-z:]+:`')

#: A docstring that uses a directive has to be written through untouched: the
#: directive and the indented body under it are one thing.
_RST_DIRECTIVE = re.compile(r'^\s*\.\.\s+[\w-]+::', re.M)

#: Inline markup a substitution must not reach inside: an entry point already
#: written as a literal or as a cross-reference is already saying what it is.
_PROTECTED = re.compile(r'``.*?``|:[a-z:]+:`[^`]*`|`[^`]*`_{0,2}', re.S)


def write_docstring(
    text: str, writer: Writer, entry_points: dict[str, str] | None = None
) -> None:
    """Write a docstring as the body of whatever directive is open.

    PyOpenGL's docstrings are mostly a call signature, a sentence or two, and
    an indented list of what each argument means.  The prose is written as
    prose, so that a name in it can become a link; the argument list becomes a
    definition list, which is what it is; anything else indented goes in
    verbatim, its layout being what carries its meaning.

    A docstring that uses a directive is written through untouched -- the
    directive and its body have to stay together, and splitting them by indent
    is exactly what would separate them.

    :func:`inspect.cleandoc` rather than :func:`textwrap.dedent`: a docstring's
    first line carries no indent and the rest carries the block's, so dedent
    finds nothing in common and removes nothing -- which makes the whole of a
    class docstring look indented, and lands all of it in a literal block.

    ``entry_points`` maps an entry point name to its reference page; where it
    is given, a name mentioned in the prose becomes a link to that page.
    """
    if not text:
        return
    text = inspect.cleandoc(text)
    if _RST_DIRECTIVE.search(text) or _RST_ROLE.search(text):
        # Written as reStructuredText, so it is written through: splitting it
        # by indent would take its structure apart -- a list item and the line
        # continuing it are not two blocks.  Only the argument lists are
        # rewritten, those being the one thing in a docstring that reST reads
        # as something else.
        #
        # A role or a directive, and not a bullet: the generated modules carry
        # the specification's own prose as their docstring, and that is full of
        # asterisks and indentation that were never markup.
        writer.blank()
        for line in convert_argument_lists(text).split('\n'):
            # An indented line in a docstring is a sample or a literal block,
            # and a link in the middle of a call is not what anybody wants.
            if entry_points and line[:1] and not line[0].isspace():
                line = link_entry_points(line, entry_points)
            writer.line(line)
        writer.blank()
        return

    #: A docstring using roles wrote itself as markup, so leave its markup
    #: alone; a plain one has to be escaped or an asterisk in it is emphasis.
    # Everything past here is plain text: whatever wrote itself as markup was
    # written through above.  So it is escaped, or an asterisk in it becomes
    # emphasis and a backquote opens a literal that never closes.
    def prose(lines: list[str]) -> str:
        body = escape(' '.join(line.strip() for line in lines))
        if entry_points:
            body = link_entry_points(body, entry_points)
        return body

    for indented, lines in docstring_blocks(text):
        entries = argument_list(lines)
        if entries is None:
            if indented or looks_like_a_list(lines):
                # Indented, so its layout is the point; or a list this could
                # not read as one, which joining into a paragraph would run
                # together into nonsense.
                writer.literal_block('\n'.join(lines))
            else:
                writer.paragraph(prose(lines))
            continue
        writer.blank()
        for term, description in entries:
            writer.line(escape(term))
            with writer.indent():
                writer.line(textwrap.fill(prose(description), 72))
            writer.blank()


#: ``name -- what it is``, which is how every PyOpenGL docstring writes an
#: argument.  Several names may share one description.
_ARGUMENT = re.compile(r'^(\S[^-]*?)\s+--\s+(.*)$')

#: What the left of a ``--`` has to look like to be argument names rather than
#: a sentence with a dash in it: identifiers, possibly several, possibly
#: starred.
_ARGUMENT_NAMES = re.compile(r'^\*{0,2}\w+(?:\s*,\s*\*{0,2}\w+)*$')


def looks_like_a_list(lines: list[str]) -> bool:
    """Whether ``lines`` is a list this could not read as an argument list.

    Such a run is left exactly as it is.  Joining it into a paragraph, which
    is what prose gets, would run its entries together into one sentence.
    """
    for line in lines:
        match = _ARGUMENT.match(line.strip())
        if match and _ARGUMENT_NAMES.match(match.group(1).strip()):
            return True
    return False


def argument_list(lines: list[str]) -> list[tuple[str, list[str]]] | None:
    """``lines`` as ``(names, description)`` pairs, or ``None``.

    ``None`` where the run is not an argument list at all -- a sample, a
    table, a quoted message -- and should be left exactly as it is.  The names
    have to look like names: a sentence with a dash in the middle of it is a
    sentence.
    """
    body = textwrap.dedent('\n'.join(lines)).split('\n')
    entries: list[tuple[str, list[str]]] = []
    for line in body:
        if not line.strip():
            continue
        if line[:1].isspace():
            if not entries:
                return None
            entries[-1][1].append(line.strip())
            continue
        match = _ARGUMENT.match(line)
        if not match or not _ARGUMENT_NAMES.match(match.group(1).strip()):
            return None
        entries.append((match.group(1).strip(), [match.group(2).strip()]))
    return entries or None


def convert_argument_lists(text: str) -> str:
    """``name -- what it is`` runs in ``text``, as definition lists.

    In place, at whatever indent they sit: everything around them is left
    exactly as it was.  As reStructuredText such a run is a block quote whose
    continuation lines are a second, unannounced indent -- which is an error,
    and the reason a docstring that is otherwise ordinary markup cannot simply
    be written through.
    """
    lines = text.split('\n')
    out: list[str] = []
    at = 0
    while at < len(lines):
        run, following = _argument_run(lines, at)
        if run is None:
            out.append(lines[at])
            at += 1
            continue
        out.extend(run)
        at = following
    return '\n'.join(out)


def _argument_run(lines: list[str], at: int) -> tuple[list[str] | None, int]:
    """The definition list for the argument run at ``at``, and where it ends.

    A run starts a block: it is the first line, the line above it is blank, or
    the line above it is a label ending in a colon -- ``Attributes:`` and
    ``Parameters:`` are how these lists are usually introduced.  Prose wraps,
    and a sentence whose second line happens to begin ``instead -- ...`` is a
    sentence rather than an argument called ``instead``.
    """
    above = lines[at - 1].strip() if at else ''
    if above and not above.endswith(':'):
        return None, at
    first = _ARGUMENT.match(lines[at].strip())
    if not first or not _ARGUMENT_NAMES.match(first.group(1).strip()):
        return None, at
    indent = ' ' * (len(lines[at]) - len(lines[at].lstrip()))
    entries: list[tuple[str, list[str]]] = []
    index = at
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            # A blank line ends the run unless another entry follows it.
            ahead = index + 1
            while ahead < len(lines) and not lines[ahead].strip():
                ahead += 1
            nxt = _ARGUMENT.match(lines[ahead].strip()) if ahead < len(lines) else None
            if not (nxt and _ARGUMENT_NAMES.match(nxt.group(1).strip())):
                break
            index = ahead
            continue
        here = len(line) - len(line.lstrip())
        if here < len(indent):
            break
        match = _ARGUMENT.match(line.strip())
        if here == len(indent) and match and _ARGUMENT_NAMES.match(
            match.group(1).strip()
        ):
            entries.append((match.group(1).strip(), [match.group(2).strip()]))
        elif here > len(indent) and entries:
            entries[-1][1].append(line.strip())
        else:
            break
        index += 1
    if not entries:
        return None, at
    written: list[str] = []
    for name, description in entries:
        written.append(indent + name)
        body = textwrap.fill(
            ' '.join(description), width=max(72 - len(indent), 30)
        )
        written.extend(indent + '   ' + part for part in body.split('\n'))
        written.append('')
    return written, index


def docstring_blocks(text: str) -> list[tuple[bool, list[str]]]:
    """``text`` split into runs of indented and unindented lines.

    A blank line inside a run of indented lines is part of it -- an argument
    list with a paragraph between its halves is one block, not three -- and
    between unindented lines it starts a new paragraph.
    """
    blocks: list[tuple[bool, list[str]]] = []
    blank = False
    for line in inspect.cleandoc(text).split('\n'):
        if not line.strip():
            blank = True
            continue
        indented = line[:1].isspace()
        if blocks and blocks[-1][0] == indented and not (blank and not indented):
            if blank:
                blocks[-1][1].append('')
            blocks[-1][1].append(line)
        else:
            blocks.append((indented, [line]))
        blank = False
    return blocks


def link_entry_points(text: str, entry_points: dict[str, str]) -> str:
    """Link the entry point names ``text`` mentions to their reference pages.

    Only where the name is not already marked up: an entry point written as a
    literal or as a cross-reference is already saying what it is.
    """
    names = re.compile(
        r'\b(%s)\b(?![`(])'
        % ('|'.join(
            re.escape(name)
            for name in sorted(entry_points, key=len, reverse=True)
        ),)
    )

    def replace(match: re.Match) -> str:
        name = match.group(1)
        return ':doc:`%s </reference/%s>`' % (name, entry_points[name])

    out, at = [], 0
    for guarded in _PROTECTED.finditer(text):
        out.append(names.sub(replace, text[at:guarded.start()]))
        out.append(guarded.group(0))
        at = guarded.end()
    out.append(names.sub(replace, text[at:]))
    return ''.join(out)


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
