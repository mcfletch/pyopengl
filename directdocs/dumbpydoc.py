#! /usr/bin/env python3
"""Writes a reStructuredText page for every module in the packages.

The pages go in ``docs/api/``, one per module, and are written by importing
each module and looking at what it holds -- which is the only way to see what
PyOpenGL actually exports, since most of it is built at import time from the
registry tables rather than written out as ``def``.

Everything found is declared in Sphinx's Python domain: ``py:module`` for the
module, ``py:class`` for each type with ``py:method`` and ``py:attribute``
under it, ``py:function`` for each entry point and ``py:data`` for each
constant.  So every name in the packages is a cross-reference target and
appears in the index: ``:py:func:`OpenGL.GL.glBegin``` and
``:py:data:`OpenGL.GL.GL_TRIANGLES``` both resolve, and so does a bare
``glBegin`` under the default role.

An entry point the reference pages already declare is *linked* rather than
declared a second time.  ``generate.py`` writes ``entrypoints.json`` saying
which those are.

Run it through ``build-docs.py``, which runs the reference generator first so
that the manifest is there.

Importing this module sets three ``PYOPENGL_*`` variables in the environment
and takes them out again once PyOpenGL has read them, which is what chooses
the configuration the pages are written from.  A variable the caller set is
left alone, and :func:`report_configuration` says so when the configuration in
front of a run is not the one the pages want.
"""

from __future__ import annotations

import os

# Before anything imports OpenGL.  The configuration is read once, when
# `OpenGL._configflags` is first touched, and these three are what the pages
# are written from: the ctypes entry points, which carry the argument names and
# the docstrings, and the annotation that says which module declares each name.
#
# Through the environment rather than by assignment, because assignment only
# works when this module is imported first -- and a process that had already
# imported OpenGL got a warning it could do nothing about rather than the
# configuration it asked for.  Only where the caller set nothing, so a build
# asking for something else on the command line still gets it.
_CONFIGURATION = {
    'PYOPENGL_DISPATCH': 'ctypes',
    'PYOPENGL_USE_ACCELERATE': '0',
    'PYOPENGL_MODULE_ANNOTATIONS': '1',
}
_SET_HERE = [name for name in _CONFIGURATION if name not in os.environ]
os.environ.update({name: _CONFIGURATION[name] for name in _SET_HERE})

import argparse  # noqa: E402
import glob  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import inspect  # noqa: E402
import pkgutil  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
import textwrap  # noqa: E402
import types  # noqa: E402
from ctypes import _CFuncPtr as CFunctionType  # noqa: E402
from typing import Any, Iterable  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE_ROOT = os.path.dirname(HERE)
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

from directdocs import model, rst  # noqa: E402
from directdocs.rst import Writer, write_docstring  # noqa: E402
from OpenGL import platform  # noqa: E402
from OpenGL.constant import Constant  # noqa: E402
from OpenGL.extensions import _Alternate as Alternate  # noqa: E402
from OpenGL.GLUT.special import GLUTCallback  # noqa: E402
from OpenGL.lazywrapper import _LazyWrapper as Lazy  # noqa: E402
from OpenGL.platform.baseplatform import _NullFunctionPointer as NullFunc  # noqa: E402
from OpenGL.wrapper import Wrapper  # noqa: E402

for _name in _SET_HERE:
    # PyOpenGL has read its configuration by now, so these have done their
    # work.  Taken back out again because `os.environ` is inherited: a process
    # that imports this module for one of its functions would otherwise hand
    # every child it starts a PyOpenGL configured for writing documentation.
    os.environ.pop(_name, None)

log = logging.getLogger('dumbpydoc')

CythonMethod = type(platform.PLATFORM.GL.glGetString)

# The entry-point type the C dispatch builds.  A build that documents the C
# implementation finds every gl* name to be one of these, so a page set without
# it is a page set with no functions in it.  Where that implementation is not
# installed there is nothing to match, and isinstance reads a nested empty
# tuple as exactly that.
try:
    from OpenGL._dispatch import _c as _dispatch_extension
except ImportError:
    GLProc: Any = ()
else:
    GLProc = _dispatch_extension.GLProc

#: Where the pages are written.
OUTPUT_DIRECTORY = os.path.join(PACKAGE_ROOT, 'docs', 'api')

#: What ``generate.py`` leaves saying which entry points the reference pages
#: declare, so that this does not declare them a second time.
ENTRYPOINTS = os.path.join(PACKAGE_ROOT, 'docs', 'reference', 'entrypoints.json')

#: The packages documented by a plain run.  PyOpenGL and its accelerators;
#: anything built on top of them documents itself.
PROJECTS = ['OpenGL', 'OpenGL_accelerate']

#: Module-name fragments that are not part of a package's public surface.
SKIP_FRAGMENTS = ('.tests.', '.tests', '.test_', '.__main__')

#: Left out of the pages entirely.  `OpenGL.raw` is not a hierarchy of modules
#: in the ordinary sense: there are no files, only declaration tables that a
#: finder turns into namespaces on demand.  Every name in it is exported by the
#: module beside it -- `OpenGL.GL.ARB.foo` for `OpenGL.raw.GL.ARB.foo` -- which
#: is where a reader should be sent and where the name is declared.  A name
#: with no such counterpart, `GLfloat` and its neighbours from
#: `OpenGL.raw.GL._types`, is declared by the package that exports it.
SKIP_PACKAGES = ('OpenGL.raw',)

#: The top-level packages a plain run documents.  A name that comes from
#: outside them under its own name is somebody else's and is not described
#: here; under one of ours it is ours, which is how `GLdouble = c_double` is
#: documented and a bare `c_double` beside it is not.
DEFAULT_ROOTS = tuple(name.split('.')[0] for name in PROJECTS)


class PyModule(object):
    OPENGL_FUNCS = (
        NullFunc,
        Alternate,
        Wrapper,
        GLUTCallback,
        Lazy,
        CFunctionType,
        CythonMethod,
        GLProc,
    )
    INTERESTING_TYPES = OPENGL_FUNCS + (
        Constant,
        types.FunctionType,
        type,
        types.ModuleType,
    )
    FUNCTIONAL_TYPES = OPENGL_FUNCS + (types.FunctionType,)
    CLASS_TYPES = (type,)
    CONSTANT_TYPES = (Constant,)
    MODULE_TYPES = (types.ModuleType,)
    FT_MAP = [
        ('functions', FUNCTIONAL_TYPES),
        ('constants', CONSTANT_TYPES),
        ('imports', MODULE_TYPES),
        ('classes', CLASS_TYPES),
    ]

    def __init__(self, name, roots=None):
        self.name = name
        self.basename = name.split('.')[-1]
        #: The packages being documented; see :func:`DEFAULT_ROOTS`.
        self.roots = tuple(roots) if roots else DEFAULT_ROOTS
        self.functions = []
        self.constants = []
        self.classes = []
        self.imports = []
        self.modules = []

    @property
    def target(self):
        return self.mod

    @property
    def is_package(self):
        # A module need not have a __file__ at all: the ones under OpenGL.raw
        # are built from the shipped declaration tables, and a module with no
        # file is a leaf rather than a package.
        path = getattr(self.mod, '__file__', None)
        if not path:
            return False
        base = os.path.splitext(os.path.basename(path))[0]
        return base == '__init__'

    _mod = None

    @property
    def mod(self):
        if not self._mod:
            self._mod = __import__(
                self.name,
                {},
                {},
                self.name.split('.'),
            )
        return self._mod

    @property
    def docstring(self):
        if self.mod.__doc__:
            return textwrap.dedent(self.mod.__doc__)
        return None

    _inspected = False

    def inspect(self):
        """Inspect the module"""
        if self._inspected:
            return
        self._inspected = True
        for key, value in sorted(
            list(self.mod.__dict__.items()), key=lambda x: x[0].lower()
        ):
            if key.startswith('_') or not self.interesting(value):
                continue
            if self.imported_from_elsewhere(key, value):
                continue
            for attr, types_ in self.FT_MAP:
                if not isinstance(value, types_):
                    continue
                # First match wins.  A ctypes function pointer type is both a
                # class and one of the callable types, and adding it to both
                # collections declares the same name twice on one page.
                collection = getattr(self, attr)
                is_duplicate = False
                for _key, existing in collection:
                    if getattr(existing, 'target', existing) is value:
                        if not hasattr(existing, 'aliases'):
                            existing.aliases = []
                        existing.aliases.append(key)
                        is_duplicate = True
                if not is_duplicate:
                    inspector = getattr(self, 'inspect_%s' % (attr,), None)
                    if inspector:
                        value = inspector(value, key)
                    collection.append((key, value))
                break

    def interesting(self, obj):
        """Whether this object is worth a place on a page.

        Every public name of the right kind is, wherever it was defined.  Which
        page *declares* it is settled once for the whole set by
        :func:`claim_owners`, and a module that re-exports a name says so
        rather than describing it again -- so the filtering that used to happen
        here, by comparing ``__module__`` against the module being documented,
        is no longer this function's job.
        """
        return isinstance(obj, self.INTERESTING_TYPES)

    def imported_from_elsewhere(self, key, obj):
        """Whether ``key`` is another package's name, imported under it.

        ``from ctypes import *`` puts `c_double` and `CFunctionType` in a
        module's namespace, and `int` arrives the same way.  Those belong to
        whoever defines them.  A name PyOpenGL gives something of somebody
        else's -- ``GLdouble = c_double`` -- is PyOpenGL's and stays.
        """
        if isinstance(obj, types.ModuleType):
            return False
        module = getattr(obj, '__module__', None)
        if module is None or module.split('.')[0] in self.roots:
            return False
        return key == getattr(obj, '__name__', key)

    def owns(self, obj):
        """Whether ``obj`` looks defined here rather than imported.

        ``__module__`` is what an object says about itself.  For a constant or
        an entry point that is the module whose declaration table it came from,
        which is the module a reader should be sent to; the friendly module of
        the same name -- ``OpenGL.GL.VERSION.GL_1_0`` beside
        ``OpenGL.raw.GL.VERSION.GL_1_0`` -- is the one people import from, and
        counts as the same place.
        """
        module = getattr(obj, '__module__', None)
        if module is None:
            return True
        return self.name in (
            module,
            module.replace('.raw', ''),
            module.replace('.raw', '').replace('_DEPRECATED', ''),
        )

    def inspect_functions(self, func, name):
        return model.PyFunction(None, func, alias=name)

    def inspect_classes(self, cls, name):
        """Inspect the classes given"""
        return Class(cls, self)


class Class(object):
    """Metadata describing a class to be documented"""

    def __init__(self, cls, module=None):
        self.cls = cls
        self.basename = cls.__name__
        self.module = module or self.find_module(cls)
        self.name = '%s.%s' % (self.module.name, cls.__name__)
        self.functions = []
        self.properties = []
        self.inspect()

    @property
    def target(self):
        return self.cls

    @classmethod
    def find_module(cls, target):
        if target.__module__:
            return PyModule(target.__module__)
        raise RuntimeError('%r has no module to document it under' % (target,))

    @property
    def bases(self):
        return [Class(x) for x in self.cls.__bases__]

    @property
    def docstring(self):
        if self.cls.__doc__:
            try:
                return textwrap.dedent(self.cls.__doc__ or '')
            except TypeError:
                return None
        return None

    def inspect(self):
        """Introspect to find methods, properties, etceteras"""
        described = self.described_attributes()
        for key, value in sorted(
            list(self.cls.__dict__.items()), key=lambda x: x[0].lower()
        ):
            if isinstance(
                value,
                (
                    types.FunctionType,
                    types.MethodType,
                    types.BuiltinFunctionType,
                    types.BuiltinMethodType,
                    classmethod,
                    staticmethod,
                ),
            ):
                self.functions.append((key, model.PyFunction(None, value, alias=key)))
            elif hasattr(value, '__get__') and key not in ('__dict__', '__weakref__'):
                annotation, default = described.get(key, (None, NOT_SET))
                self.properties.append(
                    (key, Property(value, key, self, annotation, default))
                )

    def described_attributes(self):
        """``name -> (type, default)`` for the attributes, where those exist.

        An attribute is often only a name here: a ``__slots__`` entry is a
        descriptor and says nothing about itself.  What it is and what it
        defaults to are in the annotations, or in the signature of the
        ``__init__`` that sets it -- which for a class written this way is the
        only place they are written down at all.
        """
        described = {}
        for base in reversed(getattr(self.cls, '__mro__', [self.cls])):
            for name, annotation in (
                getattr(base, '__annotations__', None) or {}
            ).items():
                described[name] = (annotation_text(annotation), NOT_SET)
        try:
            signature = inspect.signature(self.cls.__init__)
        except (TypeError, ValueError):
            return described
        for name, parameter in signature.parameters.items():
            if name == 'self' or name.startswith('*'):
                continue
            annotation = described.get(name, (None, NOT_SET))[0]
            if parameter.annotation is not inspect.Parameter.empty:
                annotation = annotation_text(parameter.annotation)
            default = (
                NOT_SET
                if parameter.default is inspect.Parameter.empty
                else parameter.default
            )
            described[name] = (annotation, default)
        return described


#: An attribute with no default is not an attribute whose default is None.
NOT_SET = object()


def annotation_text(annotation):
    """An annotation as it should read in the page.

    A module using ``from __future__ import annotations`` has these already as
    the strings they were written as, which is what a reader wants; anything
    else is turned into one.
    """
    if isinstance(annotation, str):
        return annotation
    return getattr(annotation, '__name__', None) or str(annotation)


class Property(object):
    def __init__(self, target, name, cls, annotation=None, default=NOT_SET):
        self.cls = cls
        self.target = target
        self.name = name
        #: What it holds, where anything says so.
        self.annotation = annotation
        #: What it is when nothing sets it, or :data:`NOT_SET`.
        self.default = default

    @property
    def docstring(self):
        if self.target.__doc__:
            try:
                return textwrap.dedent(self.target.__doc__ or '')
            except TypeError:
                return None
        return None


# ----------------------------------------------------------------------
# rendering


def docstring_lines(obj: Any) -> str:
    """``obj``'s docstring, or ``''`` where it has none that can be read."""
    try:
        text = obj.docstring
    except Exception as err:  # a wrapper whose __doc__ is built on demand
        log.debug('no docstring for %r: %s', obj, err)
        return ''
    if not isinstance(text, str):
        return ''
    return text.strip()


def attribute_options(prop: Any) -> dict[str, str]:
    """The ``:type:`` and ``:value:`` for an attribute, where they are known."""
    options = {}
    if prop.annotation:
        options['type'] = prop.annotation
    if prop.default is not NOT_SET:
        try:
            options['value'] = repr(prop.default)
        except Exception as err:
            log.debug('cannot show the default of %s: %s', prop.name, err)
    return options


def base_name(base: Any) -> str:
    """A base class as it should read in a class declaration.

    ``object`` is spelled ``object``: every class has it somewhere and
    ``builtins.object`` says nothing extra.
    """
    name = base.name
    if name.startswith('builtins.'):
        return name[len('builtins.'):]
    return name


def constant_value(constant: Any) -> str:
    """``constant``'s value, as the header file would give it."""
    try:
        if isinstance(constant, int) and not isinstance(constant, bool):
            return '0x%X' % (constant,) if constant >= 0 else str(int(constant))
        if isinstance(constant, float):
            return repr(float(constant))
        if isinstance(constant, bytes):
            return repr(constant)
    except Exception as err:
        log.debug('cannot read the value of %r: %s', constant, err)
    return ''


#: Where an object is declared and under what name: ``(module, name)``.
Owner = tuple


def identity(value: Any, module: PyModule, name: str) -> tuple[str, str]:
    """What makes two exports of a name the same thing.

    Not the identity of the object: the friendly module beside a declaration
    table builds its own entry point for each command, so ``OpenGL.GL.glBegin``
    and ``OpenGL.raw.GL.VERSION.GL_1_0.glBegin`` are two objects standing for
    one command.  What they agree on is the module the declaration belongs to,
    which each reports as its ``__module__``, so that and the name are the key.

    A hand-written module that wraps an entry point rather than re-exporting it
    reports itself, and is a separate thing with a page entry of its own --
    which is right, since it behaves differently from what it wraps.
    """
    target = getattr(value, 'target', value)
    return (getattr(target, '__module__', None) or module.name, name)


def claim_owners(modules: Iterable[PyModule]) -> dict[tuple[str, str], Owner]:
    """Decide which module declares each name.

    A name in PyOpenGL is usually reachable from several modules: the
    declaration table's own module, the friendly module beside it, and the
    package that re-exports both.  Declaring it on each would put the same
    entry in the index several times over and leave a cross-reference to it
    ambiguous, so one module is chosen -- the one that looks like where the
    name is defined, and failing that the shallowest module that has it.
    """
    claims: dict[tuple[str, str], tuple[tuple[int, int, str], Owner]] = {}
    for module in modules:
        for kind in ('functions', 'constants', 'classes'):
            for name, value in getattr(module, kind):
                key = identity(value, module, name)
                rank = (
                    0 if module.owns(getattr(value, 'target', value)) else 1,
                    module.name.count('.'),
                    module.name,
                )
                current = claims.get(key)
                if current is None or rank < current[0]:
                    claims[key] = (rank, (module.name, name))
    return {key: owner for key, (_rank, owner) in claims.items()}


class Renderer:
    """Writes the page for one module."""

    def __init__(
        self,
        entry_points: dict[str, dict[str, str]],
        claims: dict[tuple[str, str], Owner],
    ) -> None:
        #: Entry point name -> the reference page that declares it.
        self.entry_points = entry_points
        #: What :func:`identity` returns -> the module and name declaring it.
        self.claims = claims
        #: The modules that get a page, so a breadcrumb only names pages that
        #: are there.  Filled in by :func:`render_projects`.
        self.documented: set[str] = set()

    def reference_link(self, module: PyModule, name: str) -> str | None:
        page = self.entry_points.get(api_package(module.name), {}).get(name)
        if page is None:
            return None
        return ':doc:`%s </reference/%s>`' % (name, page)

    def owner(self, module: PyModule, name: str, value: Any) -> Owner | None:
        """Where ``value`` is declared, or ``None`` if it is declared here."""
        claimed = self.claims.get(identity(value, module, name))
        if claimed is None or claimed[0] == module.name:
            return None
        return claimed

    def render(self, module: PyModule) -> str:
        writer = Writer()
        writer.directive('py:module', module.name)
        writer.heading(module.name, 0)
        self.write_breadcrumb(module, writer)
        write_docstring(
            docstring_lines(module), writer, self.entry_points_for(module)
        )

        self.write_submodules(module, writer)
        self.write_functions(module, writer)
        self.write_classes(module, writer)
        self.write_constants(module, writer)
        self.write_reexports(module, writer)
        self.write_imports(module, writer)
        return writer.render()

    def entry_points_for(self, module: PyModule) -> dict[str, str]:
        """The reference pages a docstring on ``module`` may mention.

        Its own API's, and desktop OpenGL's for a module that is not part of
        one -- `OpenGL.arrays.vbo` and its neighbours talk about `glBindBuffer`
        rather than about anything of their own.
        """
        return self.entry_points.get(
            api_package(module.name)
        ) or self.entry_points.get('OpenGL.GL', {})

    def write_breadcrumb(self, module: PyModule, writer: Writer) -> None:
        """A line of links up to the packages this module is inside.

        Sphinx gives a page no way up on its own, and a reader who arrived at
        `OpenGL.Tk.widget` from a search has nothing saying that `OpenGL.Tk`
        exists.
        """
        parts = module.name.split('.')
        ancestors = [
            '.'.join(parts[:i])
            for i in range(1, len(parts))
            if '.'.join(parts[:i]) in self.documented
        ]
        if not ancestors:
            return
        writer.paragraph(
            ' / '.join(':doc:`%s <%s>`' % (name, name) for name in ancestors)
            + ' / **%s**' % (parts[-1],)
        )

    def write_reexports(self, module: PyModule, writer: Writer) -> None:
        """Say which modules this one passes on the names of.

        ``OpenGL.GL`` offers a few thousand names that belong to the version
        and extension modules underneath it.  Listing each one here would be
        a page of links and a second index entry apiece; naming the modules
        and how many names each contributes says the same thing, and each name
        is one search away on the page that declares it.
        """
        counts: dict[str, int] = {}
        for kind in ('functions', 'constants', 'classes'):
            for name, value in getattr(module, kind):
                claimed = self.owner(module, name, value)
                if claimed:
                    counts[claimed[0]] = counts.get(claimed[0], 0) + 1
        if not counts:
            return
        writer.heading('Re-exported names', 1)
        writer.paragraph(
            'These names are available from this module and documented on the '
            'module that declares each:'
        )
        for name in sorted(counts):
            writer.line(
                '- :py:mod:`%s` (%d name%s)'
                % (name, counts[name], '' if counts[name] == 1 else 's')
            )
        writer.blank()

    def write_submodules(self, module: PyModule, writer: Writer) -> None:
        """List the modules one level below this one.

        The toctree is hidden and the list is written out beside it.  A
        visible toctree here would put every module of the package into the
        sidebar of every page in the set -- a few thousand entries, rendered
        several thousand times -- and the list says the same thing on the one
        page where it belongs.
        """
        children = module.modules
        if not children:
            return
        writer.heading('Submodules', 1)
        writer.directive('toctree', options={'hidden': '', 'maxdepth': '1'})
        with writer.indent():
            for child in children:
                writer.line(child)
        writer.blank()
        for child in children:
            writer.line('- :doc:`%s <%s>`' % (child, child))
        writer.blank()

    def write_functions(self, module: PyModule, writer: Writer) -> None:
        if not module.functions:
            return
        described = []
        linked = []
        for name, func in module.functions:
            if self.owner(module, name, func):
                continue  # another module declares it; counted as re-exported
            link = self.reference_link(module, name)
            if link:
                linked.append(link)
            else:
                described.append((name, func))
        if not (described or linked):
            return
        writer.heading('Functions', 1)
        if linked:
            writer.paragraph(
                'These entry points wrap an OpenGL command and are described '
                'on its reference page: ' + ', '.join(linked) + '.'
            )
        for _name, func in described:
            writer.directive('py:function', model.python_signature(func))
            with writer.indent():
                for alias in sorted(getattr(func, 'aliases', []) or []):
                    writer.paragraph('Also exported as ``%s``.' % (alias,))
                write_docstring(
                    docstring_lines(func), writer, self.entry_points_for(module)
                )

    def write_classes(self, module: PyModule, writer: Writer) -> None:
        declared = [
            (name, cls)
            for name, cls in module.classes
            if not self.owner(module, name, cls)
        ]
        if not declared:
            return
        writer.heading('Classes', 1)
        for name, cls in declared:
            # Declared under the name the module binds it to, not under
            # ``__name__``: ctypes builds a type per function signature and
            # calls every one of them `CFunctionType`, so the module's own
            # names -- `GLDEBUGPROC` and its neighbours -- are the ones a
            # reader has and the only ones that are distinct.
            bases = ', '.join(base_name(base) for base in cls.bases)
            writer.directive(
                'py:class', '%s(%s)' % (name, bases) if bases else name
            )
            known = self.entry_points_for(module)
            with writer.indent():
                write_docstring(docstring_lines(cls), writer, known)
                for _key, prop in cls.properties:
                    writer.directive(
                        'py:attribute', prop.name, attribute_options(prop)
                    )
                    with writer.indent():
                        write_docstring(docstring_lines(prop), writer, known)
                for _key, func in cls.functions:
                    writer.directive('py:method', model.python_signature(func))
                    with writer.indent():
                        write_docstring(docstring_lines(func), writer, known)

    def write_constants(self, module: PyModule, writer: Writer) -> None:
        declared = [
            (name, constant)
            for name, constant in module.constants
            if not self.owner(module, name, constant)
        ]
        if not declared:
            return
        writer.heading('Constants', 1)
        for name, constant in declared:
            value = constant_value(constant)
            writer.directive(
                'py:data', name, {'value': value} if value else None
            )
            aliases = sorted(getattr(constant, 'aliases', []) or [])
            if aliases:
                with writer.indent():
                    writer.paragraph(
                        'Also exported as %s.'
                        % (', '.join('``%s``' % (a,) for a in aliases),)
                    )

    def write_imports(self, module: PyModule, writer: Writer) -> None:
        """Modules this one imports into its own namespace.

        They are named rather than declared: the module that defines one has
        its own page, and that page is where it is documented.
        """
        names = sorted(
            imported.__name__
            for _key, imported in module.imports
            if getattr(imported, '__name__', None)
        )
        if not names:
            return
        writer.heading('Imported modules', 1)
        writer.paragraph(
            ', '.join(':py:mod:`%s`' % (name,) for name in dict.fromkeys(names))
        )


def report_configuration() -> None:
    """Say so if the configuration is not the one the pages want.

    The variables at the top of this module choose it, and they are read once
    per process.  A process that had already built its entry points before
    importing this keeps what it built, and the pages would then describe
    something other than the Python entry points -- silently, since a compiled
    entry point documents as a name with no arguments and no docstring.
    """
    from OpenGL import _configflags

    if _configflags.USE_ACCELERATE:
        log.warning(
            'PyOpenGL was configured with the accelerators before this module '
            'was imported, so the pages describe the compiled entry points '
            'rather than the Python ones'
        )
    if not _configflags.MODULE_ANNOTATIONS:
        log.warning(
            'MODULE_ANNOTATIONS is off, so nothing says which module declares '
            'each name and every re-export is documented as a declaration'
        )


def package_modules(root: str) -> list[str]:
    """Every importable module under ``root``, the root itself included.

    A package that finds its parts through plugin registries or deferred
    imports -- backends, node types, loaders -- keeps most of itself out of the
    attribute graph, so the names come from the filesystem instead.

    A subpackage that cannot be imported is skipped rather than fatal: a
    Windows-only or toolkit-specific module is absent by circumstance rather
    than by error, and the rest of the package still documents.
    """
    names = [root]
    try:
        package = __import__(root, {}, {}, [root])
    except ImportError as err:
        log.warning('cannot import %s: %s', root, err)
        return []
    path = getattr(package, '__path__', None)
    if not path:
        return names
    for _, name, _ in pkgutil.walk_packages(
        path,
        prefix=root + '.',
        onerror=lambda name: None,
    ):
        if any(fragment in name for fragment in SKIP_FRAGMENTS):
            continue
        if any(
            name == package or name.startswith(package + '.')
            for package in SKIP_PACKAGES
        ):
            continue
        names.append(name)
    return names


def load_entry_points() -> dict[str, dict[str, str]]:
    """Which reference page declares each entry point, per API package.

    Per package, because an entry point can be in several: ``glBindTexture``
    is documented on one page for desktop OpenGL and another for ES 3.x, and
    which one a module page should link to depends on which API that module
    belongs to.
    """
    if not os.path.isfile(ENTRYPOINTS):
        log.info(
            'no reference manifest at %s; entry points are described here '
            'rather than linked to their reference pages',
            ENTRYPOINTS,
        )
        return {}
    with open(ENTRYPOINTS, encoding='utf-8') as fh:
        return json.load(fh).get('entry_points', {})


def api_package(module_name: str) -> str:
    """The API package ``module_name`` belongs to.

    ``OpenGL.GL.ARB.vertex_buffer_object`` is desktop OpenGL's;
    ``OpenGL.GLES3.VERSION.GLES3_3_0`` is ES 3.x's.  Two components, because
    that is how the packages are laid out.
    """
    return '.'.join(module_name.split('.')[:2])


def child_names(name: str, every: Iterable[str]) -> list[str]:
    """The module names one level under ``name``."""
    prefix = name + '.'
    depth = name.count('.') + 1
    return sorted(
        other
        for other in every
        if other.startswith(prefix) and other.count('.') == depth
    )


def write_index(roots: list[str], written: list[str], directory: str) -> None:
    writer = Writer()
    writer.heading('API reference', 0)
    writer.paragraph(
        'A page per module, written from the packages as they are installed. '
        'Every module, class, method, attribute, entry point and constant is '
        'declared here, so each one is a cross-reference target and appears in '
        'the :ref:`index <genindex>`.'
    )
    writer.paragraph(
        'An entry point that wraps an OpenGL command is described on its '
        ':doc:`reference page </reference/index>`; the module page links to it '
        'rather than repeating it.'
    )
    writer.directive('toctree', options={'maxdepth': '1'})
    with writer.indent():
        for root in roots:
            if root in written:
                writer.line(root)
    writer.blank()
    writer.paragraph(
        ':ref:`The module index <modindex>` lists every page of this section.'
    )
    with open(os.path.join(directory, 'index.rst'), 'w', encoding='utf-8') as fh:
        fh.write(writer.render())


def render_projects(
    projects: list[str] | None = None,
    directory: str = OUTPUT_DIRECTORY,
    skip: Iterable[str] = (),
) -> tuple[list[str], list[str]]:
    """Write a page for every module of every project.

    Returns the names written and the names that could not be documented.
    """
    report_configuration()
    os.makedirs(directory, exist_ok=True)
    roots = list(projects or PROJECTS)
    skip = tuple(skip)

    names: list[str] = []
    for root in roots:
        for name in package_modules(root):
            if any(name == prefix or name.startswith(prefix + '.') for prefix in skip):
                continue
            names.append(name)

    # Importing and inspecting comes first for every module, because which
    # page declares a name is a question about all of them at once.
    modules: list[PyModule] = []
    failed: list[str] = []
    for name in names:
        module = PyModule(name)
        try:
            module.inspect()
        except Exception as err:
            log.warning('could not document %s: %s', name, err)
            failed.append(name)
            continue
        modules.append(module)

    # The children a page lists are the ones that got a page: a module that
    # could not be imported here -- a platform's, on another platform -- has
    # none, and naming it in a toctree is a broken link rather than a gap.
    found = {module.name for module in modules}
    for module in modules:
        module.modules = child_names(module.name, found)

    renderer = Renderer(load_entry_points(), claim_owners(modules))
    renderer.documented = {module.name for module in modules}
    rendered: list[str] = []
    for module in modules:
        try:
            page = renderer.render(module)
        except Exception as err:
            log.warning('could not write the page for %s: %s', module.name, err)
            failed.append(module.name)
            continue
        with open(
            os.path.join(directory, '%s.rst' % (module.name,)), 'w', encoding='utf-8'
        ) as fh:
            fh.write(page)
        rendered.append(module.name)

    write_index(roots, rendered, directory)
    return rendered, failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument(
        'projects',
        nargs='*',
        default=None,
        help='packages to document (default: %s)' % (' '.join(PROJECTS),),
    )
    parser.add_argument(
        '--output',
        default=OUTPUT_DIRECTORY,
        help='directory to write the pages into (default: %(default)s)',
    )
    parser.add_argument(
        '--skip',
        action='append',
        default=[],
        metavar='MODULE',
        help=(
            'leave out this module and anything under it; '
            '"--skip OpenGL.raw" halves the page count and the build time'
        ),
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='report every module skipped'
    )
    options = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if options.verbose else logging.INFO)

    rendered, failed = render_projects(
        options.projects or None, options.output, options.skip
    )
    log.info(
        '%d modules documented, %d could not be imported', len(rendered), len(failed)
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
