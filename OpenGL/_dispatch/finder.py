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

There is nothing for this to be switched off in favour of: the generated files
are not shipped and the generator does not write them, so these names resolve
here or not at all.

Shadowing files would not have been worth an import hook, and the measurement
is why -- with the friendly modules importing the raw ones eagerly, the module
objects exist either way:

    import OpenGL.GL, warm      58 ms both ways, 62 MB both ways, 309 modules
    import OpenGL.GL, cold     185 ms from files, 166 ms from tables
    the whole raw tree, cold   333 ms from files, 352 ms from tables

What pays is *removing* the 1,278 files, which the definitions being in the
tables is what allows.  A test asserts that what is built here defines exactly
what a file defined, which is what made removing them a decision rather than a
gamble.

Two kinds keep their files either way.  The packages and the private modules
-- ``_types``, ``_errors``, ``_glgets`` -- carry classes and conditionals, so
no table describes them.  And the finder can only be installed once the
extension is loaded, which is the first entry point built, so whatever was
imported to reach that point comes from files: for ``import OpenGL.GL`` that
is GL_1_0 and GL_1_1.
"""

import importlib
import importlib.machinery
import os
import pkgutil
import sys

from OpenGL import _declarations
from OpenGL._declarations import Declaration, resolve_type  # noqa: F401
from OpenGL._dispatch import support

#: One reader, one declaration class, for both routes into the same
#: declarations: see :mod:`OpenGL._declarations`.  Re-exported here because
#: this is where a reader of the import hook looks for them.
__all__ = [
    'RawModuleFinder',
    'Declaration',
    'resolve_type',
    'install',
    'installed',
]

_installed = None


class RawModuleFinder:
    """Finds and builds the generated modules from the dispatch tables.

    A meta-path finder is what it does, not what it inherits: the import
    machinery asks for ``find_spec``, ``create_module`` and ``exec_module`` and
    never for a base class.  Deriving from ``importlib.abc`` would pull in
    ``importlib.resources`` and ``inspect`` -- 15 ms, on every import, for a
    registration this file does not need.
    """

    def __init__(self, extension=None, entry_points=None):
        self._extension = extension
        self._entry_points = entry_points
        self._known = None

    @property
    def _names(self):
        """The generated module names, read on the first import that asks.

        From the tables even where the extension will answer, because the two
        describe the same set and reading an index is cheaper than installing
        the dispatch layer.  Read late rather than in ``__init__`` because this
        object is built during ``import OpenGL``, and a program sets
        ``OpenGL.ERROR_CHECKING`` and its neighbours in the lines after that --
        anything read here would be read before it had been written.
        """
        if self._known is None:
            self._known = frozenset(
                _declarations.data_declarations().module_names()
            )
        return self._known

    def _source(self):
        """The extension where it is the implementation, the tables otherwise.

        Resolved on the first module built rather than at construction: that
        is the first moment the answer can be right, because deciding it
        earlier would settle the configuration before a program has finished
        writing it.
        """
        if self._extension is None:
            extension = _declarations._c_source()
            if extension:
                from OpenGL._dispatch import entry_points

                self._extension, self._entry_points = extension, entry_points
            else:
                self._extension = _declarations.data_declarations()
                self._entry_points = {}
        return self._extension, self._entry_points

    # -- finding ---------------------------------------------------------
    def find_spec(self, name, path=None, target=None):
        # The prefix test first, and without touching _names: this is asked
        # about every import in the process, and reading the index is what
        # imports OpenGL._declarations -- which would ask about itself.
        if not name.startswith('OpenGL.raw.') or name not in self._names:
            return None
        # The origin is the table the definitions come from, which is the
        # honest answer to "where did this module come from" and the only one
        # there is.  has_location stays false: the file is marshalled data
        # rather than the source of anything, so nothing should try to read it
        # as source or count lines in it.
        return importlib.machinery.ModuleSpec(
            name, self, origin=_declarations.table_path(_api_of(name))
        )

    # -- loading ---------------------------------------------------------
    def create_module(self, spec):
        return None  # the default module object is what is wanted

    def exec_module(self, module):
        name = module.__name__
        extension, entry_points = self._source()
        contents = extension.module_contents(name)
        if contents is None:  # pragma: no cover - find_spec filtered on this
            raise ImportError(name)

        namespace = module.__dict__
        # __file__ names the table the definitions were read from, so that a
        # tool asking where they came from gets a useful answer rather than
        # nothing.  It is not read to load anything, and where the package is
        # not a directory on disk there is no path to give and the attribute
        # is left unset -- which is a legitimate thing for a module to be.
        origin = module.__spec__.origin if module.__spec__ else None
        if origin:
            namespace['__file__'] = origin
        namespace['_EXTENSION_NAME'] = contents['extension']

        # A module re-exports the ones it was built on top of, as the file did
        # with ``from ... import *`` -- which takes __all__ where the source
        # defines one, and only falls back to "every public name" where it
        # does not.  The two differ for _types and _glgets, which define it.
        for source in contents['reexports']:
            imported = importlib.import_module(source)
            exported = getattr(imported, '__all__', None)
            if exported is None:
                for key, value in vars(imported).items():
                    if not key.startswith('_'):
                        namespace[key] = value
            else:
                for key in exported:
                    try:
                        namespace[key] = getattr(imported, key)
                    except AttributeError:
                        # ``import *`` raises for an __all__ naming something
                        # absent, and so does this.
                        raise ImportError(
                            'cannot import name %r from %r' % (key, source)
                        ) from None

        from OpenGL.constant import Constant

        for key, value in contents['constants'].items():
            namespace[key] = Constant(key, value)

        api = _api_of(name)
        extension = contents['extension']
        for command, arguments, types in contents['commands']:
            declaration = Declaration(
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
            entry = entry_points.get((api, command))
            if entry is None:
                # An entry point the C does not implement is what it always
                # was, so build it now rather than describe it.
                entry = declaration()
                support.register_ctypes_binding(api, command, entry)
            namespace[command] = entry


def _api_of(name):
    parts = name.split('.')
    return parts[2] if len(parts) > 2 else 'GL'


class _RawDirectoryFinder:
    """A path entry finder for one directory under ``OpenGL/raw``.

    ``pkgutil.iter_modules`` and ``walk_packages`` ask the *path* finder for a
    package's directory what it holds, never the meta-path finder that builds
    the modules -- so with the generated files gone the ordinary
    :class:`FileFinder` reports an empty directory and a walk of
    ``OpenGL.raw.GL.ARB`` yields nothing at all.  Nothing raises: the caller is
    told there are no extensions, which is the wrong answer rather than no
    answer.

    So this stands in front of the real finder for those directories, adds the
    names the tables describe, and defers everything else -- finding and
    loading included -- to the finder that would have handled the directory.
    """

    def __init__(self, path, delegate):
        self.path = path
        self._delegate = delegate

    # -- the import protocol, which is entirely the real finder's job --------
    def find_spec(self, name, target=None):
        return self._delegate.find_spec(name, target)

    def invalidate_caches(self):
        self._delegate.invalidate_caches()

    # -- what this exists for -----------------------------------------------
    def iter_modules(self, prefix=''):
        seen = set()
        for name, ispkg in pkgutil.iter_importer_modules(self._delegate, ''):
            seen.add(name)
            yield prefix + name, ispkg
        for name in sorted(self._generated()):
            if name not in seen:
                yield prefix + name, False

    def _generated(self):
        """The leaf names the tables describe for this directory."""
        installed = _installed
        if installed is None:
            return ()
        package = _package_for_directory(self.path)
        if package is None:
            return ()
        prefix = package + '.'
        return {
            name[len(prefix) :]
            for name in installed._names
            if name.startswith(prefix) and '.' not in name[len(prefix) :]
        }


def _package_for_directory(path):
    """``OpenGL.raw.GL.ARB`` for the directory that package lives in."""
    root = _raw_directory()
    if not root:
        return None
    relative = os.path.relpath(os.path.abspath(path), root)
    if relative.startswith(os.pardir):
        return None
    parts = [] if relative == os.curdir else relative.split(os.sep)
    return '.'.join(['OpenGL', 'raw'] + parts)


#: The ``OpenGL/raw`` directory, or ``''`` where the package is not on disk.
#: Resolved once: the hook below is asked about every path entry in the
#: process, so the question it answers has to be cheap.
_raw_root = None


def _raw_directory():
    global _raw_root
    if _raw_root is None:
        import OpenGL

        paths = getattr(OpenGL, '__path__', None)
        candidate = paths[0] if paths and len(paths) == 1 else ''
        directory = os.path.join(candidate, 'raw') if candidate else ''
        _raw_root = os.path.abspath(directory) if os.path.isdir(directory) else ''
    return _raw_root


def _path_hook(path):
    """Claim the directories under ``OpenGL/raw``, decline everything else."""
    root = _raw_directory()
    if not root or not isinstance(path, str):
        raise ImportError(path)
    resolved = os.path.abspath(path)
    if resolved != root and not resolved.startswith(root + os.sep):
        raise ImportError(path)
    return _RawDirectoryFinder(resolved, _default_path_finder(resolved))


def _default_path_finder(path):
    """The finder that would have handled this directory without the hook."""
    for hook in sys.path_hooks:
        if hook is _path_hook:
            continue
        try:
            return hook(path)
        except ImportError:
            continue
    raise ImportError(path)  # pragma: no cover - FileFinder always claims a dir


def installed():
    """The finder answering for the generated modules, or ``None``."""
    return _installed


def install(extension=None, entry_points=None):
    """Put the finder ahead of the path finder.

    Ahead of it because there are no files for it to be behind: the generated
    modules are not shipped, and this is what answers for their names.
    """
    global _installed
    if _installed is not None:
        return _installed
    _installed = RawModuleFinder(extension, entry_points)
    sys.meta_path.insert(0, _installed)
    if _path_hook not in sys.path_hooks:
        sys.path_hooks.insert(0, _path_hook)
        # Directories already resolved carry the finder from before the hook.
        for key in [k for k in sys.path_importer_cache if _claims(k)]:
            del sys.path_importer_cache[key]
    return _installed


def _claims(path):
    try:
        _path_hook(path)
    except ImportError:
        return False
    return True


def uninstall():
    """Go back to importing the files.  For the tests that compare them."""
    global _installed
    if _installed is not None:
        try:
            sys.meta_path.remove(_installed)
        except ValueError:
            pass
        _installed = None
    if _path_hook in sys.path_hooks:
        sys.path_hooks.remove(_path_hook)
        for key in [k for k in sys.path_importer_cache if _claims(k)]:
            del sys.path_importer_cache[key]
