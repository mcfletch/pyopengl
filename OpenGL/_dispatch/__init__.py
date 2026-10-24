"""The C implementation of the OpenGL entry points.

The C implementation is compiled and ships in ``PyOpenGL_accelerate``.  It
runs on CPython where that package is installed.  ``PYOPENGL_DISPATCH=ctypes``
selects the ctypes implementation instead.  The ctypes implementation defines
the reference behaviour and is the starting point for a new platform.  It runs
with ``PyOpenGL`` alone and on every interpreter other than CPython, and it
remains supported.

Installing this layer replaces the ctypes binding for an entry point with a
``GLProc``.  A ``GLProc`` implements the friendly API directly instead of
wrapping a raw call.  Entry points the generator does not fully implement keep
their ctypes binding, so the two kinds coexist.
"""

import ctypes
import os

__all__ = [
    'AVAILABLE',
    'ACTIVE',
    'install',
    'entry_points',
    'suspend_error_checking',
    'use_debug_output',
    'debug_output_available',
    'set_error_checking',
]

#: How the layer decides which context's table to dispatch through.
#:
#: ``auto`` (the default) re-reads the current context whenever an entry point
#: needs resolving, and otherwise relies on ``make_current``.  The ctypes
#: implementation holds one binding per process and cannot tell contexts
#: apart, so ``auto`` is never less accurate than ctypes.
#:
#: ``verify`` queries the platform on every call.  Use it for a program that
#: switches between contexts of different capability without calling
#: ``make_current``.  It costs about 97ns per call on the reference machine.
CONTEXT_TRACKING = os.environ.get('PYOPENGL_CONTEXT_TRACKING', 'auto').strip().lower()
_TRACK_VERIFY, _TRACK_NOTIFY = 0, 1
TRACKING = _TRACK_VERIFY if CONTEXT_TRACKING in ('verify', 'strict') else _TRACK_NOTIFY

AVAILABLE = False
ACTIVE = False
entry_points = {}

#: The compiled layer.  It is built by ``pyopengl_accelerate``, an optional
#: compiled package released from the same repository, so that PyOpenGL itself
#: stays a single universal wheel.  Without accelerate installed there is no
#: extension and the ctypes implementation runs.  PyOpenGL's other
#: accelerators work the same way.
try:
    from OpenGL_accelerate import dispatch as _c
except ImportError as _err:  # pragma: no cover - depends on what is installed
    _c = None
    _IMPORT_ERROR = _err
else:
    AVAILABLE = True
    _IMPORT_ERROR = None


def _versions_match():
    """Return whether PyOpenGL and the extension were generated together.

    They share the generated slot numbering and table layout.  A mismatched
    pair does not fail cleanly: it dispatches through the wrong indices.  The
    two are released together, so requiring equal versions replaces a crash
    with an error message.

    An extension without a version attribute counts as a mismatch.  The usual
    mismatch is an old accelerate left by a partial upgrade, and the oldest
    builds do not carry the attribute.
    """
    if _c is None:
        return True
    from OpenGL.version import __version__ as ours

    return getattr(_c, '__pyopengl_version__', None) == ours


def _current_context_getter():
    """Return the address of the platform's current-context function, or None.

    With ``None`` the layer dispatches through one table.  That is correct for
    a process with a single context, which is the common case, and
    ``make_current`` still works.

    Not called at import.  Finding whether EGL or GLX owns the current context
    means probing both, and probing loads the driver (26 MB of libnvidia on
    the development machine).  At import there is no current context to find.
    :func:`install_context_getter` calls this at the first entry-point
    resolution instead, the first point at which a context can exist.
    """
    from OpenGL import platform

    from OpenGL._dispatch import support

    try:
        # Probe only if the caller has asked for context checking.  The
        # application's toolkit loads EGL or GLX itself, so once a context
        # exists the library is usually already loaded.  Before that there is
        # no context to find.
        return platform.PLATFORM.currentContextAddress(
            probe=support.probe_allowed()
        )
    except TypeError:  # a platform whose signature predates the argument
        try:
            return platform.PLATFORM.currentContextAddress()
        except Exception:
            return None
    except Exception:
        return None


#: Whether the address has been handed to the C layer yet.
_context_getter_installed = False


def install_context_getter():
    """Pass the C layer the function that returns the current context.

    Called from the first entry-point resolution.  Idempotent and cheap after
    the first call, because it is on that path.
    """
    global _context_getter_installed
    if _context_getter_installed or not AVAILABLE:
        return
    address = _current_context_getter()
    if address:
        # Marked installed only once an address is found.  Before a context
        # exists there is none, and trying again costs an attribute read.
        _context_getter_installed = True
        _c.set_context_getter(address)


def configure():
    """Pass the C layer the Python functions it calls back into."""
    from OpenGL import _configflags, arrays  # noqa: F401 -- registers handlers
    from OpenGL._dispatch import _tables, support

    error_slot = -1
    proc = entry_points.get(('GL', 'glGetError'))
    if proc is not None:
        error_slot = _tables.SLOTS[('GL', 'glGetError')]
    _c._configure(
        support,
        support.array_type_map(),
        ctypes_simple=ctypes._SimpleCData,
        ctypes_pointer=ctypes._Pointer,
        error_slot=error_slot,
        # Deferred: see install_context_getter().
        get_current_context=0,
        strict_context=False,
        context_tracking=TRACKING,
        array_size_checking=_configflags.ARRAY_SIZE_CHECKING,
        error_checking=_configflags.ERROR_CHECKING,
        error_proc=proc,
        size_1_array_unpack=_configflags.SIZE_1_ARRAY_UNPACK,
        context_checking=_configflags.CONTEXT_CHECKING,
    )


#: The APIs whose errors are GL's: reported by the GL_KHR_debug callback, and
#: suspended inside a glBegin block, which is a GL construct.
_GL_FAMILY = ('GL', 'GLES1', 'GLES2', 'GLES3', 'GLSC2')


def register_error_source(api, checker):
    """Register how errors are read for ``api``, from the checker it declares.

    ``OpenGL/raw/<api>/_errors.py`` builds one checker per API.  The checker
    names the function to call, the code that means success, and the
    exception to raise.  Both implementations use it.  The ctypes bindings
    call the checker, and this function passes the same three values to the
    compiled layer, which makes the call itself.

    A checker with no error function (GLX's, or WGL's missing checker) leaves
    the API unpolled.  Under ctypes such a checker returns its no-error result
    and never raises, so the behaviour is the same.

    The function passed is the driver's own, ``_baseGetErrors``, instead of
    the checker's current reader.  ``setErrorReader`` replaces ``_getErrors``
    with a Python callable that reads the GL_KHR_debug flag.  That callable
    belongs to the ctypes implementation and names no entry point.  Passing it
    would leave the compiled layer with no slot to call, and error checking
    would be off for every call in the API.
    """
    from OpenGL._dispatch import _tables, support

    getter = getattr(checker, '_baseGetErrors', None) if checker is not None else None
    errorClass = getattr(checker, '_errorClass', None) if getter else None
    support.register_error_class(api, errorClass or error_module().GLError)
    if not AVAILABLE:
        return
    if getter is None:
        _c.set_error_source(api, -1, None, 0, api in _GL_FAMILY)
        return
    name = getattr(getter, '__name__', None)
    proc = entry_points.get((api, name)) if name else None
    slot = _tables.SLOTS.get((api, name), -1) if name else -1
    _c.set_error_source(
        api,
        slot,
        proc,
        int(getattr(checker, '_noErrorResult', 0)),
        api in _GL_FAMILY,
    )


def error_module():
    from OpenGL import error

    return error


def install_finder():
    """Install the import finder for the generated module names.

    The modules under ``OpenGL/raw`` are not shipped, because the declaration
    tables hold the same information.  A finder must supply them when a
    program imports one, under either implementation.

    The implementation is chosen when the first module is built, not here.
    This runs at ``import OpenGL``, and a program sets
    ``OpenGL.ERROR_CHECKING`` and the related flags after that import.
    Choosing now would read the configuration before it is set.
    """
    # Imported here instead of at module level, so an unused module costs
    # nothing.  finder checks whether it is needed without importing
    # _configflags, which would read every flag from OpenGL before a program
    # had set them.
    from OpenGL._dispatch import finder

    if ACTIVE:
        return finder.install(_c, entry_points)
    return finder.install()


def _wanted():
    """Return whether the configuration requests the compiled layer.

    Both settings are read here instead of at import.  A program sets
    ``OpenGL.USE_ACCELERATE`` after ``import OpenGL``.  This runs later, when
    the first entry point is built, so it reads the value the program set.

    This is checked before the version check.  A program that turns the
    extension off then gets no error about the extension.  Turning it off is
    the usual response to a mismatched accelerate left by a partial upgrade,
    so it must work in that case.

    ``USE_ACCELERATE`` is read from the package instead of from
    ``_configflags``.  ``_configflags`` copies it when first imported, and the
    first import may come from a framework, a profiler or another binding
    built on PyOpenGL.  The copy would then predate the program's assignment,
    and the setting would silently have no effect.  ``DISPATCH`` comes from
    the environment and has no setter.
    """
    import OpenGL
    from OpenGL import _configflags

    return bool(OpenGL.USE_ACCELERATE) and _configflags.DISPATCH == 'c'


def install():
    """Make the C layer the implementation of the entry points.

    Two hooks are installed, and none of the 1,299 generated modules changes.
    ``platform.createFunction`` returns a ``GLProc`` where one exists.
    ``wrapper.wrapper`` passes a ``GLProc`` through unchanged, because the C
    code already implements what the wrapper would add.
    """
    global ACTIVE
    if ACTIVE or not AVAILABLE:
        return ACTIVE
    if not _wanted():
        return False
    if not _versions_match():
        from OpenGL.version import __version__ as ours

        raise ImportError(
            'pyopengl %s and pyopengl_accelerate %s were not built together; '
            'they share generated tables, so the pair must match exactly. '
            'Install the same version of both, or run on ctypes by setting '
            'PYOPENGL_USE_ACCELERATE=0 in the environment (or '
            'OpenGL.USE_ACCELERATE = False before the first entry point is '
            'used).'
            % (ours, getattr(_c, '__pyopengl_version__', 'unknown'))
        )
    entry_points.update(_c.entry_points)
    configure()

    from OpenGL import platform, wrapper

    _base_wrapper = wrapper.wrapper
    # The platform copies its bound methods into the module namespace at
    # import, and the friendly modules call that name, so the module attribute
    # is replaced.
    _base_extension = platform.createExtensionFunction

    def wrapper_(base):
        """Return a C entry point unchanged; wrap anything else."""
        if isinstance(base, _c.GLProc):
            return base
        return _base_wrapper(base)

    def createExtensionFunction(functionName, dll, *args, **named):
        """Return the hand-written C entry point for a rebuilt binding, if any.

        A few friendly modules build an entry point themselves.
        ``OpenGL.GL.VERSION.GL_2_0`` builds its own ``glShaderSource`` instead
        of customising the generated one, so that declaration never reaches
        ``createFunction``.  Intercepting it here uses the hand-written C
        implementation where there is one.
        """
        binding = _base_extension(functionName, dll, *args, **named)
        proc = _handwritten_for(functionName, dll)
        if proc is None:
            return binding
        from OpenGL._dispatch import support

        support.register_ctypes_binding(_api_of_dll(dll), functionName, binding)
        return proc

    wrapper.wrapper = wrapper_
    platform.createExtensionFunction = createExtensionFunction
    ACTIVE = True
    # Last, because the finder returns the C entry points only when ACTIVE is
    # set.
    install_finder()
    return True


#: The API namespaces a library object can serve.  GL, GLX and WGL share one
#: library, so the function name's prefix decides between them.
_DLL_APIS = ('GLES2', 'GLES3', 'GLES1', 'EGL', 'GL')


def _api_of_dll(dll):
    from OpenGL import platform

    for api in _DLL_APIS:
        if getattr(platform.PLATFORM, api, None) is dll:
            return api
    return 'GL'


def _handwritten_for(name, dll):
    """Return the hand-written C entry point for a rebuilt binding, or None."""
    from OpenGL._dispatch import _tables

    if name not in _tables.HANDWRITTEN:
        return None
    return entry_points.get((_api_of_dll(dll), name))


def entry_point_for(function, build_binding):
    """Return the C entry point for a declaration, or None to keep ctypes.

    ``build_binding`` is a callable instead of a binding.  The binding is only
    needed when an entry point is demoted to ctypes, which is rare.  Building
    one per entry point would be most of the import cost.
    """
    api = _api_of(function.__module__)
    name = function.__name__
    proc = entry_points.get((api, name))
    if proc is None:
        return None
    from OpenGL._dispatch import support

    support.register_ctypes_factory(api, name, build_binding)
    support.register_module(api, name, function.__module__)
    return proc


def _api_of(module_name):
    """Return the API a raw module belongs to.

    ``OpenGL.raw.GL.VERSION.GL_1_1`` belongs to ``GL``.
    """
    parts = module_name.split('.')
    if len(parts) > 2 and parts[1] == 'raw':
        return parts[2]
    return 'GL'


def suspend_error_checking(suspend):
    """Turn the C layer's per-call error check off, and on again.

    ``glGetError`` between ``glBegin`` and ``glEnd`` is an invalid operation,
    so OpenGL.GL.exceptional suspends checking for the block.  Those two entry
    points stay on the ctypes path and call this function, so the C layer
    needs no separate switch.
    """
    if ACTIVE:
        _c.suspend_error_checking(bool(suspend))


#: These functions are defined in :mod:`OpenGL.dispatch`.  They are
#: re-exported here for code that imports them from this module.
from OpenGL.dispatch import (  # noqa: E402  -- after the layer it reads
    debug_output_available,
    forget_context,
    make_current,
    reclaim_retired,
    set_error_checking,
    use_debug_output,
)


