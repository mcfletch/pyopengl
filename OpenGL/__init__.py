"""ctypes-based OpenGL wrapper for Python

PyOpenGL 3.x and later call OpenGL through the ctypes foreign function
interface.  The API stays largely compatible with code written for the
PyOpenGL 2.x series.

Configuration Variables:

This top-level module holds a few configuration variables.  Only the
application should set them.  A library should not enable or disable
features at this level, and library code should work with any valid
combination of these flags.

The flags are read once, when the first entry point is loaded.  The
OpenGL._configflags module copies them from this module at that point,
and later changes have no effect.

    ERROR_CHECKING - if set to a False value before any OpenGL.*
        module is imported, error checking is disabled completely.
        This can greatly improve performance, but makes debugging
        much harder.

        Turn it off *only* in a production environment where your
        code never uses exception handling for error conditions,
        i.e. where it explicitly checks for errors everywhere they
        can occur.

        Default: True

    ERROR_LOGGING - if True, array-handler functions are wrapped
        with error logging, so every exception is reported to a
        logger in OpenGL.logs.  Code that tests by trying something
        and catching the error then logs a lot.  Turn it on during
        development to see why something is failing.

        Errors are normally logged to the OpenGL.errors logger.

        Only applies if ERROR_CHECKING is True.

        Default: False

    ERROR_ON_COPY - if set to a True value before the numpy/lists
        support modules are imported, an array operation raises
        OpenGL.error.CopyError when it would have to copy the data
        to match the target data type.

        This disables list and tuple array support, since lists and
        tuples are always copied.

        The flag applies to array *data*.  A per-frame vertex or
        pixel copy costs speed, and its temporary can be freed while
        the driver still holds the pointer.  String parameters (a
        uniform or attribute name, a debug label, GLSL source) are
        still accepted as str and encoded.  That copy happens once,
        the driver reads it before the call returns, and a str
        cannot be passed any other way.

        Use this flag to find copies while optimising an
        application.  Enable it only during testing, so that
        recoverable conditions do not raise errors at run time.

        Default: False

    ERROR_DEBUG_OUTPUT - if True, a context offering GL_KHR_debug
        reports errors through the driver's debug callback instead
        of a glGetError after every call.  The callback runs during
        the failing call, so the check on the normal path is a flag
        read.  Both modes raise the same GLError from the same call.

        With the flag off, error checking uses the glGetError round
        trip.  Turn it off if the program installs its own
        GL_KHR_debug callback, or if the driver should not be put
        into synchronous debug output.  PyOpenGL never replaces an
        existing callback.

        OpenGL.dispatch.error_checking_mode() reports which
        mechanism a context uses.

        Default: True

    CONTEXT_CHECKING - if set to True, PyOpenGL wraps *every* GL
        and GLU call with a check for a valid context, and raises
        OpenGL.errors.NoContext when there is none.  The check is
        *extremely* slow and is off by default.  Use it to find code
        that calls GL/GLU entry points before the context has been
        initialized (later Linux GL implementations reject this).

        The check covers GL and GLU only.  EGL, GLX and WGL calls
        create and manage the display, the config and the context,
        so they run before any GL context exists.  Their errors are
        checked whether or not a context is current.

        Default: False

        With the flag off, the result of a call made *after* the
        context is gone depends on the platform.  A cleanup handler
        that deletes GL objects is the common case:

        - On Linux, libGL returns zero from glGetError when no
          context is current, so the call is silent and the handler
          finishes.
        - On Windows, opengl32 reports GL_INVALID_OPERATION for the
          same call, so ERROR_CHECKING raises a GLError.  A handler
          that must run to the end there should delete its objects
          while the context is still current, or catch GLError
          around the calls that may follow it.

        PyOpenGL keeps this difference.  Hiding it would need a
        context check on every call, which is what this flag does
        and what it costs.  The C and ctypes dispatch
        implementations behave the same way on each platform.

    ARRAY_SIZE_CHECKING - if True, an output array passed in by the
        caller is compared with the amount the call will write into
        it, before the driver receives the pointer.

        Only sizes derived from a count argument are checked, since
        the driver writes exactly that many.  A fixed size or a
        pname table lookup is only an upper bound, so passing a
        smaller array for a pname that returns one value is not an
        error.

        The check prevents heap overruns.  glGenTextures(1024, a)
        with a sixteen-byte array writes 4096 bytes into it.  The
        bytes past the end belong to another live allocation, so the
        damage shows up in unrelated code.

        Input arrays are checked the same way.  An input with a
        fixed size must hold exactly that many elements: glVertex3dv
        takes three.  An input whose length comes from a count must
        hold at least that many items.  glViewportArrayv(first,
        count, v) reads four floats per viewport, so v needs
        count * 4 of them, and a longer array is accepted.  With a
        shorter one the driver would read past its end.

        Turning the check off removes these guards and saves a few
        array attribute reads per call.  It applies only to arrays
        the caller passes in.

        String arrays are checked whatever this flag says.  In
        glTransformFeedbackVaryings(program, count, varyings, mode),
        varyings must hold at least count strings, and None with a
        positive count is refused instead of being read from address
        zero.  PyOpenGL builds the pointer array from the sequence
        and sizes it by the sequence's length, so a larger count
        would read past the end of that buffer.  A GLchar *const *
        built by the caller is passed unchecked, because PyOpenGL
        does not have its length.

        Default: True

    STORE_POINTERS - if set to True, PyOpenGL array operations
        keep references to the arrays whose pointers they pass, so
        the memory stays valid if the caller's object goes out of
        scope.  Programs can then pass temporary arrays without
        memory errors, at some cost in speed.

        To use this flag, first set ERROR_ON_COPY to True and remove
        every array copy from your application.  Copied arrays *will*
        segfault your application deep within the GL if you disable
        this feature!

        Next, make sure every array passed to the GL lives at least
        as long as the GL uses it, i.e. until it is no longer bound
        in the GL.  That depends on your application's structure.

        Once your arrays cannot cause segfaults, set
        STORE_POINTERS=False in your application for a small speed
        up.

        Note: this flag is *only* observed when ERROR_ON_COPY == True,
            so that copied arrays cannot cause segfaults.

        Default: True

    WARN_ON_FORMAT_UNAVAILABLE - if True, logs a warning (with
        traceback) through the logging module when a FormatHandler
        plugin cannot be loaded.

        Default: False

    FULL_LOGGING - if True, functions are wrapped so that each call
        and its arguments are logged to the OpenGL.calltrace logger
        at INFO level.  This is *extremely* slow.  Do *not* enable it
        in production code.

        The top-level script needs a logging configuration (e.g. a
        call to logging.basicConfig()) to show the output.

        Default: False

    ALLOW_NUMPY_SCALARS - no effect from 4.0; the flag is still
        readable, so setting it is not an error.

        A numpy integer scalar is accepted wherever an integer is
        expected, whatever this flag says, because ctypes converts it
        through __index__.  A value returned by one call can be
        passed straight to the next:

            textures = glGenTextures(2)
            glBindTexture(GL_TEXTURE_2D, textures[0])

        Before 4.0 the flag also enabled a retry through int().  That
        retry accepted a numpy *float* where an integer was expected
        and truncated it silently, and 4.0 removed it.

    UNSIGNED_BYTE_IMAGES_AS_STRING - if True, glReadPixels and
        glGetTexImage return GL_UNSIGNED_BYTE image data as strings
        instead of arrays.

        Default: True

    FORWARD_COMPATIBLE_ONLY - no effect from 4.0; the flag is still
        readable and settable, so a program that sets it does not
        fail.

        The flag was meant to make calls to the entry points removed
        in OpenGL 3.1 fail, whatever the driver exported.  It checks
        a `deprecated` mark on each entry point as the entry point is
        built, and no entry point carries that mark.  The list of
        forward-compatible names is in
        OpenGL/platform/entrypoint31.py, and no module imports it.
        Turning the flag on changes no call.

        Requesting a forward-compatible *context* is separate and
        still works.  The window system creates such a context, and
        the backends that support the request make it.

        Default: False

    SIZE_1_ARRAY_UNPACK - if True, size-1 arrays are returned as
        scalar values, as in PyOpenGL 1.5 to 3.0.0.  For example,
        glGenLists( 1 ) returns a uint instead of an array of uints.

        Like the flags around it, it can be set from the environment
        as PYOPENGL_SIZE_1_ARRAY_UNPACK.

        Default: True

    USE_ACCELERATE - if True, use the OpenGL_accelerate package,
        when installed, for Cython-coded versions of the core
        wrapping operations.

        Default: True

    MODULE_ANNOTATIONS - if True, alternates() and constants are
        annotated with the module that defines them.  Only the
        documentation generator uses this.

        Default: False

    TYPE_ANNOTATIONS - if True, __annotations__ is filled on the
        entry points declared with OpenGL.platform.types.

        From 4.0 that is nine entry points: eight in OSMesa and one
        EGL extension, in the raw modules still written by hand.
        Entry points generated from the registry are built from the
        declaration tables and do not pass through that decorator,
        so the flag does not affect them.

        The annotation values are ctypes types and ArrayDatatype
        classes, so they describe the C signature.  Type checkers
        read the .pyi stub beside each package instead.  The stubs
        are generated from the registry, ship with a py.typed
        marker, and describe the Python signature, including the
        arguments it drops from the C signature.  See
        docs/c-dispatch.rst.

        Default: False
"""
from OpenGL.version import __version__
import os


def environ_key(name, default):
    composed = "PYOPENGL_%s" % name.upper()
    if composed in os.environ:
        value = os.environ[composed]
        if value.lower() in ("1", "true"):
            return True
        else:
            return False
    return os.environ.get(composed, default)


ERROR_CHECKING = environ_key("ERROR_CHECKING", True)
ERROR_LOGGING = environ_key("ERROR_LOGGING", False)
ERROR_ON_COPY = environ_key("ERROR_ON_COPY", False)
ARRAY_SIZE_CHECKING = environ_key("ARRAY_SIZE_CHECKING", True)
STORE_POINTERS = environ_key("STORE_POINTERS", True)
WARN_ON_FORMAT_UNAVAILABLE = environ_key("WARN_ON_FORMAT_UNAVAILABLE", False)
FORWARD_COMPATIBLE_ONLY = environ_key("FORWARD_COMPATIBLE_ONLY", False)
SIZE_1_ARRAY_UNPACK = environ_key("SIZE_1_ARRAY_UNPACK", True)
USE_ACCELERATE = environ_key("USE_ACCELERATE", True)
CONTEXT_CHECKING = environ_key("CONTEXT_CHECKING", False)
ERROR_DEBUG_OUTPUT = environ_key("ERROR_DEBUG_OUTPUT", True)

FULL_LOGGING = environ_key("FULL_LOGGING", False)
ALLOW_NUMPY_SCALARS = environ_key("ALLOW_NUMPY_SCALARS", False)
UNSIGNED_BYTE_IMAGES_AS_STRING = environ_key("UNSIGNED_BYTE_IMAGES_AS_STRING", True)
MODULE_ANNOTATIONS = environ_key("MODULE_ANNOTATIONS", False)
TYPE_ANNOTATIONS = environ_key("TYPE_ANNOTATIONS", False)


# Declarations of plugins provided by PyOpenGL itself
from OpenGL.plugins import PlatformPlugin, FormatHandler

PlatformPlugin("nt", "OpenGL.platform.win32.Win32Platform")
PlatformPlugin("darwin", "OpenGL.platform.darwin.DarwinPlatform")
# The Linux platform supports both GLX and EGL, selecting between them at
# runtime by probing for the current context, so every X11/Wayland/GLX/EGL
# key maps to the same implementation.
PlatformPlugin("linux2", "OpenGL.platform.linux.LinuxPlatform")
PlatformPlugin("linux", "OpenGL.platform.linux.LinuxPlatform")
PlatformPlugin("glx", "OpenGL.platform.linux.LinuxPlatform")
PlatformPlugin("posix", "OpenGL.platform.linux.LinuxPlatform")
PlatformPlugin("x11", "OpenGL.platform.linux.LinuxPlatform")  # xdg session type
PlatformPlugin("osmesa", "OpenGL.platform.osmesa.OSMesaPlatform")
# ANGLE supplies EGL and OpenGL ES on machines whose own GL is not ES, which on
# Windows is every machine.  It is selected only by name and never guessed,
# because it offers no desktop GL.
PlatformPlugin("angle", "OpenGL.platform.angle.ANGLEPlatform")
PlatformPlugin("egl", "OpenGL.platform.linux.LinuxPlatform")
PlatformPlugin("wayland", "OpenGL.platform.linux.LinuxPlatform")  # xdg session type
PlatformPlugin("xwayland", "OpenGL.platform.linux.LinuxPlatform")  # xdg session type


def setPlatform(key):
    """Programatically set the platform to use for PyOpenGL

    Note: you must do this *before* you import e.g. GL.* or GLES.*
    as the extension procedure lookup is platform dependent

    The PYOPENGL_PLATFORM environment variable is likely more useful
    for a *user* choosing a platform, but in cases where the programmer
    needs to choose the platform (e.g. to allow using Pygame-GLX
    under wayland) you can call `setPlatform('glx')` to force the
    use of the glx plugin.
    """
    os.environ["PYOPENGL_PLATFORM"] = key


import sys

if sys.version_info[0] < 3:
    # Python 3.x renames the built-in module
    _bi = "__builtin__"
else:
    _bi = "builtins"

FormatHandler(
    "none", "OpenGL.arrays.nones.NoneHandler", [_bi + ".NoneType"], isOutput=False
)

if sys.version_info[0] < 3:
    FormatHandler(
        "str", "OpenGL.arrays.strings.StringHandler", [_bi + ".str"], isOutput=False
    )
    FormatHandler(
        "unicode",
        "OpenGL.arrays.strings.UnicodeHandler",
        [_bi + ".unicode"],
        isOutput=False,
    )
else:
    FormatHandler(
        "bytes", "OpenGL.arrays.strings.StringHandler", [_bi + ".bytes"], isOutput=False
    )
    FormatHandler(
        "str", "OpenGL.arrays.strings.UnicodeHandler", [_bi + ".str"], isOutput=False
    )

FormatHandler(
    "list",
    "OpenGL.arrays.lists.ListHandler",
    [
        _bi + ".list",
        _bi + ".tuple",
    ],
    isOutput=False,
)
FormatHandler(
    "numbers",
    "OpenGL.arrays.numbers.NumberHandler",
    [
        _bi + ".int",
        _bi + ".float",
        _bi + ".long",
    ],
    isOutput=False,
)
FormatHandler(
    "ctypesarrays",
    "OpenGL.arrays.ctypesarrays.CtypesArrayHandler",
    [
        "_ctypes.ArrayType",
        "_ctypes.PyCArrayType",
        "_ctypes.Array",
        "_ctypes.array.Array",
        "_ctypes.array.ArrayMeta",
    ],
    isOutput=True,
)
FormatHandler(
    "ctypesparameter",
    "OpenGL.arrays.ctypesparameters.CtypesParameterHandler",
    [
        ("_ctypes" if sys.version_info[:2] >= (3,12) else _bi) + ".CArgObject",
        "ctypes.c_uint",
        "ctypes.c_int",
        "ctypes.c_float",
        "ctypes.c_double",
        "ctypes.c_ulong",
        "ctypes.c_long",
        "ctypes.c_longlong",
    ],
    isOutput=True,
)
FormatHandler(
    "ctypespointer",
    "OpenGL.arrays.ctypespointers.CtypesPointerHandler",
    [
        "ctypes.c_void_p",
        "_ctypes._Pointer",
        "ctypes.c_char_p",
        "_ctypes.pointer._Pointer",
    ],
    isOutput=False,
)
FormatHandler(
    "numpy",
    "OpenGL.arrays.numpymodule.NumpyHandler",
    [
        "numpy.ndarray",
        "numpy.core.memmap.memmap",
        "numpy.uint8",
        "numpy.uint16",
        "numpy.uint32",
        "numpy.uint64",
        "numpy.int8",
        "numpy.int16",
        "numpy.int32",
        "numpy.int64",
        "numpy.float16",
        "numpy.float32",
        "numpy.float64",
        "numpy.float128",
        # numpy names each scalar type twice: by width above, and after the C
        # type of that width here.  Whether the two names are one object
        # depends on the platform's C model.  On LLP64 (Windows), intc and
        # uintc are separate types, and an array built from a ctypes
        # declaration has them.
        "numpy.byte",
        "numpy.ubyte",
        "numpy.short",
        "numpy.ushort",
        "numpy.intc",
        "numpy.uintc",
        "numpy.longlong",
        "numpy.ulonglong",
        "numpy.single",
        "numpy.double",
    ],
    isOutput=True,
)
FormatHandler(
    "buffer",
    "OpenGL.arrays.buffers.BufferHandler",
    [
        "OpenGL.arrays._buffers.Py_buffer",
        _bi + ".memoryview",
        _bi + ".bytearray",
    ],
    isOutput=True,
)
FormatHandler(
    "vbo",
    "OpenGL.arrays.vbo.VBOHandler",
    ["OpenGL.arrays.vbo.VBO", "OpenGL_accelerate.vbo.VBO"],
    isOutput=False,
)
FormatHandler(
    "vbooffset",
    "OpenGL.arrays.vbo.VBOOffsetHandler",
    ["OpenGL.arrays.vbo.VBOOffset", "OpenGL_accelerate.vbo.VBOOffset"],
    isOutput=False,
)

# The generated modules under OpenGL/raw are not shipped.  Their content is in
# the declaration tables beside them.  Programs still import OpenGL.raw.*
# modules, and so does PyOpenGL, three lines into importing OpenGL.GL.  A
# stand-in finder goes on sys.meta_path here and loads the real finder on the
# first OpenGL.raw.* import.  The real finder reads the flags above, which a
# program sets in the lines after `import OpenGL`, so importing it here would
# read them too early.
from OpenGL import _rawfinder as _rawfinder_module

_rawfinder_module.install()


# Warning for a flag set too late
#
# The flags above are read once, when the first entry point is built, and
# copied into `OpenGL._configflags`.  Every wrapper is built from that copy.
# This is the documented order, and it works:
#
#     import OpenGL
#     OpenGL.ERROR_ON_COPY = True
#     import OpenGL.GL
#
# and this changes nothing at all:
#
#     import OpenGL.GL
#     OpenGL.ERROR_ON_COPY = True
#
# The second order is easy to reach by accident.  Under pytest, another test
# module's `import OpenGL.GL` runs during collection, before the module that
# sets the flag.  The program then runs without the setting it asked for.
# Issues #5 and #159 report this case:
# https://github.com/mcfletch/pyopengl/issues/5 and .../issues/159
#
# The late assignment warns and is not applied.  Applying it would mean
# rebuilding every entry point already bound, which an attribute assignment
# should not do.

#: The names whose values are copied into `_configflags`.
_SNAPSHOTTED_FLAGS = frozenset([
    'ERROR_CHECKING', 'ERROR_DEBUG_OUTPUT', 'ERROR_LOGGING', 'ERROR_ON_COPY',
    'ARRAY_SIZE_CHECKING', 'STORE_POINTERS', 'WARN_ON_FORMAT_UNAVAILABLE',
    'FORWARD_COMPATIBLE_ONLY', 'SIZE_1_ARRAY_UNPACK', 'USE_ACCELERATE',
    'CONTEXT_CHECKING', 'FULL_LOGGING', 'ALLOW_NUMPY_SCALARS',
    'UNSIGNED_BYTE_IMAGES_AS_STRING', 'MODULE_ANNOTATIONS', 'TYPE_ANNOTATIONS',
])


class _ConfigurationHasBeenReadWarning(RuntimeWarning):
    """A configuration flag was set after the wrappers were built from it."""


def _warn_if_too_late(name, value):
    """Warn when assigning `name` can no longer have any effect.

    Warns only after `_configflags` has copied the flags, since before that the
    assignment takes effect.  Warns only when the value differs from the
    copied one, since setting a flag to its current value changes nothing.
    """
    import sys as _sys

    snapshot = _sys.modules.get('OpenGL._configflags')
    if snapshot is None or name not in _SNAPSHOTTED_FLAGS:
        return
    if getattr(snapshot, name, value) == value:
        return
    import warnings as _warnings

    _warnings.warn(
        'OpenGL.%s was set after PyOpenGL had already read its configuration, '
        'so it has no effect: the entry points were built with %s=%r and keep '
        'that. Set it before the first `import OpenGL.GL` (or any other API '
        'namespace), or set PYOPENGL_%s in the environment, which works '
        'whatever the import order.'
        % (name, name, getattr(snapshot, name, None), name),
        _ConfigurationHasBeenReadWarning,
        stacklevel=3,
    )


def _install_flag_guard():
    """Give this module a ``__setattr__`` that warns on a late assignment."""
    import sys as _sys
    from types import ModuleType as _ModuleType

    module = _sys.modules[__name__]

    class _ConfigurationModule(_ModuleType):
        def __setattr__(self, name, value):
            _warn_if_too_late(name, value)
            _ModuleType.__setattr__(self, name, value)

    module.__class__ = _ConfigurationModule


_install_flag_guard()
