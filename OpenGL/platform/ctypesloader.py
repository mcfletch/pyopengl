"""ctypes abstraction layer

We keep rewriting functions as the main entry points change,
so let's just localise the changes here...
"""
import ctypes, logging, os, sys
_log = logging.getLogger( 'OpenGL.platform.ctypesloader' )
#_log.setLevel( logging.DEBUG )
ctypes_version = [
    int(x) for x in ctypes.__version__.split('.')
]
from ctypes import util
import OpenGL

DLL_DIRECTORY = os.path.join( os.path.dirname( OpenGL.__file__ ), 'DLLS' )

#: The Windows libraries that are part of the operating system.
#:
#: ``ctypes.util.find_library`` walks ``PATH`` on Windows, and ``PATH`` is not
#: where these live.  ``C:\Windows\System32\opengl32.dll`` is a trampoline to
#: whatever the graphics driver installed, so it is the only correct one --
#: and a conda environment puts ``Library\bin``, which carries a Mesa
#: ``opengl32.dll``, ahead of ``System32`` on ``PATH``.  A program that asked
#: for the driver's GL then got software rendering, with nothing saying so.
#:
#: Handed to the loader bare, these resolve through Windows' own search order,
#: which reaches the system directory before ``PATH``.
#:
#: https://github.com/mcfletch/pyopengl/issues/174
SYSTEM_LIBRARIES = set([
    'opengl32',
    'glu32',
])

#: Where macOS keeps the frameworks this package loads, tried when
#: ``find_library`` answers nothing.
#:
#: Since Big Sur the system frameworks live in the dynamic linker cache and are
#: no longer present as files, so nothing here may check that the path names a
#: file first: ``dlopen`` is what asks the cache, and handing it the path is
#: the only way to find out.  CPython's ``find_library`` learned the same in
#: 3.8.10 and 3.9.1, which covers every interpreter this package supports; the
#: fallback is for the machines where its heuristics still come up empty.
#:
#: https://github.com/mcfletch/pyopengl/issues/55
FRAMEWORK_DIRECTORIES = (
    ['/System/Library/Frameworks'] if sys.platform == 'darwin' else []
)

def loadLibrary( dllType, name, mode = ctypes.RTLD_GLOBAL ):
    """Load a given library by name with the given mode
    
    dllType -- the standard ctypes pointer to a dll type, such as
        ctypes.cdll or ctypes.windll or the underlying ctypes.CDLL or 
        ctypes.WinDLL classes.
    name -- a short module name, e.g. 'GL' or 'GLU'
    mode -- ctypes.RTLD_GLOBAL or ctypes.RTLD_LOCAL,
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
    # If a .so is missing, let's try libs with so version (e.g libGLU.so.9, libGLU.so.8 and so on)
    filenames_to_try.extend(list(reversed([
        base_name + '.%i' % i for i in range(0, 10)
    ])))
    err = None

    for filename in filenames_to_try:
        try:
            result = dllType(filename, mode)
            _log.debug( 'Loaded %s => %s %s', base_name, filename, result)
            return result
        except Exception as current_err:
            err = current_err
    
    _log.info('''Failed to load library ( %r ): %s''', filename, err or 'No filenames available to guess?')

def _loadLibraryWindows(dllType, name, mode):
    """Load a given library for the systems that are not posix

    Windows and macOS both arrive here, and each wants something different
    from ``ctypes.util.find_library``: see :data:`SYSTEM_LIBRARIES` and
    :data:`FRAMEWORK_DIRECTORIES` for what and why.

    Where the first choice does not load -- a library of the wrong
    architecture, a bundled copy an installer dropped -- the rest are tried in
    turn, and the error from the last is raised with the name asked for and
    whatever ``find_library`` answered appended to it.

    returns the ctypes C-module object
    """
    fullName = None
    if name.lower() in SYSTEM_LIBRARIES:
        candidates = [name]
    else:
        try:
            fullName = util.find_library( name )
        except Exception as err:
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
                os.path.join( directory, '%s.framework'%(name,), name )
                for directory in FRAMEWORK_DIRECTORIES
            ])
    err = None
    for candidate in candidates:
        try:
            return dllType( candidate, mode )
        except Exception as current:
            err = current
    err.args += (name,fullName)
    raise err

def buildFunction( functionType, name, dll ):
    """Abstract away the ctypes function-creation operation"""
    return functionType( (name, dll), )
