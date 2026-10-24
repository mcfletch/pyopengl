"""Build the generated ``OpenGL.raw`` modules instead of importing files.

Every module under ``OpenGL/raw`` is generated: constants, entry-point
declarations and re-exports.  All hand-written code lives in the friendly
modules above them.  Under the C dispatch layer the entry points come from the
extension instead of from those declarations, so a module file would only add
a compile and an exec.

Client code and PyOpenGL's friendly modules still import these module names.
This finder builds the modules on demand from the same tables the C code is
generated from.

The finder cannot be switched off.  The generated files are not shipped and
the generator does not write them, so these names resolve here or not at all.

Building modules from tables is not faster than importing files.  The friendly
modules import the raw ones eagerly, so the module objects exist either way:

    import OpenGL.GL, warm      58 ms both ways, 62 MB both ways, 309 modules
    import OpenGL.GL, cold     185 ms from files, 166 ms from tables
    the whole raw tree, cold   333 ms from files, 352 ms from tables

The gain is that the 1,278 files are not shipped, since the tables hold the
same definitions.  A test asserts that each module built here defines the same
names as the file it replaces.

Two kinds of module still have files.  The packages and the private modules
(``_types``, ``_errors``, ``_glgets``) contain classes and conditionals, so no
table describes them.  The finder is installed only once the extension is
loaded, at the first entry point built, so modules imported before that come
from files.  For ``import OpenGL.GL`` those are GL_1_0 and GL_1_1.
"""

import importlib
import importlib.machinery
import os
import pkgutil
import sys

from OpenGL import _declarations
from OpenGL._declarations import Declaration, resolve_type
from OpenGL._dispatch import support

#: The declaration reader and class are shared with the other users of the
#: declarations; see :mod:`OpenGL._declarations`.  They are re-exported here
#: beside the import hook that uses them.
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

    The class implements the meta-path finder protocol without a base class.
    The import machinery calls ``find_spec``, ``create_module`` and
    ``exec_module`` and does not check the type.  Deriving from
    ``importlib.abc`` would import ``importlib.resources`` and ``inspect``,
    which adds 15 ms to every ``import OpenGL``.
    """

    def __init__(self, extension=None, entry_points=None):
        self._extension = extension
        self._entry_points = entry_points
        self._known = None

    @property
    def _names(self):
        """The generated module names, read on the first import needing them.

        Read from the tables even where the extension supplies the modules.
        Both describe the same set, and reading an index is cheaper than
        installing the dispatch layer.  Read on first use instead of in
        ``__init__``, because this object is built during ``import OpenGL``.
        A program sets ``OpenGL.ERROR_CHECKING`` and the related flags after
        that import, and reading earlier would see them unset.
        """
        if self._known is None:
            self._known = frozenset(
                _declarations.data_declarations().module_names()
            )
        return self._known

    def _source(self):
        """Return the extension if it is the implementation, else the tables.

        Resolved when the first module is built instead of at construction.
        Deciding earlier would read the configuration before a program has
        set it.
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
        # Test the prefix first, without touching _names.  This runs for every
        # import in the process.  Reading the index imports
        # OpenGL._declarations, which would recurse into this finder.
        if not name.startswith('OpenGL.raw.') or name not in self._names:
            return None
        # The origin is the table the definitions come from.  has_location
        # stays false: the table is marshalled data, so tools must not read it
        # as source or count lines in it.
        return importlib.machinery.ModuleSpec(
            name, self, origin=_declarations.table_path(_api_of(name))
        )

    # -- loading ---------------------------------------------------------
    def create_module(self, spec):
        return None  # use the default module object

    def exec_module(self, module):
        name = module.__name__
        extension, entry_points = self._source()
        contents = extension.module_contents(name)
        if contents is None:  # pragma: no cover - find_spec filtered on this
            raise ImportError(name)

        namespace = module.__dict__
        # __file__ names the table the definitions were read from, so tools
        # that report a module's location get a useful path.  Nothing loads
        # from it.  Where the package is not a directory on disk there is no
        # path, and the attribute is left unset, which is valid for a module.
        origin = module.__spec__.origin if module.__spec__ else None
        if origin:
            namespace['__file__'] = origin
        namespace['_EXTENSION_NAME'] = contents['extension']

        # A module re-exports the modules it builds on, as the file did with
        # ``from ... import *``.  That uses __all__ where the source defines
        # one, and every public name otherwise.  The two differ for _types and
        # _glgets, which define __all__.
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

        from OpenGL.constant import declared

        for key, value in contents['constants'].items():
            # Given the module name explicitly, as with register_module below,
            # so a constant reports the same module whichever loader filled
            # the namespace.
            namespace[key] = declared(key, value, name)

        api = _api_of(name)
        extension = contents['extension']
        for command, arguments, types in contents['commands']:
            declaration = Declaration(
                api, command, extension, name, arguments, types
            )
            # A derived function whose arity differs from the entry point's
            # demotes to the ctypes binding.  Registering a factory for the
            # binding, instead of building it, keeps the import cost to
            # defining the names.
            support.register_ctypes_factory(api, command, declaration)
            # The value of ``proc.__module__``.  Module files recorded it in
            # createFunction, and it must be the same however the module was
            # filled.
            support.register_module(api, command, name)
            entry = entry_points.get((api, command))
            if entry is None:
                # The C layer does not implement this entry point, so build
                # the ctypes binding now.
                entry = declaration()
                support.register_ctypes_binding(api, command, entry)
            namespace[command] = entry


def _api_of(name):
    parts = name.split('.')
    return parts[2] if len(parts) > 2 else 'GL'


class _RawDirectoryFinder:
    """A path entry finder for one directory under ``OpenGL/raw``.

    ``pkgutil.iter_modules`` and ``walk_packages`` list a package's contents
    through the path finder for its directory, not through the meta-path
    finder that builds the modules.  Without the generated files, the standard
    :class:`FileFinder` reports an empty directory, and a walk of
    ``OpenGL.raw.GL.ARB`` yields nothing.  No error is raised, so the caller
    sees no extensions.

    This finder wraps the standard finder for those directories.  It adds the
    names the tables describe, and passes finding and loading to the wrapped
    finder.
    """

    def __init__(self, path, delegate):
        self.path = path
        self._delegate = delegate

    # -- the import protocol, handled by the wrapped finder ------------------
    def find_spec(self, name, target=None):
        return self._delegate.find_spec(name, target)

    def invalidate_caches(self):
        self._delegate.invalidate_caches()

    # -- listing the generated modules ---------------------------------------
    def iter_modules(self, prefix=''):
        seen = set()
        for name, ispkg in pkgutil.iter_importer_modules(self._delegate, ''):
            seen.add(name)
            yield prefix + name, ispkg
        for name in sorted(self._generated()):
            if name not in seen:
                yield prefix + name, False

    def _generated(self):
        """Return the module names the tables list for this directory."""
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
    """Return a directory's package name, such as ``OpenGL.raw.GL.ARB``."""
    root = _raw_directory()
    if not root:
        return None
    relative = os.path.relpath(os.path.abspath(path), root)
    if relative.startswith(os.pardir):
        return None
    parts = [] if relative == os.curdir else relative.split(os.sep)
    return '.'.join(['OpenGL', 'raw'] + parts)


#: The ``OpenGL/raw`` directory, or ``''`` where the package is not on disk.
#: Resolved once, because the hook below runs for every path entry in the
#: process and must be cheap.
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
    """Return the finder that handles this directory without the hook."""
    for hook in sys.path_hooks:
        if hook is _path_hook:
            continue
        try:
            return hook(path)
        except ImportError:
            continue
    raise ImportError(path)  # pragma: no cover - FileFinder always claims a dir


def installed():
    """Return the finder for the generated modules, or ``None``."""
    return _installed


def install(extension=None, entry_points=None):
    """Install the finder ahead of the path finder and return it.

    The generated modules are not shipped as files, so this finder goes first
    and supplies their names.
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
    """Remove the finder and path hook, for tests that compare with files."""
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
