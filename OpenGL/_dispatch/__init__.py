"""The C implementation of the OpenGL entry points.

It is compiled, so it ships in ``PyOpenGL_accelerate``; where that is installed
on CPython it is what runs, and ``PYOPENGL_DISPATCH=ctypes`` selects the older
implementation instead.  That one is the reference semantics, the bootstrap
route for a new platform, and what runs with ``PyOpenGL`` alone; it is not
scheduled for removal.

Installing this layer replaces the ctypes binding for an entry point with a
``GLProc``, which implements the friendly API directly rather than wrapping a
raw call.  An entry point the generator does not fully implement keeps its
ctypes binding, so the two coexist.
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
    'use_debug_output',
    'debug_output_available',
    'set_error_checking',
]

#: Which implementation the process is using.  ``PYOPENGL_DISPATCH=ctypes``
#: selects the older implementation wholesale, and keeps doing so: it is the
#: reference semantics and is not scheduled for removal.
DISPATCH = os.environ.get('PYOPENGL_DISPATCH', 'c').strip().lower()

#: How the layer decides which context's table to dispatch through.
#:
#: ``auto`` (the default) re-reads the current context whenever an entry point
#: needs resolving, and otherwise trusts ``make_current``.  That is the same
#: exposure the ctypes implementation has always had -- it holds one binding
#: per process and cannot tell contexts apart at all -- so per-context tables
#: can only improve on it.
#:
#: ``verify`` asks the platform on every call, for a program that switches
#: between contexts of differing capability without saying so.  It costs about
#: 97ns per call on the reference machine.
CONTEXT_TRACKING = os.environ.get('PYOPENGL_CONTEXT_TRACKING', 'auto').strip().lower()
_TRACK_VERIFY, _TRACK_NOTIFY = 0, 1
TRACKING = _TRACK_VERIFY if CONTEXT_TRACKING in ('verify', 'strict') else _TRACK_NOTIFY

AVAILABLE = False
ACTIVE = False
entry_points = {}

#: Where the compiled layer lives.  It is built by ``pyopengl_accelerate``,
#: the optional compiled companion released from the same repository, so that
#: PyOpenGL itself stays a single universal wheel.  Without accelerate
#: installed there is no extension and the ctypes implementation runs, which is
#: exactly the arrangement PyOpenGL has always had for its accelerators.
try:
    from OpenGL_accelerate import dispatch as _c
except ImportError as _err:  # pragma: no cover - depends on what is installed
    _c = None
    _IMPORT_ERROR = _err
else:
    AVAILABLE = True
    _IMPORT_ERROR = None


def _versions_match():
    """Whether the two packages are the pair they were generated as.

    They share the generated slot numbering and table layout, so a mismatched
    pair does not fail cleanly -- it dispatches through the wrong indices.
    They are released together, so requiring equality costs nothing and turns
    a confusing crash into a sentence.
    """
    if _c is None:
        return True
    from OpenGL.version import __version__ as ours

    theirs = getattr(_c, '__pyopengl_version__', None)
    return theirs is None or theirs == ours


def _current_context_getter():
    """The address of the platform's "which context is current" function.

    Returning ``None`` is not a failure: without it the layer dispatches
    through one table, which is right for the single-context processes that are
    the overwhelming majority, and ``make_current`` remains available.

    Not called at import.  Finding out whether EGL or GLX owns the current
    context means probing both, and probing loads the driver -- 26 MB of
    libnvidia here -- to answer a question that has no answer yet, because at
    import there is no current context.  :func:`install_context_getter` calls
    this at the first resolution instead, which is the first moment a context
    exists to be asked about.
    """
    from OpenGL import platform

    from OpenGL._dispatch import support

    try:
        # Without probing unless the caller has asked for context checking:
        # the application's own toolkit loads whichever of EGL and GLX it
        # uses, so by the time a context exists the answer is usually there
        # for the taking, and before that there is nothing to take.
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
    """Tell the C layer how to ask which context is current.

    Called from the first entry-point resolution.  Idempotent and cheap after
    the first call, because it is on that path.
    """
    global _context_getter_installed
    if _context_getter_installed or not AVAILABLE:
        return
    address = _current_context_getter()
    if address:
        # Only settled once there is an answer.  Before a context exists there
        # is none, and asking again next time costs an attribute read.
        _context_getter_installed = True
        _c.set_context_getter(address)


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


def install_finder():
    """Answer for the generated module names, whichever implementation is used.

    The modules under ``OpenGL/raw`` are not shipped -- they held nothing the
    declaration tables do not -- so something has to answer when a program
    imports one, and that is as true on ctypes as it is on C.

    Which of the two answers is settled on the first module built, not here.
    This runs at ``import OpenGL``, and a program sets ``OpenGL.ERROR_CHECKING``
    and its neighbours in the lines *after* that import; deciding now would
    read the configuration before it had been written.
    """
    # Imported here rather than at module level: a module nobody has switched
    # on should cost nothing to leave switched off.  finder decides whether it
    # is wanted without importing _configflags, which would read every flag off
    # OpenGL before a program had finished setting them.
    from OpenGL._dispatch import finder

    if ACTIVE:
        return finder.install(_c, entry_points)
    return finder.install()


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
    if not _versions_match():
        from OpenGL.version import __version__ as ours

        raise ImportError(
            'pyopengl %s and pyopengl_accelerate %s were not built together; '
            'they share generated tables, so the pair must match exactly. '
            'Install the same version of both, or uninstall '
            'pyopengl_accelerate to run on ctypes.'
            % (ours, getattr(_c, '__pyopengl_version__', 'unknown'))
        )
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
    # Last, because the finder hands out the C entry points and ACTIVE is what
    # tells it there are any.
    install_finder()
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


def entry_point_for(function, build_binding):
    """The C entry point for a declaration, or None to keep the ctypes one.

    ``build_binding`` is a callable rather than a binding: what it builds is
    only wanted where a client demotes, which is rare enough that building one
    per entry point is the larger part of what importing costs.
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


#: GL_KHR_debug enums, so that turning the mechanism on needs no import from
#: a particular API module.
_DEBUG_OUTPUT = 0x92E0
_DEBUG_OUTPUT_SYNCHRONOUS = 0x8242
_DEBUG_SEVERITY_NOTIFICATION = 0x826B
_DONT_CARE = 0x1100


def debug_output_available():
    """Whether the current context reports errors through GL_KHR_debug."""
    if not ACTIVE:
        return False
    proc = entry_points.get(('GL', 'glDebugMessageCallback'))
    return bool(proc) if proc is not None else False


def use_debug_output(enable=True):
    """Notice GL errors through GL_KHR_debug rather than a glGetError per call.

    A per-call ``glGetError`` is a driver round trip and it is the whole cost
    of error checking.  With this on, the driver reports an error through a
    callback during the call itself, and the check afterwards is a read of the
    flag that callback set.  What a caller sees does not change: the same
    exception, raised from the same call.

    Returns True when it took effect.  It needs a context offering
    ``GL_KHR_debug``; without one, error checking stays as it was.
    """
    if not ACTIVE:
        return False
    if not enable:
        _c.set_error_mode(0)
        return True
    if not debug_output_available():
        return False

    from OpenGL.GL import (
        glDebugMessageCallback,
        glDebugMessageControl,
        glEnable,
    )

    address = _c.debug_callback_address()
    callback = ctypes.cast(ctypes.c_void_p(address), _debug_callback_type())
    glEnable(_DEBUG_OUTPUT)
    # Synchronous, because the callback has to run during the call it belongs
    # to for the stub to attribute the error to the right entry point.
    glEnable(_DEBUG_OUTPUT_SYNCHRONOUS)
    glDebugMessageCallback(callback, None)
    # Notifications are chatter; the callback only cares about errors, and not
    # asking for the rest keeps the driver from formatting them.
    glDebugMessageControl(
        _DONT_CARE, _DONT_CARE, _DEBUG_SEVERITY_NOTIFICATION, 0, None, False
    )
    _c.set_error_mode(1)
    # The callback holds the reference the driver will call through.
    _installed_callbacks.append(callback)
    return True


_installed_callbacks = []


def _debug_callback_type():
    from OpenGL.raw.GL._types import GLDEBUGPROC

    return GLDEBUGPROC


def set_error_checking(enable=True, entry_point=None):
    """Turn per-call error checking on or off, for one entry point or all.

    Unlike ``OpenGL.ERROR_CHECKING``, which is read once at import, this takes
    effect immediately and can be scoped to a single entry point.
    """
    if ACTIVE:
        _c.set_error_checking(bool(enable), entry_point)


def _end_suspended_block():
    """End the glBegin block, if any, error checking is suspended for.

    A Begin/End block belongs to the context it was opened in, so a context
    change ends it.  That matters because ``glEnd`` is otherwise the only
    thing that turns checking back on, and an exception raised between the
    two -- a bad vertex, an entry point the driver does not export -- means
    ``glEnd`` never runs and every later call in the process goes unchecked.

    Reads ``sys.modules`` rather than importing: a process using only ES or
    EGL has no desktop-GL checker to resume, and importing one to find that
    out would load a driver to answer a question about a block it cannot
    have opened.  The compiled layer keeps the same switch of its own, which
    ``make_current`` and ``forget_context`` clear for themselves.
    """
    module = sys.modules.get('OpenGL.raw.GL._errors')
    checker = getattr(module, '_error_checker', None) if module else None
    if checker is not None:
        checker.onEnd()


def make_current(handle):
    """Dispatch this thread through the table for ``handle``.

    Call this wherever the application makes a context current, so that N
    contexts in one process each resolve and hold their own entry points.
    """
    _end_suspended_block()
    if AVAILABLE:
        _c.make_current(int(handle or 0))


def forget_context(handle):
    """Free the dispatch table for a context that has been destroyed."""
    _end_suspended_block()
    if AVAILABLE:
        _c.forget_context(int(handle or 0))


