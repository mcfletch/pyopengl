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
import importlib
import json
import logging
import os
import pickle
import re
import sys
from typing import Any, Iterable, NamedTuple

import lxml.etree as ET

# Before OpenGL is imported.  With this set, a constant and an entry point
# carry the module whose declaration table built them, which is what
# `declaring_module` below reads to write a cross-reference that names one
# target rather than a name several modules answer to.  Taken out again once
# it has been read, so a child process inherits nothing.
_ANNOTATIONS_SET_HERE = 'PYOPENGL_MODULE_ANNOTATIONS' not in os.environ
if _ANNOTATIONS_SET_HERE:
    os.environ['PYOPENGL_MODULE_ANNOTATIONS'] = '1'

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.dirname(HERE)
if PACKAGE_ROOT not in sys.path:
    # Run as ./generate.py, the package root is not on the path, and the
    # cached samples unpickle as directdocs.model.Sample.
    sys.path.insert(0, PACKAGE_ROOT)

from directdocs import model, references, rst  # noqa: E402
from directdocs.model import (  # noqa: E402
    Function,
    Parameter,
    ParameterReference,
    c_prototype,
    python_signature,
)
from directdocs.rst import (  # noqa: E402
    DOCBOOK_NS,
    MML_NS,
    Writer,
    write_docstring,
)
from OpenGL import __version__  # noqa: E402
from OpenGL._bytes import as_8_bit  # noqa: E402

if _ANNOTATIONS_SET_HERE:
    os.environ.pop('PYOPENGL_MODULE_ANNOTATIONS', None)

log = logging.getLogger('generate')

#: Where the pages are written, relative to the package root.
OUTPUT_DIRECTORY = os.path.join(PACKAGE_ROOT, 'docs', 'reference')

#: The checkout of https://github.com/KhronosGroup/OpenGL-Refpages, which
#: ``acquireoriginal.py`` makes.
REFPAGES = os.path.join(HERE, 'OpenGL-Refpages')

#: The API directories of that checkout, best first: an entry point declared in
#: more than one takes its page from the first that has it.  ES 3.2 has no
#: directory of its own; its pages are in ``es3``, which carries the ES 3.x
#: pages together.  ``tests/directdocs/test_generate.py`` holds every name
#: here to being a directory that exists, since one that is not reads as an
#: API with no pages rather than as a mistake.
REFPAGE_SETS = ['gl4', 'gl2.1', 'es3.1', 'es3.0', 'es3', 'es2.0', 'es1.1']


class Api(NamedTuple):
    """One of the APIs PyOpenGL wraps, and where its reference lives.

    Each gets a directory of pages under ``docs/reference/`` and an index of
    its own, which is what makes the reference navigable: a reader who wants
    EGL should not have to know that ``eglInitialize`` sorts between
    ``glEnable`` and ``glutMainLoop``.
    """

    #: The directory under ``docs/reference/``, and the first part of every
    #: docname in it.
    key: str
    #: What it is called on its index and in the contents.
    title: str
    #: The Python package its entry points are exported from.  The
    #: ``py:function`` declarations name it, so ``OpenGL.GLES3.glBindTexture``
    #: and ``OpenGL.GL.glBindTexture`` are the two different things they are.
    module: str
    #: The reference-page directories its pages come from, best first.  Empty
    #: where Khronos publishes no reference pages for it, which is EGL, WGL and
    #: the two this project carries its own copies of.
    sources: tuple[str, ...]
    #: One line for the index.
    blurb: str


#: The name prefixes that say which API an entry point belongs to, longest
#: first: ``glutInit`` is GLUT rather than GLU rather than GL.
ENTRY_PREFIXES = ('glut', 'glu', 'glX', 'gle', 'gl', 'egl', 'wgl')

#: Which API a ``gl``-prefixed page belongs to, by the directory it came from.
#: The same entry point is in several of these and means something different
#: in each: ``glTexImage2D`` on desktop takes arguments ES has never had.
GL_SOURCE_APIS = {
    'gl4': 'gl',
    'gl2.1': 'gl',
    'es1.1': 'gles1',
    'es2.0': 'gles2',
    'es3': 'gles3',
    'es3.0': 'gles3',
    'es3.1': 'gles3',
}

APIS = [
    Api(
        'gl',
        'OpenGL',
        'OpenGL.GL',
        ('gl4', 'gl2.1'),
        'Desktop OpenGL, 1.1 through 4.6, and the extensions to it.',
    ),
    Api(
        'gles1',
        'OpenGL ES 1.1',
        'OpenGL.GLES1',
        ('es1.1',),
        'The fixed-function ES profile, for embedded and mobile hardware.',
    ),
    Api(
        'gles2',
        'OpenGL ES 2.0',
        'OpenGL.GLES2',
        ('es2.0',),
        'The first shader-only ES profile.',
    ),
    Api(
        'gles3',
        'OpenGL ES 3.x',
        'OpenGL.GLES3',
        ('es3.1', 'es3.0', 'es3'),
        'ES 3.0 through 3.2.',
    ),
    Api(
        'glu',
        'GLU',
        'OpenGL.GLU',
        ('gl2.1',),
        'The OpenGL utility library: quadrics, tessellation, NURBS and '
        'mipmap building.',
    ),
    Api(
        'glut',
        'GLUT',
        'OpenGL.GLUT',
        (),
        'Windows, input and a main loop, for a program that wants no other '
        'GUI toolkit.',
    ),
    Api(
        'gle',
        'GLE',
        'OpenGL.GLE',
        (),
        'The extrusion library: tubing, lathing and swept surfaces.',
    ),
    Api(
        'egl',
        'EGL',
        'OpenGL.EGL',
        (),
        'Contexts and surfaces on Linux, Android and anywhere without a '
        'display server.  See :ref:`offscreen rendering on EGL <offscreen-egl>`.',
    ),
    Api(
        'glx',
        'GLX',
        'OpenGL.GLX',
        ('gl2.1',),
        'Contexts and surfaces on X11.',
    ),
    Api(
        'wgl',
        'WGL',
        'OpenGL.WGL',
        (),
        'Contexts and surfaces on Windows.  See :ref:`offscreen rendering with '
        'pbuffers <offscreen-wgl>`.',
    ),
]

#: By key, for the lookups below.
BY_KEY = {api.key: api for api in APIS}

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
    """Every reference page, indexed per API.

    Per API rather than by name alone: the same entry point is in several of
    them, ``glTexBuffer`` is a page of desktop OpenGL and a page of ES 3.x, and
    a single table keyed by title keeps whichever was read last.
    """

    def __init__(self):
        super().__init__()
        #: API key -> entry point name -> the function, for cross-references.
        self.functions_by_api: dict[str, dict[str, Function]] = {}

    def append(self, section):
        key = (section.api.key, section.title)
        if key in self.sections:
            # Two source files with one title: `glGetBufferParameter` in the
            # 2.1 pages and `glGetBufferParameteriv` in the 4.x ones are the
            # same entry point written up twice.  The first wins, and the
            # sources are read newest first.
            log.debug('%s already has a page titled %s', section.api.key, section.title)
            return
        self.sections[key] = section
        self.section_titles[key] = section
        for function in section.functions.values():
            self.functions_for(section.api).setdefault(function.name, function)

    def functions_for(self, api: Api) -> dict[str, Function]:
        return self.functions_by_api.setdefault(api.key, {})

    def get_crossref(self, title, volume=None, section=None):
        """The page ``title`` names, preferring the API asking for it.

        A see-also in a GLES page that names ``glBindTexture`` means the ES
        one; the same name in a desktop page means the desktop one.  Where the
        asking API has no such page -- a GLU page pointing at ``glBegin`` --
        any API that does will do, taking them in the order they are declared,
        which puts desktop OpenGL first.
        """
        if '(' in title:
            title = title.split('(')[0]
        here = section.api if section is not None and hasattr(section, 'api') else None
        for api in ([here] if here else []) + [a for a in APIS if a is not here]:
            found = self._in_api(api, title)
            if found is not None:
                return found
        log.debug(
            'Reference to %s in %s has no page',
            title,
            getattr(section, 'title', 'Unknown'),
        )
        return None

    def _in_api(self, api: Api, title: str):
        section = self.sections.get((api.key, title))
        if section is not None:
            return section
        functions = self.functions_by_api.get(api.key, {})
        if title in functions:
            return functions[title]
        for name in functions:
            if self.suffixed_name(name, title) or self.suffixed_name(title, name):
                return functions[name]
        return None

    def docname(self, target) -> str:
        """The docname for ``target``, from the top of the source tree.

        Absolute rather than relative, because a page in one API's directory
        links to pages in another's: a GLU page's see-also names ``glBegin``.
        """
        if isinstance(target, RefSect):
            return '/reference/%s/%s' % (target.api.key, page_name(target.title))
        elif isinstance(target, Function):
            return self.docname(target.section)
        raise ValueError("""Don't know how to name a page for %r""" % (target,))

    def by_api(self) -> list[tuple[Api, list[RefSect]]]:
        """The sections each API has a page for, in name order."""
        grouped: dict[str, list[RefSect]] = {}
        for section in self.sections.values():
            grouped.setdefault(section.api.key, []).append(section)
        return [
            (api, sorted(grouped.get(api.key, []), key=lambda s: s.title.lower()))
            for api in APIS
        ]


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

    def __init__(self, api: Api, reference=None):
        super().__init__(api.key, reference)
        #: Which API this page belongs to.  The same entry point can be in
        #: several, and each gets its own page: ``glTexImage2D`` on desktop
        #: takes arguments ES has never had.
        self.api = api

    def get_module(self):
        """The Python module to look for this page's entry points in.

        ``None`` where the API's package cannot be imported here -- EGL
        without an EGL library, WGL anywhere but Windows.  The page is then
        written from the DocBook alone, without the Python signatures.
        """
        return imported_package(self.api)

    def find_python_functions(self):
        """Find this page's entry points, and their aliases, in the package.

        The base class keeps its results in one table for the whole reference;
        this keeps them per API, for the same reason the pages are per API.
        """
        source = self.get_module()
        if source is None:
            return
        known = self.reference.functions_for(self.api)
        for name, function in sorted(self.functions.items()):
            if not hasattr(source, function.name):
                continue
            function.python[name] = model.PyFunction(
                root_function=function,
                py_function=getattr(source, name),
                alias=name,
            )
            for other in sorted(dir(source)):
                if not (
                    self.reference.suffixed_name(other, function.name)
                    or self.reference.suffixed_name(function.name, other)
                ):
                    continue
                if self.has_function(other):
                    continue
                function.python[other] = model.PyFunction(
                    root_function=function,
                    py_function=getattr(source, other),
                    alias=other,
                )
                self.py_functions[other] = function
                known.setdefault(other, function)

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


#: The two XPointer forms the reference pages use.  Anything else is reported
#: to the caller rather than handled here.
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
        pointer = include.get('xpointer')
        replacement: list[Any] = []
        path = os.path.join(source_dir, href) if href else None
        if path and os.path.isfile(path) and path not in seen:
            try:
                included = parse_fragment(path)
            except ET.XMLSyntaxError as err:
                log.debug('cannot include %s: %s', path, err)
            else:
                resolve_includes(included, source_dir, seen | {path})
                if pointer is None:
                    # No XPointer means the whole document element, not its
                    # children.  The format tables -- `bufferbindings.xml` and
                    # its neighbours, on thirty pages -- are included this way,
                    # and taking the children instead drops the
                    # `informaltable` wrapper and leaves every cell to render
                    # as a paragraph of its own.
                    replacement = [included[0]]
                else:
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


def entry_prefix(name: str) -> str | None:
    """Which family of entry point ``name`` is, by its prefix.

    Longest first, so that ``glutInit`` is GLUT rather than GLU rather than
    GL, and ``gleLathe`` is GLE rather than GL.
    """
    for prefix in ENTRY_PREFIXES:
        if name.startswith(prefix):
            return prefix
    return None


#: The prefixes that name an API outright.  ``gl`` does not: the same
#: ``gl``-prefixed page is desktop OpenGL in one directory and ES in another.
PREFIX_APIS = {'glu': 'glu', 'glX': 'glx', 'glut': 'glut', 'gle': 'gle',
               'egl': 'egl', 'wgl': 'wgl'}


def api_of_page(directory: str, basename: str) -> Api | None:
    """The API a reference page in ``directory`` belongs to."""
    prefix = entry_prefix(basename)
    if prefix is None:
        return None
    key = PREFIX_APIS.get(prefix) or GL_SOURCE_APIS.get(directory)
    return BY_KEY.get(key) if key else None


_IMPORTED: dict[str, Any] = {}


def imported_package(api: Api) -> Any:
    """``api``'s Python package, or ``None`` where it will not import here.

    EGL wants an EGL library and WGL wants Windows, so on any one machine some
    of these are absent.  That costs those pages their Python signatures and
    their index its entry-point list, which is said on the page rather than
    left to be noticed.
    """
    if api.module not in _IMPORTED:
        try:
            _IMPORTED[api.module] = importlib.import_module(api.module)
        except Exception as err:
            log.warning('%s will not import here: %s', api.module, err)
            _IMPORTED[api.module] = None
    return _IMPORTED[api.module]


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
        if docname == self.reference.docname(self.section):
            # A page referring to itself; the reader is already here.
            return None
        return docname

    def parameter_label(self, name: str) -> str | None:
        return self.parameters.get(name)


def page_label(section: RefSect) -> str:
    """The label for ``section``'s page.

    The API is in it because the page name is not unique on its own:
    ``glBindTexture`` is a page of desktop OpenGL and a page of ES 3.x.
    """
    return 'ref-%s-%s' % (section.api.key, page_name(section.title).lower())


def parameter_label(section: RefSect, name: str) -> str:
    """The Sphinx label for ``name`` as documented on ``section``'s page."""
    return '%s-param-%s' % (page_label(section), name.lower())


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


class PageWriter:
    """Renders one reference page, and records what it declared."""

    def __init__(
        self, reference: Reference, declared: dict[str, dict[str, str]]
    ) -> None:
        self.reference = reference
        #: Python entry point name -> the docname that declares it.  A name
        #: declared twice is indexed once, and the second page says so.
        self.declared = declared

    def render(self, section: RefSect) -> str:
        links = PageLinks(self.reference, section)
        renderer = rst.DocBookRenderer(links)
        writer = Writer()
        # What the rest of the set has to write to reach this page: the API's
        # directory and the page in it.
        docname = '%s/%s' % (section.api.key, page_name(section.title))

        writer.target(page_label(section))
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
        module = section.api.module
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
        # Per module, not per name: `glBindTexture` is an entry point of
        # desktop OpenGL and of ES, they are declared as
        # `OpenGL.GL.glBindTexture` and `OpenGL.GLES3.glBindTexture`, and each
        # has a page of its own.
        for_module = self.declared.setdefault(module, {})
        first = for_module.setdefault(name, docname)
        if first != docname:
            # The same name from two reference pages: index the first and let
            # this one render without claiming the cross-reference target.
            options['no-index'] = ''
        writer.directive('py:function', python_signature(pyfunc), options)
        docstring = docstring_of(pyfunc)
        if docstring:
            # What has been declared for this API so far.  The pages are
            # written in one pass, so a docstring links to an entry point whose
            # page has already been reached; a see-also covers the rest.
            with writer.indent():
                write_docstring(docstring, writer, self.declared.get(module, {}))

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

def entry_points_of(api: Api) -> list[str]:
    """The entry points ``api``'s package exports, in name order.

    Read from the package rather than from the reference pages, because that
    is what PyOpenGL actually offers: EGL and WGL have no Khronos reference
    pages at all, and every API has extension entry points that never got one.
    """
    package = imported_package(api)
    if package is None:
        return []
    import types

    from OpenGL.constant import Constant

    return sorted(
        name
        for name, value in vars(package).items()
        if not name.startswith('_')
        and callable(value)
        and not isinstance(value, (type, types.ModuleType, Constant))
        and entry_prefix(name) is not None
    )


def declaring_module(api: Api, name: str) -> str:
    """The module that declares ``name``, fully qualified.

    An entry point says which declaration table it came from, and the module
    documenting it is the friendly one of that name -- which is the rule
    ``dumbpydoc`` declares by, so naming it here is naming the one target
    there is.  A bare name would be searched for instead, and 76 of desktop
    OpenGL's extension entry points share a name with an ES one, so the search
    would find two and link to neither.
    """
    package = imported_package(api)
    if package is None:
        return api.module
    value = getattr(package, name, None)
    module = (getattr(value, '__module__', None) or api.module).replace(
        '.raw', '', 1
    )
    if module == api.module:
        return module
    # The module a name says it came from is not always a module that has it.
    # The type-suffixed array forms -- `glColorPointerb` and its two dozen
    # neighbours -- are built in `OpenGL.GL.pointers` and put straight into
    # the package, keeping the `__module__` of the entry point they decorate.
    # `dumbpydoc` declares a name on a module that exports it, so this asks
    # the same question.
    try:
        candidate = importlib.import_module(module)
    except Exception as err:
        log.debug('cannot check %s for %s: %s', module, name, err)
        return api.module
    return module if hasattr(candidate, name) else api.module


def extension_modules(api: Api) -> list[tuple[str, list[str]]]:
    """``(vendor package, extension modules)`` for ``api``, in name order."""
    package = imported_package(api)
    if package is None:
        return []
    import pkgutil

    result = []
    for entry in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        if not entry.ispkg or entry.name.startswith('_'):
            continue
        vendor = '%s.%s' % (api.module, entry.name)
        try:
            loaded = importlib.import_module(vendor)
        except Exception as err:
            log.debug('cannot list %s: %s', vendor, err)
            continue
        names = sorted(
            '%s.%s' % (vendor, child.name)
            for child in pkgutil.iter_modules(loaded.__path__)
            if not child.name.startswith('_')
        )
        if names:
            result.append((vendor, names))
    return result


def write_reference_index(reference: Reference, directory: str) -> None:
    """The reference's front page: one row per API, linking to its index."""
    writer = Writer()
    writer.heading('Reference', 0)
    writer.paragraph(
        'The OpenGL reference pages with PyOpenGL\'s call signatures added to '
        'them: the C declaration the specification gives, the Python entry '
        'points that reach it, the aliases PyOpenGL exports for it, and links '
        'to code that calls it.'
    )
    writer.paragraph(
        'One index per API.  The same entry point can be in several of them '
        'and mean something different in each, so each has its own page: '
        '``glTexImage2D`` on desktop takes arguments ES has never had.'
    )

    counts = {api.key: len(sections) for api, sections in reference.by_api()}
    # Hidden: the table below is the visible list, and two of them on one page
    # is one too many.  The toctree is still what puts the APIs in the sidebar
    # and gives the pages a parent.
    writer.directive('toctree', options={'hidden': '', 'maxdepth': '1'})
    with writer.indent():
        for api in APIS:
            writer.line('%s/index' % (api.key,))
    writer.blank()

    writer.directive(
        'list-table',
        options={'widths': 'auto', 'header-rows': '1', 'class': 'entry-point-index'},
    )
    with writer.indent():
        writer.line('* - API')
        writer.line('  - Module')
        writer.line('  - Pages')
        writer.line('  - What it covers')
        for api in APIS:
            writer.line('* - :doc:`%s <%s/index>`' % (api.title, api.key))
            writer.line('  - :py:mod:`%s`' % (api.module,))
            writer.line('  - %s' % (counts.get(api.key) or '--',))
            writer.line('  - %s' % (api.blurb,))
    writer.blank()

    writer.heading('The rest of the package', 1)
    writer.paragraph(
        'Modules with entry points of their own, rather than wrappers around '
        'an OpenGL command, are described in the :doc:`API pages '
        '</api/index>`:'
    )
    for name, description in IMPLEMENTATION_MODULES:
        writer.line(':py:mod:`%s`' % (name,))
        with writer.indent():
            writer.line(description)
        writer.blank()

    with open(os.path.join(directory, 'index.rst'), 'w', encoding='utf-8') as fh:
        fh.write(writer.render())


def write_api_index(
    api: Api, sections: list[RefSect], directory: str
) -> None:
    """One API's index: its entry points, and its extension modules."""
    writer = Writer()
    writer.heading(api.title, 0)
    writer.paragraph(api.blurb)
    writer.paragraph(
        'Exported from :py:mod:`%s`.  :doc:`Back to the reference </reference/index>`.'
        % (api.module,)
    )

    documented = {
        name for section in sections for name in section.functions
    } | {name for section in sections for name in section.py_functions}

    if sections:
        writer.directive('toctree', options={'hidden': '', 'maxdepth': '1'})
        with writer.indent():
            for section in sections:
                writer.line(page_name(section.title))
        writer.blank()

        writer.heading('Reference pages', 1)
        writer.directive(
            'list-table',
            options={
                'widths': 'auto',
                'header-rows': '1',
                'class': 'entry-point-index',
            },
        )
        with writer.indent():
            writer.line('* - Entry point')
            writer.line('  - Purpose')
            for section in sections:
                writer.line(
                    '* - :doc:`%s <%s>`'
                    % (section.title, page_name(section.title))
                )
                writer.line(
                    '  - %s' % (rst.escape(rst.collapse(section.purpose or '')),)
                )
        writer.blank()

    exported = entry_points_of(api)
    remaining = [name for name in exported if name not in documented]
    if remaining:
        writer.heading('Entry points with no reference page', 1)
        writer.paragraph(
            'Extensions, and whatever else Khronos publishes no reference page '
            'for.  Each links to its declaration on the module that exports it.'
            if sections
            else 'Khronos publishes no reference pages for this API, so each '
            'entry point links to its declaration on the module that exports '
            'it.'
        )
        writer.paragraph(
            ', '.join(
                ':py:func:`~%s.%s`' % (declaring_module(api, name), name)
                for name in remaining
            )
        )
    elif not exported and not sections:
        writer.paragraph(
            '%s could not be imported where this was built, so its entry '
            'points are not listed here.  They are in the :doc:`API pages '
            '</api/index>`.' % (api.module,)
        )

    vendors = extension_modules(api)
    if vendors:
        writer.heading('Extension modules', 1)
        writer.paragraph(
            'One module per extension, each documented in the :doc:`API pages '
            '</api/index>`.  Importing one is how a program reaches an '
            'extension\'s entry points by the extension rather than by the '
            'version that adopted it; see :doc:`/using`.'
        )
        for vendor, names in vendors:
            writer.heading(vendor.rsplit('.', 1)[-1], 2)
            # `py:mod` rather than `doc`: it goes to the module's declaration
            # wherever that page turns out to be, and a module that could not
            # be documented on this machine renders as its own name rather
            # than as a link to a page that is not there.
            writer.paragraph(
                ', '.join(
                    ':py:mod:`%s <%s>`' % (name.rsplit('.', 1)[-1], name)
                    for name in names
                )
            )

    api_directory = os.path.join(directory, api.key)
    os.makedirs(api_directory, exist_ok=True)
    with open(
        os.path.join(api_directory, 'index.rst'), 'w', encoding='utf-8'
    ) as fh:
        fh.write(writer.render())


def refpage_files(limit_to: list[str]) -> list[tuple[Api, str]]:
    """``(api, path)`` for every reference page to render.

    Deduplicated per API rather than across all of them.  The same file name
    appears in several of the Khronos directories, and the old scan kept the
    first and dropped the rest -- which meant every ES page whose name also
    existed on the desktop was thrown away, and the ones that survived were
    filed under GL.
    """
    seen: set[tuple[str, str]] = set()
    files: list[tuple[Api, str]] = []

    def wanted(base: str) -> bool:
        return not limit_to or any(filter in base for filter in limit_to)

    for directory in REFPAGE_SETS:
        pattern = os.path.join(REFPAGES, directory, '*.xml')
        for filename in sorted(glob.glob(pattern)):
            base = os.path.basename(filename)
            api = api_of_page(directory, base)
            if api is None or not wanted(base):
                continue
            if (api.key, base) in seen:
                log.debug('%s is in more than one %s directory', base, api.key)
                continue
            seen.add((api.key, base))
            files.append((api, filename))

    # GLUT and GLE are not at Khronos; this project carries their pages.
    for key in ('glut', 'gle'):
        api = BY_KEY[key]
        pattern = os.path.join(HERE, 'original', key.upper(), '*.xml')
        for filename in sorted(glob.glob(pattern)):
            base = os.path.basename(filename)
            if not wanted(base) or (api.key, base) in seen:
                continue
            seen.add((api.key, base))
            files.append((api, filename))

    # Left in the order they were read, which is the order REFPAGE_SETS
    # declares: where two files describe one entry point, the first wins.
    return files


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
    logging.basicConfig()
    # `setLevel` rather than `basicConfig(level=...)`: `references` configures
    # the root logger when it is imported, and basicConfig does nothing to a
    # root logger that already has a handler.
    logging.getLogger().setLevel(
        logging.DEBUG if options.verbose else logging.INFO
    )

    if not os.path.isdir(REFPAGES):
        parser.error(
            'no DocBook sources at %s; run directdocs/acquireoriginal.py first'
            % (REFPAGES,)
        )
    os.makedirs(options.output, exist_ok=True)

    samples = load_samples()
    if samples:
        log.info('%d entry points have sample code references', len(samples))
    files = refpage_files(options.limit_to)
    log.info('Loading %d reference pages', len(files))
    reference = Reference()
    for api, path in files:
        log.debug('Loading: %s', path)
        try:
            tree = load_file(path)
        except (Exception, ET.XMLSyntaxError) as err:
            err.args += (path,)
            raise
        section = RefSect(api, reference)
        section.process(tree)
        reference.append(section)
        section.get_samples(samples)

    log.info('Resolving cross-references')
    reference.check_crossrefs()

    declared: dict[str, dict[str, str]] = {}
    pages = PageWriter(reference, declared)
    written = 0
    for api, sections in reference.by_api():
        api_directory = os.path.join(options.output, api.key)
        os.makedirs(api_directory, exist_ok=True)
        for section in sections:
            target = os.path.join(
                api_directory, '%s.rst' % (page_name(section.title),)
            )
            with open(target, 'w', encoding='utf-8') as fh:
                fh.write(pages.render(section))
            written += 1
        write_api_index(api, sections, options.output)
        log.info(
            '%-6s %4d reference pages, %4d entry points, %4d extension modules',
            api.key,
            len(sections),
            len(entry_points_of(api)),
            sum(len(names) for _vendor, names in extension_modules(api)),
        )

    write_reference_index(reference, options.output)

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
        sum(len(names) for names in declared.values()),
        manifest,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
