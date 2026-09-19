#! /usr/bin/env python3
"""Generates the PyOpenGL reference documentation as reStructuredText.

The Khronos reference pages are DocBook; PyOpenGL's addition to them is the
Python call signature for each entry point, the aliases that reach it, and
links to sample code that uses it.  This writes one page per reference entry
into ``docs/reference/``, where Sphinx builds them with the rest of the set.

Each page declares its Python entry points in the ``py`` domain, so they are
the cross-reference targets for the whole documentation set: a ``:py:func:``
reference anywhere, and every mention of an entry point in a reference page,
resolves to the page that documents it.  ``docs/reference/entrypoints.json``
records what was declared, which is how ``dumbpydoc`` knows to link to a page
rather than describe the entry point a second time.

Run it through ``build-docs.py``, which fetches the DocBook sources first.
"""

from __future__ import annotations

import argparse
import datetime
import glob
import json
import logging
import os
import pickle
import re
import sys
from typing import Any, Iterable

import lxml.etree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.dirname(HERE)
if PACKAGE_ROOT not in sys.path:
    # Run as ./generate.py, the package root is not on the path, and the
    # cached samples unpickle as directdocs.model.Sample.
    sys.path.insert(0, PACKAGE_ROOT)

from directdocs import model, references, rst  # noqa: E402
from directdocs.model import Function, Parameter, ParameterReference  # noqa: E402
from directdocs.rst import DOCBOOK_NS, MML_NS, Writer  # noqa: E402
from OpenGL import GL, GLE, GLU, GLUT, GLX  # noqa: E402,F401
from OpenGL import __version__  # noqa: E402
from OpenGL._bytes import as_8_bit  # noqa: E402

log = logging.getLogger('generate')

#: Where the pages are written, relative to the package root.
OUTPUT_DIRECTORY = os.path.join(PACKAGE_ROOT, 'docs', 'reference')

#: The checkout of https://github.com/KhronosGroup/OpenGL-Refpages, which
#: ``acquireoriginal.py`` makes.
REFPAGES = os.path.join(HERE, 'OpenGL-Refpages')

#: The API directories of that checkout, best first: an entry point declared in
#: more than one takes its page from the first that has it.
REFPAGE_SETS = ['gl4', 'gl2.1', 'es3.2', 'es3.1', 'es3.0', 'es3', 'es2.0', 'es1.1']

IMPORTED_PACKAGES = [GL, GLU, GLUT, GLE, GLX]
PACKAGES = ['GL', 'GLU', 'GLUT', 'GLE', 'GLX']

#: The Python module each package's entry points are exported from.  The
#: ``py:function`` declarations name it, so that a reference resolves whether
#: it is written ``glBegin`` or ``OpenGL.GL.glBegin``.
PACKAGE_MODULES = {
    'GL': 'OpenGL.GL',
    'GLU': 'OpenGL.GLU',
    'GLUT': 'OpenGL.GLUT',
    'GLE': 'OpenGL.GLE',
    'GLX': 'OpenGL.GLX',
}

XML_NS = 'http://www.w3.org/XML/1998/namespace'
XINCLUDE_NS = 'http://www.w3.org/2001/XInclude'
LINK_NS = 'http://www.w3.org/1999/xlink'

#: The entity file a reference-page directory carries, which pulls in the ISO
#: entity sets the MathML in those pages uses.
ENTITY_FILE = 'math.ent'

_NAMESPACES = tuple(as_8_bit(x) for x in [DOCBOOK_NS, MML_NS, LINK_NS])

#: Entity names the reference pages use that the ISO sets Khronos ships do not
#: declare.  They are declared after those sets, so where a set does define one
#: its definition is the one that stands: in XML the first declaration wins.
SUPPLEMENTARY_ENTITIES = {
    'CenterDot': 0x00B7,
    'Congruent': 0x2261,
    'DoubleVerticalBar': 0x2225,
    'Hat': 0x005E,
    'LeftFloor': 0x230A,
    'PartialD': 0x2202,
    'RightFloor': 0x230B,
    'VerticalBar': 0x2223,
    'mdash': 0x2014,
    'nbsp': 0x00A0,
    'ndash': 0x2013,
}


def entity_file(directory: str) -> str | None:
    """The entity set to parse a file in ``directory`` against.

    Each Khronos API directory carries its own ``math.ent``, which pulls in the
    ISO entity sets beside it.  The GLUT and GLE pages, which are kept here
    rather than at Khronos, use the same entity names without carrying the
    files, so they are parsed against the copy in the newest API directory.
    """
    local = os.path.join(directory, ENTITY_FILE)
    if os.path.isfile(local):
        return local
    for package in REFPAGE_SETS:
        shared = os.path.join(REFPAGES, package, ENTITY_FILE)
        if os.path.isfile(shared):
            return shared
    return None


def wrap(body: bytes, entities: str | None) -> bytes:
    """``body`` re-rooted in a ``book`` element that declares the namespaces.

    Every reference page names ``refentry`` as its root and declares the
    MathML entity sets in its own DOCTYPE, which has to go because it does not
    declare the namespaces the page goes on to use.  The replacement declares
    the entity sets again, so that ``&times;`` and its neighbours arrive as
    the characters they stand for rather than as an error.
    """
    declaration = b''
    if entities:
        declaration = b'    <!ENTITY %% mathent SYSTEM "%s"> %%mathent;\n' % (
            as_8_bit(entities.replace('"', '%22')),
        )
    supplementary = b''.join(
        b'    <!ENTITY %s "&#%d;">\n' % (as_8_bit(name), point)
        for name, point in sorted(SUPPLEMENTARY_ENTITIES.items())
    )
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<!DOCTYPE book [\n' + declaration + supplementary + b']>\n'
        b'<book xmlns="%s" xmlns:mml="%s" xmlns:xlink="%s">\n' % _NAMESPACES
    ) + body + b'\n</book>'

#: Modules with entry points of their own, listed on the reference index.
IMPLEMENTATION_MODULES = [
    ('OpenGL.error', 'The GL-specific error classes'),
    (
        'OpenGL.extensions',
        'Reaching OpenGL extensions, including the "alternate" mechanism',
    ),
    ('OpenGL.plugins', 'The plugin registry new data types are declared through'),
    ('OpenGL.arrays.vbo', 'The vertex buffer object abstraction'),
    ('OpenGL.GL.shaders', 'Compiling and linking GLSL shaders'),
]


class Reference(model.Reference):
    """Reference class with doc-set-specific coding"""

    def get_crossref(self, title, volume=None, section=None):
        if volume is None:
            volume = '3G'
        key = '%s.%s' % (title, volume)
        if '(' in title:
            title = title.split('(')[0]
        if key in self.sections:
            return self.sections[key]
        elif title in self.section_titles:
            return self.section_titles[title]
        elif title in self.functions:
            return self.functions[title]
        elif title.startswith('glX') or title.startswith('wgl'):
            log.debug(
                'Reference to %s in %s has no page',
                title,
                getattr(section, 'title', 'Unknown'),
            )
            return None
        else:
            # try a linear scan for suffixed version...
            for name in self.functions.keys():
                if self.suffixed_name(name, title) or self.suffixed_name(title, name):
                    return self.functions[name]
            return None

    def docname(self, target) -> str:
        """The Sphinx docname, within ``docs/reference``, for ``target``."""
        if isinstance(target, RefSect):
            return page_name(target.title)
        elif isinstance(target, Function):
            return self.docname(target.section)
        raise ValueError("""Don't know how to name a page for %r""" % (target,))

    def package_names(self):
        return PACKAGES

    def modules(self):
        return IMPORTED_PACKAGES


#: A page name has to survive being a filename on every platform and being a
#: docname in a URL.  One Khronos page is titled with a comma-separated pair.
_UNSAFE = re.compile(r'[^A-Za-z0-9_.-]+')


def page_name(title: str) -> str:
    return _UNSAFE.sub('_', title.strip())


#: A reference section's ``id``, reduced to what the section is.  The pages
#: spell it plainly (``parameters``, ``seealso``) or prefixed with the entry
#: point (``glBegin-parameters``), and a page with two of a kind numbers the
#: second (``parameters2``).
_SECTION_KIND = re.compile(
    r'^(?:.*?[-_])?(parameters|see_?also|description|errors|notes|'
    r'associatedgets|versions|examples?|copyright)\d*$',
    re.IGNORECASE,
)


def section_kind(id: str | None) -> str | None:
    """What kind of reference section ``id`` names, or ``None``."""
    if not id:
        return None
    match = _SECTION_KIND.match(id)
    if not match:
        return None
    return match.group(1).replace('_', '').lower()


class RefSect(model.RefSect):
    query_namespace = {
        'd': DOCBOOK_NS,
        'm': MML_NS,
    }

    def process(self, tree):
        self.id = tree[0].get('id')
        if not self.id:
            # newer files use a prefixed "id" attribute...
            self.id = tree[0].get('{%s}id' % (XML_NS,))
        assert self.id
        self.title = self.name = tree[0].xpath(
            './/d:refmeta/d:refentrytitle',
            namespaces=self.query_namespace,
        )[0].text
        self.functions = dict(
            [
                (x.text, Function(x.text, self))
                for x in tree[0].xpath(
                    './/d:refnamediv/d:refname',
                    namespaces=self.query_namespace,
                )
            ]
        )
        self.purpose = tree[0].xpath(
            './/d:refnamediv/d:refpurpose', namespaces=self.query_namespace
        )[0].text
        for func_prototype in tree[0].xpath(
            './/d:refsynopsisdiv/d:funcsynopsis/d:funcprototype',
            namespaces=self.query_namespace,
        ):
            self.process_funcprototype(func_prototype)
        for section in tree[0].xpath(
            './/d:refsect1', namespaces=self.query_namespace
        ):
            id = section.get('id') or section.get('{%s}id' % (XML_NS,))
            kind = section_kind(id)
            if kind == 'parameters':
                for varlist in section.xpath(
                    './d:variablelist', namespaces=self.query_namespace
                ):
                    self.process_variablelist(varlist)
            elif kind == 'seealso':
                for entry in section.xpath(
                    './/d:citerefentry', namespaces=self.query_namespace
                ):
                    title = rst.reference_name(entry)
                    volumes = entry.xpath(
                        './d:manvolnum', namespaces=self.query_namespace
                    )
                    if title:
                        self.see_also.append(
                            (title, volumes[0].text if volumes else None)
                        )
            else:
                if not id:
                    log.debug(
                        'Reference section without id in %s: %s',
                        self.title,
                        list(section.items()),
                    )
                self.discussions.append(section)
        # global search for referenced constants...
        for item in tree[0].xpath('.//d:constant', namespaces=self.query_namespace):
            self.constants[item.text.strip()] = True

    def process_funcprototype(self, node):
        funcdef = node[0]
        params = node[1:]
        return_value = funcdef.text.strip()
        funcname = None
        for child in funcdef:
            funcname = child.text
        paramresults = []
        for param in params:
            if not (
                param.tag.endswith('}void') or (param.text or '').strip() == 'void'
            ):
                typ = param.text
                paramname = None
                for item in param:
                    paramname = item.text
                    if item.tail:
                        typ += item.tail
                if paramname is None:
                    log.debug('Parameter without a name in %s', self.title)
                    continue
                paramresults.append(Parameter(data_type=typ, name=paramname))
        try:
            function = self.functions[funcname]
        except KeyError:
            function = Function(funcname, self)
            self.functions[funcname] = function
        function.return_value = return_value
        function.parameters = paramresults
        for param in paramresults:
            param.function = function

    def process_variablelist(self, node):
        """Process a variable list into annotations"""
        result = []
        for entry in node:
            terms = []
            description = None
            for item in entry:
                if item.tag.endswith('term'):
                    value = [
                        x.text.strip()
                        for x in item.iterdescendants()
                        if (x.text and x.tag.endswith('}parameter'))
                    ]
                    terms.extend(value)
                else:
                    description = item
            if terms:
                result.append(ParameterReference(terms, description))
        self.varrefs.extend(result)


HEADER_KILLER = re.compile(b'[<][!]DOCTYPE.*?[>]', re.MULTILINE | re.DOTALL)
DECLARATION_KILLER = re.compile(br'\A\s*<\?xml[^>]*\?>', re.DOTALL)


def strip_bad_header(data: bytes) -> bytes:
    """``data`` as a fragment fit to put inside the wrapper.

    Both the XML declaration and the DOCTYPE have to go: a declaration is only
    allowed at the start of a document, and the DOCTYPE does not declare the
    namespaces the file goes on to use.  GLUT and GLE have neither.
    """
    data = DECLARATION_KILLER.sub(b'', data)
    match = HEADER_KILLER.search(data)
    if not match:
        return data
    return data[match.end():]


def parser() -> Any:
    """A parser that resolves the entity sets the reference pages declare."""
    return ET.XMLParser(load_dtd=True, resolve_entities=True, no_network=True)


def parse_fragment(path: str) -> Any:
    """The file at ``path``, wrapped and parsed, comments removed."""
    directory = os.path.dirname(os.path.abspath(path))
    entities = entity_file(directory)
    with open(path, 'rb') as fh:
        data = wrap(strip_bad_header(fh.read()), entities)
    return filter_comments(
        ET.XML(data, parser(), base_url=os.path.abspath(path))
    )


#: The two XPointer forms the reference pages use.  Anything else is left for
#: the caller to notice.
_XPOINTER_ALL = 'xpointer(/*/*)'
_XPOINTER_ROLE = re.compile(r"^xpointer\(/\*/\*\[@role='([^']+)'\]/\*\)$")


def resolve_includes(tree: Any, source_dir: str, seen: set[str] | None = None) -> None:
    """Replace ``xi:include`` elements with what they include.

    The reference pages use XInclude for the table saying which OpenGL versions
    a command belongs to: one include brings in the column headings and another
    the row for this command's version set.  lxml's own XInclude does not
    evaluate the XPointer these use, so the two forms are resolved here.
    """
    seen = seen if seen is not None else set()
    for include in tree.xpath(
        './/xi:include', namespaces={'xi': XINCLUDE_NS}
    ):
        parent = include.getparent()
        if parent is None:
            continue
        href = include.get('href')
        pointer = include.get('xpointer') or _XPOINTER_ALL
        replacement: list[Any] = []
        path = os.path.join(source_dir, href) if href else None
        if path and os.path.isfile(path) and path not in seen:
            try:
                included = parse_fragment(path)
            except ET.XMLSyntaxError as err:
                log.debug('cannot include %s: %s', path, err)
            else:
                resolve_includes(included, source_dir, seen | {path})
                replacement = list(select(included[0], pointer))
        index = parent.index(include)
        tail = include.tail
        parent.remove(include)
        for offset, node in enumerate(replacement):
            parent.insert(index + offset, node)
        if replacement:
            replacement[-1].tail = (replacement[-1].tail or '') + (tail or '')
        elif index > 0:
            previous = parent[index - 1]
            previous.tail = (previous.tail or '') + (tail or '')
        else:
            parent.text = (parent.text or '') + (tail or '')


def select(root: Any, pointer: str) -> Iterable[Any]:
    """The nodes ``pointer`` names, for the two forms the pages use."""
    if pointer == _XPOINTER_ALL:
        return list(root)
    match = _XPOINTER_ROLE.match(pointer)
    if match:
        for child in root:
            if child.get('role') == match.group(1):
                return list(child)
        return []
    log.debug('unsupported xpointer: %s', pointer)
    return []


def load_file(filename: str) -> Any:
    try:
        tree = parse_fragment(filename)
    except Exception:
        log.error("Failure loading file: %r", filename)
        raise
    resolve_includes(tree, os.path.dirname(os.path.abspath(filename)))
    return tree


def filter_comments(tree: Any) -> Any:
    for element in list(tree):
        if isinstance(element.tag, str):
            filter_comments(element)
        else:
            tree.remove(element)
    return tree


def api_entry_point(name: str) -> str | None:
    for prefix in ['glu', 'glX', 'gl']:
        if name.startswith(prefix):
            return prefix
    return None


class PageLinks:
    """What :class:`~directdocs.rst.DocBookRenderer` asks about a page."""

    def __init__(self, reference: Reference, section: RefSect) -> None:
        self.reference = reference
        self.section = section
        self.parameters = {
            name: parameter_label(section, name)
            for varref in section.varrefs
            for name in varref.names
        }

    def entry_point_page(self, name: str) -> str | None:
        target = self.reference.get_crossref(name, section=self.section)
        if target is None:
            return None
        docname = self.reference.docname(target)
        if docname == page_name(self.section.title):
            # A page referring to itself; the reader is already here.
            return None
        return docname

    def parameter_label(self, name: str) -> str | None:
        return self.parameters.get(name)


def parameter_label(section: RefSect, name: str) -> str:
    """The Sphinx label for ``name`` as documented on ``section``'s page."""
    return 'ref-%s-param-%s' % (page_name(section.title).lower(), name.lower())


def python_signature(function: Any) -> str:
    """``name(arg, arg=default, *args, **named)`` for a Python entry point."""
    parts = []
    for parameter in function.parameters:
        name = parameter.name
        if isinstance(name, (list, tuple)):
            name = '(%s)' % (', '.join(str(x) for x in name),)
        if parameter.varargs:
            parts.append('*%s' % (name,))
        elif parameter.varnamed:
            parts.append('**%s' % (name,))
        elif parameter.has_default:
            parts.append('%s=%r' % (name, parameter.default))
        else:
            parts.append(str(name))
    return '%s(%s)' % (function.name, ', '.join(parts))


def c_prototype(function: Any) -> str:
    """The C declaration as the specification gives it."""
    parts = []
    for parameter in function.parameters:
        data_type = (parameter.data_type or '').strip()
        parts.append(('%s %s' % (data_type, parameter.name)).strip())
    return '%s %s(%s)' % (
        (function.return_value or 'void').strip(),
        function.name,
        ', '.join(parts) or 'void',
    )


def docstring_of(function: Any) -> str:
    try:
        text = function.docstring
    except Exception as err:  # a wrapper whose __doc__ is built lazily
        log.debug('no docstring for %s: %s', function, err)
        return ''
    if not isinstance(text, str):
        return ''
    import textwrap

    return textwrap.dedent(text).strip()


def write_docstring(docstring: str, writer: Writer) -> None:
    """Write an entry point's docstring into the directive body.

    PyOpenGL's docstrings are plain text laid out with indentation: a call
    signature, then a paragraph, then an indented list of what each argument
    means.  Rendered as reST that layout is a string of warnings, so anything
    with a second line goes in verbatim and only a one-line docstring is set as
    prose.
    """
    lines = docstring.split('\n')
    if len(lines) == 1:
        writer.paragraph(rst.escape(lines[0]))
    else:
        writer.literal_block(docstring)


class PageWriter:
    """Renders one reference page, and records what it declared."""

    def __init__(self, reference: Reference, declared: dict[str, str]) -> None:
        self.reference = reference
        #: Python entry point name -> the docname that declares it.  A name
        #: declared twice is indexed once, and the second page says so.
        self.declared = declared

    def render(self, section: RefSect) -> str:
        links = PageLinks(self.reference, section)
        renderer = rst.DocBookRenderer(links)
        writer = Writer()
        docname = page_name(section.title)

        writer.target('ref-%s' % (docname.lower(),))
        writer.heading(section.title, 0)
        if section.purpose:
            writer.paragraph(rst.escape(rst.collapse(section.purpose)))

        self.write_signatures(section, writer, renderer, docname)
        self.write_parameters(section, writer, renderer)

        for discussion in section.discussions:
            renderer.render_block(discussion, writer, 1)

        self.write_see_also(section, writer)
        self.write_samples(section, writer)
        return writer.render()

    def write_signatures(
        self,
        section: RefSect,
        writer: Writer,
        renderer: rst.DocBookRenderer,
        docname: str,
    ) -> None:
        if not section.functions:
            return
        module = PACKAGE_MODULES.get(section.package, 'OpenGL.GL')
        writer.heading('Signature', 1)
        for _name, function in sorted(section.functions.items()):
            if function.parameters or function.return_value:
                writer.blank()
                writer.line('.. container:: c-prototype')
                writer.blank()
                with writer.indent():
                    writer.line(rst.literal(c_prototype(function)))
                writer.blank()
            for name, pyfunc in sorted(function.python.items()):
                self.write_python_entry_point(name, pyfunc, module, writer, docname)

    def write_python_entry_point(
        self,
        name: str,
        pyfunc: Any,
        module: str,
        writer: Writer,
        docname: str,
    ) -> None:
        options = {'module': module}
        first = self.declared.setdefault(name, docname)
        if first != docname:
            # The same name from two reference pages: index the first and let
            # this one render without claiming the cross-reference target.
            options['no-index'] = ''
        writer.directive('py:function', python_signature(pyfunc), options)
        docstring = docstring_of(pyfunc)
        if docstring:
            with writer.indent():
                write_docstring(docstring, writer)

    def write_parameters(
        self, section: RefSect, writer: Writer, renderer: rst.DocBookRenderer
    ) -> None:
        if not section.varrefs:
            return
        writer.heading('Parameters', 1)
        #: A page that documents the same parameter in two sections -- the
        #: ``parameters`` and ``parameters2`` of an entry point with two
        #: signatures -- gets one target for it, on the first description.
        labelled: set[str] = set()
        for varref in section.varrefs:
            for name in varref.names:
                label = parameter_label(section, name)
                if label not in labelled:
                    labelled.add(label)
                    writer.target(label)
            writer.line(', '.join('*%s*' % (rst.escape(n),) for n in varref.names))
            body = Writer()
            if varref.description is not None:
                renderer.render(varref.description, body, 2)
            with writer.indent():
                writer.line(body.render().strip() or 'Undocumented.')
            writer.blank()

    def write_see_also(self, section: RefSect, writer: Writer) -> None:
        targets = section.get_crossrefs(self.reference)
        if not targets:
            return
        seen: dict[str, bool] = {}
        links = []
        for target in targets:
            docname = self.reference.docname(target)
            if docname in seen:
                continue
            seen[docname] = True
            links.append(':doc:`%s <%s>`' % (target.name, docname))
        if links:
            writer.heading('See also', 1)
            writer.paragraph(', '.join(links))

    def write_samples(self, section: RefSect, writer: Writer) -> None:
        if not section.samples:
            return
        writer.heading('Sample code references', 1)
        writer.paragraph(
            'These code samples appear to reference the entry points described '
            'here.  They are other people\'s projects, gathered by scanning '
            'source, so a sample may be old or may not use PyOpenGL at all.'
        )
        for key, samples in section.samples:
            writer.line('%s' % (rst.literal(key),))
            with writer.indent():
                for sample in samples:
                    lines = ', '.join(str(x[0]) for x in sample.positions[:20])
                    if len(sample.positions) > 20:
                        lines += ', ...'
                    writer.line(
                        '| %s `%s <%s>`__ -- lines %s'
                        % (
                            rst.escape(sample.projectName),
                            rst.escape(sample.deltaPath),
                            sample.url,
                            lines,
                        )
                    )
            writer.blank()

def write_index(reference: Reference, directory: str) -> None:
    """The reference's front page: a toctree and a table per package."""
    writer = Writer()
    writer.heading('OpenGL reference', 0)
    writer.paragraph(
        'The OpenGL reference pages with PyOpenGL\'s call signatures added to '
        'them: the C declaration the specification gives, the Python entry '
        'points that reach it, and the aliases PyOpenGL exports for it.  Each '
        'entry point is declared here, so a reference to it anywhere in this '
        'documentation set links to the page describing it.'
    )
    writer.paragraph(
        'The modules that have entry points of their own, rather than '
        'wrapping an OpenGL command, are in the :doc:`API pages '
        '<../api/index>`:'
    )
    for name, description in IMPLEMENTATION_MODULES:
        writer.line(':py:mod:`%s`' % (name,))
        with writer.indent():
            writer.line(description)
        writer.blank()

    packages = reference.packages()
    writer.directive('toctree', options={'hidden': '', 'maxdepth': '1'})
    with writer.indent():
        for _package, sections in packages:
            for _name, section in sections:
                writer.line(page_name(section.title))
    writer.blank()

    for package, sections in packages:
        if not sections:
            continue
        writer.heading('%s' % (package,), 1)
        writer.directive(
            'list-table',
            options={'widths': 'auto', 'header-rows': '1', 'class': 'entry-point-index'},
        )
        with writer.indent():
            writer.line('* - Entry point')
            writer.line('  - Purpose')
            for _name, section in sections:
                writer.line(
                    '* - :doc:`%s <%s>`'
                    % (section.title, page_name(section.title))
                )
                writer.line(
                    '  - %s' % (rst.escape(rst.collapse(section.purpose or '')),)
                )
        writer.blank()

    with open(os.path.join(directory, 'index.rst'), 'w', encoding='utf-8') as fh:
        fh.write(writer.render())


def refpage_files(limit_to: list[str]) -> list[tuple[str, str]]:
    """``(package, path)`` for every reference page to render."""
    base_names: set[str] = set()
    files: list[tuple[str, str]] = []
    for package in REFPAGE_SETS:
        pattern = os.path.join(REFPAGES, package, '*.xml')
        for filename in sorted(glob.glob(pattern)):
            base = os.path.basename(filename)
            api = api_entry_point(base)
            if not api:
                continue
            if limit_to and not any(filter in base for filter in limit_to):
                continue
            if base in base_names:
                log.debug('%s exists in more than one API set', base)
                continue
            base_names.add(base)
            files.append((api.upper(), filename))
    for section in ['GLUT', 'GLE']:
        pattern = os.path.join(HERE, 'original', section, '*.xml')
        for filename in sorted(glob.glob(pattern)):
            if limit_to and not any(
                filter in os.path.basename(filename) for filter in limit_to
            ):
                continue
            files.append((section, filename))
    return sorted(files)[::-1]


def load_samples() -> dict[str, Any]:
    """The sample-code index, where one has been built.

    ``references.py`` builds it by scanning checkouts of other people's
    projects.  Without it the pages are written without their sample sections
    rather than not written at all.
    """
    cache = os.path.join(HERE, references.CACHE_FILE)
    if os.path.isfile(cache):
        with open(cache, 'rb') as fh:
            return pickle.loads(fh.read())
    log.info('no sample index at %s; pages omit their sample sections', cache)
    return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument(
        'limit_to',
        nargs='*',
        help='only render pages whose filename contains one of these',
    )
    parser.add_argument(
        '--output',
        default=OUTPUT_DIRECTORY,
        help='directory to write the pages into (default: %(default)s)',
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='report every page written'
    )
    options = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if options.verbose else logging.INFO)

    if not os.path.isdir(REFPAGES):
        parser.error(
            'no DocBook sources at %s; run directdocs/acquireoriginal.py first'
            % (REFPAGES,)
        )
    os.makedirs(options.output, exist_ok=True)

    samples = load_samples()
    files = refpage_files(options.limit_to)
    log.info('Loading %d reference pages', len(files))
    reference = Reference()
    for package, path in files:
        log.debug('Loading: %s', path)
        try:
            tree = load_file(path)
        except (Exception, ET.XMLSyntaxError) as err:
            err.args += (path,)
            raise
        section = RefSect(package, reference)
        section.process(tree)
        reference.append(section)
        section.get_samples(samples)

    log.info('Resolving cross-references')
    reference.check_crossrefs()

    declared: dict[str, str] = {}
    pages = PageWriter(reference, declared)
    log.info('Writing %d pages to %s', len(reference.sections), options.output)
    written = 0
    for _name, section in sorted(reference.sections.items()):
        docname = page_name(section.title)
        target = os.path.join(options.output, '%s.rst' % (docname,))
        with open(target, 'w', encoding='utf-8') as fh:
            fh.write(pages.render(section))
        written += 1
        log.debug('Wrote %s', target)

    write_index(reference, options.output)

    manifest = os.path.join(options.output, 'entrypoints.json')
    with open(manifest, 'w', encoding='utf-8') as fh:
        json.dump(
            {
                'version': __version__,
                'generated': datetime.datetime.now().isoformat(timespec='seconds'),
                'entry_points': declared,
            },
            fh,
            indent=1,
            sort_keys=True,
        )
    log.info(
        '%d pages, %d entry points declared; manifest in %s',
        written,
        len(declared),
        manifest,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
