"""ctypes abstraction layer

Library loading and function creation through ctypes, kept in one module so
changes to the ctypes entry points are made in one place.
"""
import ctypes, logging, os, posixpath, sys
_log = logging.getLogger( 'OpenGL.platform.ctypesloader' )
#_log.setLevel( logging.DEBUG )
from ctypes import util
import OpenGL

def _bundled_dll_directory( ):
    """The directory holding the prebuilt Windows freeglut and GLE libraries

    The libraries are a separate distribution, ``PyOpenGL-glut-binaries``,
    installed on Windows with ``pip install PyOpenGL[glut]``.  Linux and macOS
    installs do not download six freeglut builds they cannot load.  Security
    scanners that flag vendored binaries flag only the package GLUT users
    install.

    Without that package the result is ``OpenGL/DLLS``.  PyOpenGL no longer
    ships that directory, so on most machines it does not exist.  It still
    exists in an installation upgraded in place over a pre-4.0 release, and in
    frozen applications packaged with it, so those keep GLUT.

    A ``pyopengl_glut_binaries`` too old to define ``DLL_DIRECTORY`` raises
    ``ImportError`` from the ``from`` clause and is treated as absent.

    This function chooses only the directory.  :func:`_loadLibraryWindows`
    decides which files to load from it, and prefers a library the system
    provides.

    See ``plans/BUNDLED-DLLS.md``.
    """
    try:
        from pyopengl_glut_binaries import DLL_DIRECTORY as directory
    except ImportError:
        return os.path.join( os.path.dirname( OpenGL.__file__ ), 'DLLS' )
    return directory


DLL_DIRECTORY = _bundled_dll_directory( )


def _bundled_dll_destination( ):
    """The path inside a frozen application for the bundled DLL directory

    A freezer collects the files from :data:`DLL_DIRECTORY`.  It must write
    them where the frozen application's loader will look, which is the same
    lookup run inside the bundle.  Both possible directories are a package
    directory with ``DLLS`` under it (``pyopengl_glut_binaries/DLLS`` or
    ``OpenGL/DLLS``).  The loader finds the package by its ``__file__``, so
    the bundle must reproduce the last two path segments.  Taking the segments
    from the path, rather than naming either package, still works if the
    package is renamed.

    Writing the files to the other directory produces an application that
    contains the libraries but cannot find them.  The caller is
    ``OpenGL/__pyinstaller/hook-OpenGL.py``.
    """
    parent, leaf = os.path.split( DLL_DIRECTORY )
    return os.path.join( os.path.basename( parent ), leaf )

#: The Windows libraries that are part of the operating system.
#:
#: ``ctypes.util.find_library`` searches ``PATH`` on Windows, but these
#: libraries are in the system directory.  ``C:\Windows\System32\opengl32.dll``
#: forwards to the graphics driver's implementation, so it is the correct
#: copy.  A conda environment puts ``Library\bin``, which contains a Mesa
#: ``opengl32.dll``, ahead of ``System32`` on ``PATH``.  Through
#: ``find_library``, a program would silently get Mesa's software rendering.
#:
#: Passed to the loader without a path, these names resolve through Windows'
#: search order, which checks the system directory before ``PATH``.  A copy
#: placed beside the interpreter still comes first; see
#: :func:`beside_the_interpreter`.
#:
#: https://github.com/mcfletch/pyopengl/issues/174
SYSTEM_LIBRARIES = set([
    'opengl32',
    'glu32',
])


def beside_the_interpreter( name ):
    """``name``.dll in the directory the running executable is in, or None.

    A machine with no graphics driver gets OpenGL from a DLL placed next to
    the executable.  Mesa's Windows build is distributed for this, and CI
    runners, headless servers and virtual desktops use it.  Windows' search
    order also checks the application directory before the system directory.
    Returning the full path keeps that order whatever search flags reach
    ``LoadLibraryEx``.

    :data:`SYSTEM_LIBRARIES` handles a different case.  A library on ``PATH``
    arrives as a side effect of another install.  A library next to the
    interpreter was placed there on purpose.
    """
    executable = getattr( sys, 'executable', None )
    if not executable:
        return None
    candidate = os.path.join( os.path.dirname( executable ), name + '.dll' )
    if os.path.isfile( candidate ):
        return candidate
    return None


#: The macOS directories holding the frameworks this package loads, tried when
#: ``find_library`` returns None.
#:
#: From Big Sur on, the system frameworks are in the dynamic linker cache and
#: are not present as files.  The path must not be checked for a file first,
#: because only ``dlopen`` searches the cache.  CPython's ``find_library``
#: handles the cache from 3.8.10 and 3.9.1, which covers every supported
#: interpreter.  This fallback serves machines where its search still fails.
#:
#: https://github.com/mcfletch/pyopengl/issues/55
FRAMEWORK_DIRECTORIES = (
    ['/System/Library/Frameworks'] if sys.platform == 'darwin' else []
)

def loadLibrary( dllType, name, mode = ctypes.RTLD_GLOBAL ):
    """Load a given library by name with the given mode
    
    dllType - the standard ctypes pointer to a dll type, such as
        ctypes.cdll or ctypes.windll or the underlying ctypes.CDLL or
        ctypes.WinDLL classes.
    name - a short module name, e.g. 'GL' or 'GLU'
    mode - ctypes.RTLD_GLOBAL or ctypes.RTLD_LOCAL,
        controls whether the module resolves names via other
        modules already loaded into this process.  GL modules
        generally need to be loaded with GLOBAL flags
    
    returns the ctypes C-module object
    """
    if isinstance( dllType, ctypes.LibraryLoader ):
        dllType = dllType._dlltype
    if sys.platform.startswith('linux'):
        return _loadLibraryPosix(dllType, name, mode)
    else:
        return _loadLibraryWindows(dllType, name, mode)


def _loadLibraryPosix(dllType, name, mode):
    """Load a given library for posix systems

    The problem with util.find_library is that it does not respect linker runtime variables like
    LD_LIBRARY_PATH.

    Also we cannot rely on libGLU.so to be available, for example. Most of Linux distributions will
    ship only libGLU.so.1 by default. Files ending with .so are normally used when compiling and are
    provided by dev packages.

    returns the ctypes C-module object
    """
    prefix = 'lib'
    suffix = '.so'
    base_name = prefix + name + suffix
    
    filenames_to_try = [base_name]
    # If the unversioned .so is missing, try versioned names (libGLU.so.9, libGLU.so.8 and so on)
    filenames_to_try.extend(list(reversed([
        base_name + '.%i' % i for i in range(0, 10)
    ])))
    err = None

    for filename in filenames_to_try:
        try:
            result = dllType(filename, mode)
            _log.debug( 'Loaded %s => %s %s', base_name, filename, result)
            return result
        except OSError as current_err:
            err = current_err
    
    _log.info('''Failed to load library ( %r ): %s''', filename, err or 'No filenames available to guess?')

def _loadLibraryWindows(dllType, name, mode):
    """Load a given library for the systems that are not posix

    Windows and macOS both use this function, and each needs different
    handling around ``ctypes.util.find_library``.  See
    :data:`SYSTEM_LIBRARIES` and :data:`FRAMEWORK_DIRECTORIES`.  A library the
    operating system provides is looked for beside the interpreter before the
    system search; see :func:`beside_the_interpreter`.

    If the first candidate does not load (for example, a library of the wrong
    architecture), the rest are tried in turn.  The last error is raised, with
    the requested name and the ``find_library`` result appended to its args.

    returns the ctypes C-module object
    """
    fullName = None
    if name.lower() in SYSTEM_LIBRARIES:
        candidates = [
            path for path in [beside_the_interpreter( name )] if path
        ]
        candidates.append( name )
    else:
        try:
            fullName = util.find_library( name )
        except Exception as err:  # noqa: BLE001 find_library runs the platform's own tools, whose failures are not a documented set
            _log.info( '''Failed on util.find_library( %r ): %s''', name, err )
            # Should the call fail, we just try to load the base filename...
        if fullName is not None:
            candidates = [fullName]
        else:
            candidates = []
            bundled = os.path.join( DLL_DIRECTORY, name + '.dll' )
            if os.path.isfile( bundled ):
                candidates.append( bundled )
            candidates.append( name )
            candidates.extend([
                # posixpath rather than os.path: a framework path is a macOS
                # path and always uses slashes.  This function also runs on
                # Windows, where os.path.join would use backslashes.
                posixpath.join( directory, '%s.framework'%(name,), name )
                for directory in FRAMEWORK_DIRECTORIES
            ])
    err = None
    for candidate in candidates:
        try:
            return dllType( candidate, mode )
        except OSError as current:
            err = current
    err.args += (name,fullName)
    raise err

def buildFunction( functionType, name, dll ):
    """Abstract away the ctypes function-creation operation"""
    return functionType( (name, dll), )
