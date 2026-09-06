"""The C implementation of the OpenGL entry points.

It is compiled, so it ships in ``PyOpenGL_accelerate``; where that is installed
on CPython it is what runs, and ``PYOPENGL_DISPATCH=ctypes`` selects the ctypes
implementation instead.  That one is the reference semantics, the bootstrap
route for a new platform, and what runs with ``PyOpenGL`` alone and on every
interpreter other than CPython; it is not scheduled for removal.

Installing this layer replaces the ctypes binding for an entry point with a
``GLProc``, which implements the friendly API directly rather than wrapping a
raw call.  An entry point the generator does not fully implement keeps its
ctypes binding, so the two coexist.
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
#: the arrangement the rest of PyOpenGL's accelerators are in.
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

    An extension that does not say which version it holds is a mismatch, not a
    pass.  The pair this exists to refuse is an accelerate left behind by a
    partial upgrade, and an accelerate old enough to be dangerous is exactly the
    one that would not carry the attribute.
    """
    if _c is None:
        return True
    from OpenGL.version import __version__ as ours

    return getattr(_c, '__pyopengl_version__', None) == ours


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
    """Say how ``api`` is asked for its errors, from the checker it declares.

    ``OpenGL/raw/<api>/_errors.py`` builds one checker per API stating which
    function is asked, which code means success and which exception carries the
    answer.  Both implementations read that one statement: the ctypes bindings
    call the checker, and this hands the same three facts to the compiled
    layer, which does the call itself.

    A checker with nothing to ask -- GLX's, and WGL's absence of one -- leaves
    the API unpolled, which is what it does under ctypes, where such a checker
    answers its no-error result and never raises.

    The function taken is the driver's own, ``_baseGetErrors``, and not
    whichever reader the checker is pointed at now: ``setErrorReader`` swaps
    ``_getErrors`` for a Python callable reading the GL_KHR_debug flag, which
    is the ctypes implementation's business and names no entry point.  Handing
    that one over would leave the compiled layer with no slot to ask and the
    API unpolled -- error checking off for every call it makes.
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


def _wanted():
    """Whether the caller has asked for the compiled layer at all.

    Both switches are read here rather than at import.  A program sets
    ``OpenGL.USE_ACCELERATE`` in the lines *after* ``import OpenGL``, and this
    runs later still, when the first entry point is built -- reading either one
    at import would see the configuration before it had been written.

    Asking this *before* the pair is judged is what keeps somebody who has said
    they do not want the extension from being handed an error about the
    extension.  A mismatched accelerate left behind by a partial upgrade is
    exactly when a person reaches for the switch, and it has to work.

    ``USE_ACCELERATE`` is read from the package rather than from
    ``_configflags``, which snapshots it when *it* is first imported -- and the
    first import may be a framework's, a profiler's, or another binding
    stacked on PyOpenGL, none of which the caller controls.  The snapshot would
    then predate the assignment and the switch would do nothing, with no error
    to say so.  ``DISPATCH`` comes from the environment and has no such setter.
    """
    import OpenGL
    from OpenGL import _configflags

    return bool(OpenGL.USE_ACCELERATE) and _configflags.DISPATCH == 'c'


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


#: The names a program calls live in :mod:`OpenGL.dispatch`, which is where
#: their implementation lives too.  They are re-exported here because that is
#: the module the documentation named before there was a public one, and code
#: written against it keeps working.
from OpenGL.dispatch import (  # noqa: E402  -- after the layer it reads
    debug_output_available,
    forget_context,
    make_current,
    reclaim_retired,
    set_error_checking,
    use_debug_output,
)


