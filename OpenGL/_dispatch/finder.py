"""Build the generated ``OpenGL.raw`` modules instead of importing files.

Every module under ``OpenGL/raw`` is purely generated: constants, entry-point
declarations and re-exports, with no hand-written material anywhere -- the
hand-written sections all live in the friendly modules above them.  Under the
C dispatch layer the entry points come from the extension rather than from
those declarations, so what the file adds is a compile and an exec, whether or
not anything looks at what it produced.

The layer has stopped being a layer.  What it still is, is a set of names that
clients import and that PyOpenGL's own friendly modules import from, so the
names go on resolving -- built from the same tables the C is generated from,
on demand.

``PYOPENGL_VIRTUAL_MODULES=1`` uses it.  It is off by default, and the
measurement is why: with the friendly modules importing the raw ones eagerly,
the module objects exist either way, so nothing is saved at run time --

    import OpenGL.GL, warm      58 ms both ways, 62 MB both ways, 309 modules
    import OpenGL.GL, cold     185 ms from files, 166 ms from tables
    the whole raw tree, cold   333 ms from files, 352 ms from tables

A 10% cold-start saving on one import and a loss on another is not a reason to
put an import hook in everyone's process.  What this is for is the step after:
with the definitions in the tables, the 1,278 files become removable, and it
is removing them -- not shadowing them -- that pays.  The files are still
shipped, and a test asserts that what is built here defines exactly what they
define, which is what makes removing them a decision rather than a gamble.

Two kinds keep their files either way.  The packages and the private modules
-- ``_types``, ``_errors``, ``_glgets`` -- carry classes and conditionals, so
no table describes them.  And the finder can only be installed once the
extension is loaded, which is the first entry point built, so whatever was
imported to reach that point comes from files: for ``import OpenGL.GL`` that
is GL_1_0 and GL_1_1.
"""

import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys

from OpenGL._configflags import VIRTUAL_MODULES
from OpenGL._dispatch import support

__all__ = ['RawModuleFinder', 'install']

_installed = None


class RawModuleFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Finds and builds the generated modules from the dispatch tables."""

    def __init__(self, extension, entry_points):
        self._extension = extension
        self._entry_points = entry_points
        self._names = frozenset(extension.module_names())

    # -- finding ---------------------------------------------------------
    def find_spec(self, name, path=None, target=None):
        if name not in self._names:
            return None
        return importlib.machinery.ModuleSpec(name, self, origin='<generated>')

    # -- loading ---------------------------------------------------------
    def create_module(self, spec):
        return None  # the default module object is what is wanted

    def exec_module(self, module):
        name = module.__name__
        contents = self._extension.module_contents(name)
        if contents is None:  # pragma: no cover - find_spec filtered on this
            raise ImportError(name)

        namespace = module.__dict__
        # __file__ is set to the file this stands in for, so that a tool
        # asking where a definition came from gets a useful answer rather than
        # nothing.  It is not read to load anything.
        origin = _file_for(name)
        if origin:
            namespace['__file__'] = origin
        namespace['_EXTENSION_NAME'] = contents['extension']

        # A module re-exports the ones it was built on top of, as the file did
        # with ``from ... import *``.
        for source in contents['reexports']:
            imported = importlib.import_module(source)
            for key, value in vars(imported).items():
                if not key.startswith('_'):
                    namespace[key] = value

        from OpenGL.constant import Constant

        for key, value in contents['constants'].items():
            namespace[key] = Constant(key, value)

        api = _api_of(name)
        extension = contents['extension']
        for command, arguments, types in contents['commands']:
            declaration = _Declaration(
                api, command, extension, name, arguments, types
            )
            # A derived function whose arity differs from the entry point's
            # demotes to the ctypes binding, and running the declaration used
            # to be what recorded it.  Registering how to build one, rather
            # than building it, keeps the import to what it was: nothing but
            # the names.
            support.register_ctypes_factory(api, command, declaration)
            # What ``proc.__module__`` answers.  The file recorded it on its
            # way through createFunction, and a name that reports where it was
            # declared should not depend on how the module was filled.
            support.register_module(api, command, name)
            entry = self._entry_points.get((api, command))
            if entry is None:
                # An entry point the C does not implement is what it always
                # was, so build it now rather than describe it.
                entry = declaration()
                support.register_ctypes_binding(api, command, entry)
            namespace[command] = entry


class _Declaration:
    """What the file's ``@_p.types(...) def glFoo(...)`` said.

    Held as the text it was written in and resolved on the first demotion that
    asks, because most entry points never see one.
    """

    __slots__ = ('_arguments', '_types', 'api', 'extension', 'module', 'name')

    def __init__(self, api, name, extension, module, arguments, types):
        self.api = api
        self.name = name
        self.extension = extension
        self.module = module
        self._arguments = arguments
        self._types = types

    def __call__(self):
        """The ctypes binding the declaration would have produced."""
        # ctypes and arrays are named by the type expressions, platform
        # builds the binding.
        import ctypes

        from OpenGL import arrays, platform

        _cs = importlib.import_module('OpenGL.raw.%s._types' % (self.api,))
        namespace = {'ctypes': ctypes, 'arrays': arrays, '_cs': _cs}
        # The text was written by the generator out of the shipped tree, and
        # the namespace offers it three names; it is our own source arriving
        # by a longer road than usual.
        types = [eval(text, namespace) for text in self._types.split(',')]
        errors = importlib.import_module('OpenGL.raw.%s._errors' % (self.api,))

        def declaration(*arguments):
            """Stands where the generated ``def glFoo(a, b): pass`` stood."""

        declaration.__name__ = self.name
        declaration = platform.types(types[0], *types[1:])(declaration)
        # types() reads the names off the code object, and this one has none
        # of its own -- the names are the declaration's, so state them.
        argument_names = tuple(
            name for name in self._arguments.split(',') if name
        )
        # nullFunction rather than createFunction: createFunction hands back
        # the C entry point where there is one, and what a demotion wants is
        # the thing underneath it.
        return platform.nullFunction(
            self.name,
            getattr(platform.PLATFORM, self.api, None) or platform.PLATFORM.GL,
            resultType=types[0],
            argTypes=tuple(types[1:]),
            doc=None,
            argNames=argument_names,
            extension=self.extension,
            module=self.module,
            error_checker=errors._error_checker,
        )


def _api_of(name):
    parts = name.split('.')
    return parts[2] if len(parts) > 2 else 'GL'


def _file_for(name):
    """The file this module stands in for, if it is still shipped."""
    import OpenGL

    root = os.path.dirname(os.path.dirname(os.path.abspath(OpenGL.__file__)))
    path = os.path.join(root, *name.split('.')) + '.py'
    return path if os.path.exists(path) else ''


def install(extension, entry_points):
    """Put the finder ahead of the path finder.

    Ahead, because the files are still there: what decides which is used is
    which finder answers first, and that keeps the two comparable.
    """
    global _installed
    if _installed is not None or not VIRTUAL_MODULES:
        return _installed
    _installed = RawModuleFinder(extension, entry_points)
    sys.meta_path.insert(0, _installed)
    return _installed


def uninstall():
    """Go back to importing the files.  For the tests that compare them."""
    global _installed
    if _installed is not None:
        try:
            sys.meta_path.remove(_installed)
        except ValueError:
            pass
        _installed = None
