"""ctypes-based OpenGL wrapper for Python

This is the PyOpenGL 3.x tree, it attempts to provide
a largely compatible API for code written with the
PyOpenGL 2.x series using the ctypes foreign function
interface system.

Configuration Variables:

There are a few configuration variables in this top-level
module.  Applications should be the only code that tweaks
these variables, mid-level libraries should not take it
upon themselves to disable/enable features at this level.
The implication there is that your library code should be
able to work with any of the valid configurations available
with these sets of flags.

Further, once any entry point has been loaded, the variables 
can no longer be updated.  The OpenGL._confligflags module 
imports the variables from this location, and once that 
import occurs the flags should no longer be changed.

    ERROR_CHECKING -- if set to a False value before
        importing any OpenGL.* libraries will completely
        disable error-checking.  This can dramatically
        improve performance, but makes debugging far
        harder.

        This is intended to be turned off *only* in a
        production environment where you *know* that
        your code is entirely free of situations where you
        use exception-handling to handle error conditions,
        i.e. where you are explicitly checking for errors
        everywhere they can occur in your code.

        Default: True

    ERROR_LOGGING -- If True, then wrap array-handler
        functions with  error-logging operations so that all exceptions
        will be reported to log objects in OpenGL.logs, note that
        this means you will get lots of error logging whenever you
        have code that tests by trying something and catching an
        error, this is intended to be turned on only during
        development so that you can see why something is failing.

        Errors are normally logged to the OpenGL.errors logger.

        Only triggers if ERROR_CHECKING is True

        Default: False

    ERROR_ON_COPY -- if set to a True value before
        importing the numpy/lists support modules, will
        cause array operations to raise
        OpenGL.error.CopyError if the operation
        would cause a data-copy in order to make the
        passed data-type match the target data-type.

        This effectively disables all list/tuple array
        support, as they are inherently copy-based.

        This feature allows for optimisation of your
        application.  It should only be enabled during
        testing stages to prevent raising errors on
        recoverable conditions at run-time.

        Note: this feature does not currently work with
            numarray or Numeric arrays.

        Default: False

    CONTEXT_CHECKING -- if set to True, PyOpenGL will wrap
        *every* GL and GLU call with a check to see if there
        is a valid context.  If there is no valid context
        then will throw OpenGL.errors.NoContext.  This is an
        *extremely* slow check and is not enabled by default,
        intended to be enabled in order to track down (wrong)
        code that uses GL/GLU entry points before the context
        has been initialized (something later Linux GLs are
        very picky about).

        Default: False

    STORE_POINTERS -- if set to True, PyOpenGL array operations
        will attempt to store references to pointers which are
        being passed in order to prevent memory-access failures
        if the pointed-to-object goes out of scope.  This
        behaviour is primarily intended to allow temporary arrays
        to be created without causing memory errors, thus it is
        trading off performance for safety.

        To use this flag effectively, you will want to first set
        ERROR_ON_COPY to True and eliminate all cases where you
        are copying arrays.  Copied arrays *will* segfault your
        application deep within the GL if you disable this feature!

        Once you have eliminated all copying of arrays in your
        application, you will further need to be sure that all
        arrays which are passed to the GL are stored for at least
        the time period for which they are active in the GL.  That
        is, you must be sure that your array objects live at least
        until they are no longer bound in the GL.  This is something
        you need to confirm by thinking about your application's
        structure.

        When you are sure your arrays won't cause seg-faults, you
        can set STORE_POINTERS=False in your application and enjoy
        a (slight) speed up.

        Note: this flag is *only* observed when ERROR_ON_COPY == True,
            as a safety measure to prevent pointless segfaults

        Default: True

    WARN_ON_FORMAT_UNAVAILABLE -- If True, generates
        logging-module warn-level events when a FormatHandler
        plugin is not loadable (with traceback).

        Default: False

    FULL_LOGGING -- If True, then wrap functions with
        logging operations which reports each call along with its
        arguments to  the OpenGL.calltrace logger at the INFO
        level.  This is *extremely* slow.  You should *not* enable
        this in production code!

        You will need to have a  logging configuration (e.g.
            logging.basicConfig()
        ) call  in your top-level script to see the results of the
        logging.

        Default: False

    ALLOW_NUMPY_SCALARS -- if True, we will wrap
        all GLint/GLfloat calls conversions with wrappers
        that allow for passing numpy scalar values.

        Note that this is experimental, *not* reliable,
        and very slow!

        Note that byte/char types are not wrapped.

        Default: False

    UNSIGNED_BYTE_IMAGES_AS_STRING -- if True, we will return
        GL_UNSIGNED_BYTE image-data as strings, istead of arrays
        for glReadPixels and glGetTexImage

        Default: True

    FORWARD_COMPATIBLE_ONLY -- only include OpenGL 3.1 compatible
        entry points.  Note that this will generally break most
        PyOpenGL code that hasn't been explicitly made "legacy free"
        via a significant rewrite.

        Default: False

    SIZE_1_ARRAY_UNPACK -- if True, unpack size-1 arrays to be
        scalar values, as done in PyOpenGL 1.5 -> 3.0.0, that is,
        if a glGenList( 1 ) is done, return a uint rather than
        an array of uints.

        Default: True

    USE_ACCELERATE -- if True, attempt to use the OpenGL_accelerate
        package to provide Cython-coded accelerators for core wrapping
        operations.

        Default: True
    
    MODULE_ANNOTATIONS -- if True, attempt to annotate alternates() and 
        constants to track in which module they are defined (only useful 
        for the documentation-generation passes, really).
        
        Default: False
"""
from OpenGL.version import __version__

ERROR_CHECKING = True
ERROR_LOGGING = False
ERROR_ON_COPY = False
ARRAY_SIZE_CHECKING = True
STORE_POINTERS = True
WARN_ON_FORMAT_UNAVAILABLE = False
FORWARD_COMPATIBLE_ONLY = False
SIZE_1_ARRAY_UNPACK = True
USE_ACCELERATE = True
CONTEXT_CHECKING = False

FULL_LOGGING = False
ALLOW_NUMPY_SCALARS = False
UNSIGNED_BYTE_IMAGES_AS_STRING = True
MODULE_ANNOTATIONS = False

# Declarations of plugins provided by PyOpenGL itself
from OpenGL.plugins import PlatformPlugin, FormatHandler
PlatformPlugin( 'nt', 'OpenGL.platform.win32.Win32Platform' )
PlatformPlugin( 'linux2', 'OpenGL.platform.glx.GLXPlatform' )
PlatformPlugin( 'darwin', 'OpenGL.platform.darwin.DarwinPlatform' )
PlatformPlugin( 'posix', 'OpenGL.platform.glx.GLXPlatform' )

FormatHandler( 'none', 'OpenGL.arrays.nones.NoneHandler' )
import sys
if sys.version_info[0] < 3:
    FormatHandler( 'str', 'OpenGL.arrays.strings.StringHandler' )
else:
    FormatHandler( 'bytes', 'OpenGL.arrays.strings.StringHandler' )
FormatHandler( 'list', 'OpenGL.arrays.lists.ListHandler', ['__builtin__.list','__builtin__.tuple'] )
FormatHandler( 'numbers', 'OpenGL.arrays.numbers.NumberHandler' )
FormatHandler(
    'ctypesarray', 'OpenGL.arrays.ctypesarrays.CtypesArrayHandler',
    [
        '_ctypes.ArrayType','_ctypes.PyCArrayType',
    ],
)
FormatHandler(
    'ctypesparameter',
    'OpenGL.arrays.ctypesparameters.CtypesParameterHandler',
)
FormatHandler( 'ctypespointer', 'OpenGL.arrays.ctypespointers.CtypesPointerHandler' )
FormatHandler( 'numpy', 'OpenGL.arrays.numpymodule.NumpyHandler', ['numpy.ndarray'] )
FormatHandler( 'numeric', 'OpenGL.arrays.numeric.NumericHandler', )
