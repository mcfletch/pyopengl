"""The C implementation of the OpenGL entry points.

Selected with ``PYOPENGL_DISPATCH=c``.  The default is ``ctypes``, which is the
reference semantics, the bootstrap route for a new platform, and what runs
where no wheel exists; it is not scheduled for removal.

Installing this layer replaces the ctypes binding for an entry point with a
``GLProc``, which implements the friendly API directly rather than wrapping a
raw call.  An entry point the generator does not fully implement keeps its
ctypes binding, so the two can coexist while the phases land.
"""

import ctypes
import os
import sys

__all__ = [
    'AVAILABLE',
    'ACTIVE',
    'install',
    'entry_points',
    'suspend_error_checking',
]

#: Which implementation the process is using.  ``PYOPENGL_DISPATCH=ctypes``
#: selects the current implementation wholesale and keeps doing so after the
#: default flips.
DISPATCH = os.environ.get('PYOPENGL_DISPATCH', 'ctypes').strip().lower()

#: Ask the platform which context is current on every call rather than only
#: when resolving.  Correct for a process that switches contexts without
#: telling PyOpenGL, and costs about 95ns per call on the reference machine.
STRICT_CONTEXT = (
    os.environ.get('PYOPENGL_CONTEXT_TRACKING', 'auto').strip().lower() == 'strict'
)

AVAILABLE = False
ACTIVE = False
entry_points = {}

try:
    from OpenGL._dispatch import _dispatch as _c
except ImportError as _err:  # pragma: no cover - depends on the build
    _c = None
    _IMPORT_ERROR = _err
else:
    AVAILABLE = True
    _IMPORT_ERROR = None


def _current_context_getter():
    """The address of the platform's "which context is current" function.

    Returning ``None`` is not a failure: without it the layer dispatches
    through one table, which is right for the single-context processes that are
    the overwhelming majority, and ``make_current`` remains available.
    """
    from OpenGL import platform

    try:
        return platform.PLATFORM.currentContextAddress()
    except Exception:
        return None


def configure():
    """Hand the C layer the Python facilities it calls back into."""
    from OpenGL import _configflags, arrays  # noqa: F401 -- registers handlers
    from OpenGL._dispatch import _tables, support

    error_slot = -1
    proc = entry_points.get(('GL', 'glGetError'))
    if proc is not None:
        error_slot = _tables.SLOTS[('GL', 'glGetError')]
    _c._configure(
        support,
        support.array_type_list(_tables.ARRAY_TYPES),
        ctypes_simple=ctypes._SimpleCData,
        ctypes_pointer=ctypes._Pointer,
        error_slot=error_slot,
        get_current_context=_current_context_getter() or 0,
        strict_context=STRICT_CONTEXT,
        array_size_checking=_configflags.ARRAY_SIZE_CHECKING,
        error_checking=_configflags.ERROR_CHECKING,
        error_proc=proc,
        size_1_array_unpack=_configflags.SIZE_1_ARRAY_UNPACK,
    )


def install():
    """Make the C layer the implementation of the entry points.

    Two hooks are enough, so none of the 1,299 generated modules changes:
    ``platform.createFunction`` hands back a ``GLProc`` where one exists, and
    ``wrapper.wrapper`` passes a ``GLProc`` straight through because the C
    already implements what the wrapper would have added.
    """
    global ACTIVE
    if ACTIVE or not AVAILABLE:
        return ACTIVE
    entry_points.update(_c.entry_points)
    configure()

    from OpenGL import platform, wrapper

    _base_wrapper = wrapper.wrapper
    # The platform installs its bound methods into the module namespace at
    # import, and that is the name the friendly modules call, so the module
    # attribute is what has to be replaced.
    _base_extension = platform.createExtensionFunction

    def wrapper_(base):
        """A C entry point already implements what the wrapper would add."""
        if isinstance(base, _c.GLProc):
            return base
        return _base_wrapper(base)

    def createExtensionFunction(functionName, dll, *args, **named):
        """A few friendly modules rebuild an entry point from scratch.

        ``OpenGL.GL.VERSION.GL_2_0`` builds its own ``glShaderSource`` rather
        than customising the generated one, so that declaration never reaches
        ``createFunction``.  Catching it here lets the hand-written C
        implementation win where there is one.
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
    return True


#: Which namespace a library object serves.  GL, GLX and WGL share one library,
#: so the name's prefix settles it where they overlap.
_DLL_APIS = ('GLES2', 'GLES3', 'GLES1', 'EGL', 'GL')


def _api_of_dll(dll):
    from OpenGL import platform

    for api in _DLL_APIS:
        if getattr(platform.PLATFORM, api, None) is dll:
            return api
    return 'GL'


def _handwritten_for(name, dll):
    """The hand-written C entry point for a rebuilt binding, if there is one."""
    from OpenGL._dispatch import _tables

    if name not in _tables.HANDWRITTEN:
        return None
    return entry_points.get((_api_of_dll(dll), name))


def entry_point_for(function, binding):
    """The C entry point for a declaration, or None to keep the ctypes one."""
    api = _api_of(function.__module__)
    name = function.__name__
    proc = entry_points.get((api, name))
    if proc is None:
        return None
    from OpenGL._dispatch import support

    support.register_ctypes_binding(api, name, binding)
    support.register_module(api, name, function.__module__)
    return proc


def _api_of(module_name):
    """``OpenGL.raw.GL.VERSION.GL_1_1`` names the GL API."""
    parts = module_name.split('.')
    if len(parts) > 2 and parts[1] == 'raw':
        return parts[2]
    return 'GL'


def suspend_error_checking(suspend):
    """Turn the C layer's per-call error check off, and on again.

    ``glGetError`` between ``glBegin`` and ``glEnd`` is itself an invalid
    operation, so OpenGL.GL.exceptional suspends checking for the block.  Those
    two entry points stay on the ctypes path, so they tell the C layer rather
    than the C layer keeping a second switch of its own.
    """
    if ACTIVE:
        _c.suspend_error_checking(bool(suspend))


def make_current(handle):
    """Dispatch this thread through the table for ``handle``.

    Call this wherever the application makes a context current, so that N
    contexts in one process each resolve and hold their own entry points.
    """
    if AVAILABLE:
        _c.make_current(int(handle or 0))


def forget_context(handle):
    """Free the dispatch table for a context that has been destroyed."""
    if AVAILABLE:
        _c.forget_context(int(handle or 0))


