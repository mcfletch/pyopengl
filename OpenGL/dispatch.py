"""Report and control which implementation dispatches the GL entry points.

PyOpenGL dispatches through one of two implementations.  The C
implementation is generated from the Khronos registry and compiled.  It ships
in ``PyOpenGL_accelerate`` and runs under CPython where that package is
installed.  The ctypes implementation is pure Python and runs everywhere else.
Both implement the same API.  This module reports which one a process is
using::

    >>> from OpenGL import dispatch
    >>> dispatch.active()
    'c'
    >>> dispatch.status()
    Status(requested='c', active='c', available=True, reason=None)

The extension is optional.  Asking for the C implementation where it is not
installed leaves the ctypes implementation in place, with no warning or
error.  A program or test suite that requires the C implementation must
check, and :func:`status` gives the reason when it is not active.

The rest of the module controls the dispatch layer.  Under the C
implementation each context holds its own function pointer for every entry
point, so two contexts with different capabilities each resolve correctly.
:func:`make_current` records that a context has become current, and
:func:`forget_context` records that one has been destroyed.  Call both under
either implementation, because both determine which context PyOpenGL checks
errors in.  :func:`context_identity` returns an object representing the
current context.  A context created after another is destroyed gets a new
identity, even where the driver reuses the old handle.

The module also controls error checking.  A context that supports
``GL_KHR_debug`` uses debug output by default.  The driver reports an error
through a callback during the call, so the check after each call reads a flag
instead of calling ``glGetError``.  :func:`error_checking_mode` returns the
mechanism a context uses.
"""

import ctypes
import os
import sys
import threading
from typing import NamedTuple, Optional

__all__ = [
    'Status',
    'requested',
    'active',
    'available',
    'settle',
    'status',
    'make_current',
    'forget_context',
    'context_identity',
    'reclaim_retired',
    'set_error_checking',
    'error_checking_mode',
    'use_debug_output',
    'debug_output_available',
    'offer_debug_output',
]


class Status(NamedTuple):
    """The requested and active implementations, availability, and reason."""

    #: Which implementation the configuration asks for: ``'c'`` or ``'ctypes'``.
    requested: str
    #: Which implementation the entry points built so far dispatch through.
    active: str
    #: Whether the compiled layer is installed and importable.
    available: bool
    #: Why the entry points are the ctypes ones, or None where they are not.
    reason: Optional[str]


def _layer():
    """The compiled layer, or None where the entry points are the ctypes ones.

    Read from ``sys.modules`` instead of imported.  The extension is 13 MB and
    the ctypes path never imports it.  Programs on the ctypes path still call
    :func:`make_current`, and that call must not load the extension.  If the
    module is not loaded, it is not installed, because installing it loads it.
    """
    module = sys.modules.get('OpenGL._dispatch')
    if module is None or not module.ACTIVE:
        return None
    return module._c


def requested():
    """Return the requested implementation, ``'c'`` or ``'ctypes'``.

    ``PYOPENGL_DISPATCH`` names one directly.  Unset, it is ``'c'`` on CPython
    and ``'ctypes'`` on other interpreters, where the extension is not built.
    ``OpenGL.USE_ACCELERATE = False`` and ``OpenGL.FULL_LOGGING`` also request
    ctypes; :func:`status` reports which setting did.
    """
    from OpenGL import _configflags

    if _configflags.DISPATCH == 'c' and _configflags.USE_ACCELERATE:
        return 'c'
    return 'ctypes'


def active():
    """Return the implementation the entry points use, ``'c'`` or ``'ctypes'``.

    The choice is made when the first entry point is built.  Before anything
    from ``OpenGL.GL`` is imported, this returns ``'ctypes'`` whatever the
    configuration.  Call :func:`settle` to make the choice earlier.
    """
    return 'ctypes' if _layer() is None else 'c'


def available():
    """Return whether the compiled layer is installed and importable.

    Uses the loaded module where there is one.  Otherwise it queries the
    import system, which does not load the 13 MB extension.
    """
    module = sys.modules.get('OpenGL._dispatch')
    if module is not None:
        return module.AVAILABLE
    from importlib.util import find_spec

    try:
        return find_spec('OpenGL_accelerate.dispatch') is not None
    except (ImportError, ValueError):  # pragma: no cover - depends on the build
        return False


def settle():
    """Choose the implementation now and return ``'c'`` or ``'ctypes'``.

    Without this call, the first entry point built makes the choice.  The
    choice reads ``OpenGL.ERROR_CHECKING`` and the related flags, so call this
    after setting them, as with importing ``OpenGL.GL``.

    Use it where code must know the implementation before rendering.  Examples
    are a test suite for the C implementation, or a program that should fail
    instead of running several times slower on ctypes.
    """
    if requested() != 'c':
        return 'ctypes'
    try:
        from OpenGL import _dispatch
    except ImportError:  # pragma: no cover - depends on what is installed
        return 'ctypes'
    return 'c' if _dispatch.install() else 'ctypes'


def status():
    """Return a :class:`Status` of requested, active, available and reason.

    The reason is a sentence naming the setting or the missing package
    responsible.  A caller can include it in an error message::

        state = dispatch.status()
        if state.active != 'c':
            raise SystemExit('this program needs the C dispatch: %s' % state.reason)
    """
    asked, running = requested(), active()
    return Status(asked, running, available(), _reason(asked, running))


def _reason(asked, running):
    """Why the entry points are the ctypes ones, in the caller's terms."""
    if running == 'c':
        return None
    from OpenGL import _configflags

    if _configflags.FULL_LOGGING:
        return (
            'OpenGL.FULL_LOGGING is on, and the call trace is written by the '
            'ctypes wrapper chain'
        )
    if not _configflags.USE_ACCELERATE:
        return 'OpenGL.USE_ACCELERATE is off, which turns off every compiled accelerator'
    if asked != 'c':
        # Where a caller set the environment variable, that setting decided,
        # so it is reported instead of the interpreter.  Unset, the
        # interpreter decided.
        if 'PYOPENGL_DISPATCH' in os.environ:
            return 'PYOPENGL_DISPATCH asks for the ctypes implementation'
        if sys.implementation.name != 'cpython':
            return (
                'the C dispatch extension is built for CPython only, and this '
                'is %s' % (sys.implementation.name,)
            )
        return 'PYOPENGL_DISPATCH asks for the ctypes implementation'
    if not available():
        return 'PyOpenGL_accelerate is not installed, so there is no C implementation'
    return (
        'no entry point has been built yet, and the choice is made when the '
        'first one is'
    )


def _end_suspended_block():
    """End the glBegin block that error checking is suspended for, if any.

    A Begin/End block belongs to the context it was opened in, so a context
    change ends it.  Error checking is suspended inside the block, and only
    ``glEnd`` turns it back on.  If an exception is raised inside the block
    (a bad vertex, or an entry point the driver does not export), ``glEnd``
    never runs and every later call in the process goes unchecked.

    The block is also closed in GL.  The suspension flag records the driver's
    state but does not change it, and destroying a context with a block still
    open is undefined.  :func:`OpenGL.error.end_abandoned_block` does both.  A
    toolkit that creates its own contexts calls it for context changes that do
    not go through :func:`make_current`.

    Imported on use instead of at module scope.  A process using only ES or
    EGL has no desktop GL block to close, and this module is loaded before any
    entry point is dispatched.
    """
    from OpenGL import error

    error.end_abandoned_block()


def make_current(handle):
    """Dispatch this thread through the table for ``handle``.

    Call this wherever the application makes a context current, so that each
    context in a process resolves and holds its own entry points.  ``handle``
    is the value ``OpenGL.platform.PLATFORM.GetCurrentContext()`` returns, in
    that platform's type: an ``int``, a ``c_void_p``, or a ctypes pointer such
    as GLX's ``GLXContext``.  ``None`` or a null pointer means no context.

    Call it under either implementation.  The C implementation dispatches
    through the named context's table from then on.  The ctypes implementation
    has no per-context tables, but uses this call to check errors in the new
    context.
    """
    global _ctypes_current_context

    _end_suspended_block()
    address = _as_address(handle)
    layer = _layer()
    if layer is not None:
        layer.make_current(address)
    else:
        _drop_unnamed_arming()
        _ctypes_current_context = address
    # Called before the offer.  The offer may arm this context and start
    # reading the flag itself; this call handles a context that arrives
    # unarmed.
    _follow_debug_output()
    offer_debug_output()


def forget_context(handle):
    """Retire the dispatch table for a destroyed context.

    The table is emptied and kept instead of freed.  ``make_current`` is per
    thread, so another thread may still point at the table.  Freeing it would
    be a use-after-free in a program with one window per thread.
    :func:`reclaim_retired` frees retired tables when the caller says no
    thread is using them.
    """
    _end_suspended_block()
    # Two stores are keyed by a context, with different keys: the dispatch
    # table by address, and `contextdata` by the handle object the platform
    # returned.  On platforms whose handle is an integer (WGL, CGL and EGL
    # here) the two are equal.  On platforms whose handle is an opaque pointer
    # (OSMesa, GLX) the address finds nothing in contextdata.  The destroyed
    # context's cached extension list would then pass to whichever context the
    # driver next gives that address.
    context = handle
    handle = _as_address(handle)
    if handle and handle in _installed_callbacks and handle == _current_context():
        # Remove our callback while the context still exists.  The driver
        # keeps the callback address until it is replaced, and a context is
        # destroyed holding its last callback.  The current context comes from
        # the driver instead of the record: nothing has been made current
        # since this context was destroyed, so the record still names it.
        use_debug_output(False)
    _offered.discard(handle)
    _installed_callbacks.pop(handle, None)
    with _identities_lock:
        # Keyed by address, which is what `context_identity` files it under.
        _identities.pop(handle, None)
    _forget_context_data(context)
    layer = _layer()
    if layer is not None:
        layer.forget_context(handle)
    else:
        _drop_unnamed_arming()
    # The context that was setting the flag may be the one that has just gone.
    _follow_debug_output()


#: The identity :func:`context_identity` returned for each context, by
#: address, until :func:`forget_context` reports that context destroyed.
_identities = {}
_identities_lock = threading.Lock()


class ContextIdentity:
    """One context for its lifetime; see :func:`context_identity`."""

    __slots__ = ('address', '__weakref__')

    def __init__(self, address):
        self.address = address

    def __repr__(self):
        return '<ContextIdentity for the context at 0x%x>' % (self.address,)


def context_identity():
    """Return an object representing the current context, or None.

    The object stays the same while the context lives.  After
    :func:`forget_context`, a context at the same address gets a new object.
    The handle alone cannot show this, because the driver reuses a destroyed
    context's address for the next context.  Buffers, textures and programs
    are numbered from 1 in each context.  Code holding one can store this
    identity beside the name and compare it before use.  That prevents using
    the name in another context, where the same number is a different object.

    Identities are only as accurate as the calls to :func:`forget_context`.
    If a context is destroyed without that call and another is created at the
    same address, the two share an identity.
    """
    address = _current_context()
    if not address:
        return None
    with _identities_lock:
        identity = _identities.get(address)
        if identity is None:
            identity = _identities[address] = ContextIdentity(address)
    return identity


def _forget_context_data(handle):
    """Drop the values cached about a context, as well as its dispatch table.

    A context's extension list and version are cached against its handle.
    The driver reuses handles, so a destroyed context and the next one can
    share one.  Without this, the new context reads the destroyed context's
    extension list.  Entry points gated on an extension only the new context
    has are then refused.

    Closing a window and opening another reuses handles, as does creating a
    GL context and then an OpenGL ES context.  For example,
    ``bool(glTexParameterIivEXT)`` returns False under an ES context that
    exports it, if a desktop GL context without it held the handle first.

    Only the cached description of the context is dropped.
    ``contextdata.cleanupContext`` also releases client array pointers, and its
    docstring warns that doing so while the driver may still read them causes
    a protection fault.  The cached query results belong to PyOpenGL and
    describe nothing the driver holds.

    Errors are suppressed.  This runs during context teardown, and a cleanup
    failure must not raise in the caller.
    """
    if not handle:
        return
    try:
        from OpenGL import contextdata
    except ImportError:                # pragma: no cover - interpreter shutdown
        return
    for storage in contextdata.STORAGES:
        try:
            held = storage.get(handle)
        except TypeError:
            # An unhashable handle, such as a bare ctypes pointer from a
            # caller's own binding.  Nothing is stored under it, because
            # `contextdata.setValue` raises the same TypeError, so there is
            # nothing to drop.
            return
        if not held:
            continue
        for key in [k for k in held if _describes_a_context(k)]:
            try:
                del held[key]
            except KeyError:           # pragma: no cover - raced with a cleanup
                pass


#: Keys under which a context's own description is cached: the queriers'
#: version and extension lists, keyed
#: ``('OpenGL.extensions', <kind>, <prefix>)`` one per API, and the per-name
#: results ``BasePlatform.checkExtension`` memoises under ``'extensions'``.
_CONTEXT_DESCRIPTION_KEY = 'OpenGL.extensions'


def _describes_a_context(key):
    """Return whether `key` names a value cached about a context.

    Other keys hold the caller's data, such as client array pointers the
    driver may still read.  ``contextdata.cleanupContext`` warns against
    dropping those, so only these keys are dropped.
    """
    if key == 'extensions':
        return True
    return isinstance(key, tuple) and key[:1] == (_CONTEXT_DESCRIPTION_KEY,)


def _drop_unnamed_arming():
    """Release debug output armed before the program named a context.

    Only the ctypes implementation records one.  It holds one binding for the
    process and has only the handles passed to :func:`make_current`.  A
    context armed before any such call is recorded under 0, which names no
    context.

    That record is stale once the program reports a change: a context
    destroyed, or another made current.  The context now current has never
    been given our callback, and a check reading a flag that nothing sets
    passes every call.  So the arming is released here and the next context
    gets a fresh offer, without waiting for the next audit.

    The compiled layer does not need this.  It reads the handle itself, so 0
    there means the platform reported no context.
    """
    if 0 not in _installed_callbacks:
        return
    _offered.discard(0)
    _release_debug_callback(0)


def reclaim_retired():
    """Free the tables of forgotten contexts and return how many were freed.

    A retired table uses about 43 KB and is unreachable.  A program with one
    or two contexts does not need this.  A program that opens and closes a
    context per document window over a long session accumulates retired
    tables, and calls this to free them.

    Only call this where no thread is still dispatching through a context this
    process has destroyed.  The caller knows whether that holds and PyOpenGL
    does not, so the caller asserts it by making this call.
    """
    layer = _layer()
    if layer is None:
        return 0
    return layer.reclaim_retired()


def set_error_checking(enable=True, entry_point=None):
    """Turn per-call error checking on or off, for one entry point or all.

    ``OpenGL.ERROR_CHECKING`` is read once, when the layer is configured.
    This function takes effect immediately and can apply to one entry point.
    It affects only the C implementation; under ctypes it does nothing.
    """
    layer = _layer()
    if layer is not None:
        layer.set_error_checking(bool(enable), entry_point)


#: GL_KHR_debug enums, so that turning the mechanism on needs no import from a
#: particular API module.
_DEBUG_OUTPUT = 0x92E0
_DEBUG_OUTPUT_SYNCHRONOUS = 0x8242
_DEBUG_SEVERITY_NOTIFICATION = 0x826B
_DEBUG_CALLBACK_FUNCTION = 0x8244
_DONT_CARE = 0x1100

#: The error checking modes, as :func:`error_checking_mode` names them.
DEBUG_OUTPUT, GET_ERROR, NOT_CHECKED = 'debug-output', 'get-error', 'off'

#: Context handles debug output has already been offered to, so that the offer
#: is made once per context rather than at every entry point resolved in it.
_offered = set()

#: Set while the offer runs.  Arming calls entry points, each of those
#: resolves, and resolving an entry point makes the offer.
_offering = False


def error_checking_mode():
    """Return how GL errors are detected in the current context.

    ``'debug-output'`` where the driver reports them through a
    ``GL_KHR_debug`` callback and the check reads the flag it sets,
    ``'get-error'`` where the check calls ``glGetError``, and ``'off'`` where
    errors are not checked.
    """
    from OpenGL import _configflags

    if not _configflags.ERROR_CHECKING:
        return NOT_CHECKED
    layer = _layer()
    if layer is None:
        return _ctypes_checking_mode()
    return DEBUG_OUTPUT if layer.error_mode() else GET_ERROR


def _ctypes_checking_mode():
    """Return the mode the ctypes implementation's error checker uses."""
    checker = _ctypes_error_checker()
    if checker is None or not checker:
        return NOT_CHECKED
    return DEBUG_OUTPUT if getattr(checker, 'readsDebugOutput', False) else GET_ERROR


def _ctypes_error_checker():
    """Return the desktop GL error checker, or None if none has been built.

    Read from ``sys.modules`` instead of imported.  A process that has never
    imported desktop GL has no checker, and importing one would load a driver.
    """
    module = sys.modules.get('OpenGL.raw.GL._errors')
    return getattr(module, '_error_checker', None) if module else None


def _has_current_context():
    """Return whether the platform reports a current context.

    Returns True where the platform cannot report.  The ctypes implementation
    assumes that code calling GL has a context, and returning False here would
    decline the offer permanently on such a platform.
    """
    from OpenGL import platform

    try:
        return bool(platform.PLATFORM.CurrentContextIsValid())
    except Exception:  # noqa: BLE001 a platform with no way to ask fails in its own way  # pragma: no cover
        return True


def _current_context():
    """Return the current context's address, or None if the platform cannot say.

    :func:`_context_key` returns the handle last passed to
    :func:`make_current`.  Callbacks are filed under that key, and it is all
    the ctypes implementation has.  The two differ after a context is
    destroyed.  Nothing is made current after it, so the record still names
    it while the driver reports none.

    Returns None instead of 0 where the platform cannot report.  The caller
    is deciding whether to call GL, and either guess would be wrong.
    :func:`_has_current_context` returns True in that case, because its
    caller is deciding whether to make the offer and would otherwise decline
    permanently.
    """
    from OpenGL import platform

    try:
        return _as_address(platform.PLATFORM.GetCurrentContext())
    except Exception:  # noqa: BLE001 each platform plugin fails in its own way where it cannot say
        return None


def _debug_output_wanted():
    """Return whether the layer should offer debug output to contexts.

    Setting ``OpenGL.ERROR_DEBUG_OUTPUT = False`` before the first call turns
    it off for the process.  Use this in a program that installs its own
    ``GL_KHR_debug`` callback, or that must not put the driver into
    synchronous debug output.
    """
    from OpenGL import _configflags

    return bool(_configflags.ERROR_CHECKING and _configflags.ERROR_DEBUG_OUTPUT)


def offer_debug_output():
    """Switch the current context to debug-output error checking, once.

    Called from entry-point resolution, the first point at which a context
    exists.  Later calls for the same context do nothing.  The context is
    recorded as offered whether or not it accepted, so a context without
    ``GL_KHR_debug`` is only tried once.

    This must not run inside a ``glBegin`` block.  No GL query is legal there,
    ``glEnable`` included, and immediate-mode entry points are first resolved
    inside one.
    """
    global _offering

    from OpenGL import error

    if _offering or not _debug_output_wanted():
        return
    if error.inside_begin_block():
        return
    handle = _context_key()
    if handle in _offered:
        return
    if not _has_current_context():
        # No context to offer to.  Entry points can be resolved with no
        # context, for example by a probe of what a platform supports, or by
        # a cleanup handler after the window has closed.  The GL calls that
        # arm debug output would then run with no context.  The recorded
        # handle does not prove a context exists: it is the value make_current
        # last received, and that context may have been destroyed.
        return
    _offering = True
    try:
        _offered.add(handle)
        use_debug_output(True)
    finally:
        _offering = False

#: The live callback per context handle.  A dict instead of a list, because
#: each reference must last until its context releases the callback and no
#: longer.  Keeping every callback ever made would hold one per context for
#: the life of the process.
_installed_callbacks = {}


def debug_output_available():
    """Return whether the current context can report errors via GL_KHR_debug."""
    layer = _layer()
    if layer is None:
        from OpenGL.GL import glDebugMessageCallback

        return bool(glDebugMessageCallback)
    from OpenGL._dispatch import entry_points

    proc = entry_points.get(('GL', 'glDebugMessageCallback'))
    return bool(proc) if proc is not None else False


def use_debug_output(enable=True):
    """Use GL_KHR_debug callbacks instead of a ``glGetError`` per call.

    Polling ``glGetError`` is expensive, often as costly as the call it
    checks, and it introduces a stall.  Most current implementations support
    ``GL_KHR_debug``, which calls a callback only when there is something to
    report.  The check after each call then reads the flag that callback set.
    Callers see the same behaviour either way.  ``OpenGL.ERROR_CHECKING`` and
    :func:`set_error_checking` still choose which entry points are checked.
    The same exception is raised from the same call, with the same GL error
    code.

    Both implementations use it.  A context that supports ``GL_KHR_debug``
    gets it by default, so programs mostly call this to turn it off.  Turning
    it off removes the callback and restores the driver state for the current
    context.  Synchronous debug output serialises the driver, and turning it
    off removes that cost.

    Returns True when the change took effect.  Turning it on needs a context
    that supports ``GL_KHR_debug`` and has no other callback installed.
    Otherwise checking stays on ``glGetError``.
    """
    from OpenGL.GL import (
        glDebugMessageCallback,
        glDebugMessageControl,
        glDisable,
        glEnable,
    )

    key = _context_key()
    # On or off, the program has now chosen for this context.  The automatic
    # offer applies only to contexts with no explicit choice, and must not
    # override one.  Without this, ``use_debug_output(False)`` lasts only
    # until the next entry point is resolved.
    _offered.add(key)
    if not enable:
        if _release_debug_callback(key):
            glDisable(_DEBUG_OUTPUT_SYNCHRONOUS)
            glDisable(_DEBUG_OUTPUT)
            # A null GLDEBUGPROC instead of None.  The ctypes binding is
            # declared to take one and refuses anything else, and the C
            # implementation passes the driver a null pointer for None.
            glDebugMessageCallback(_debug_callback_type()(), None)
        return True
    if not debug_output_available():
        return False

    callback = _our_callback()
    if _foreign_callback_installed(key, _callback_address(callback)):
        # The application uses GL_KHR_debug itself.  Installing our callback
        # would remove its debug output, and its next glDebugMessageCallback
        # would remove our error checking, with neither side detecting the
        # change.  So the context keeps glGetError.
        return False
    glEnable(_DEBUG_OUTPUT)
    # Synchronous, because the callback has to run during the call it belongs
    # to for the error to be attributed to the right entry point.
    glEnable(_DEBUG_OUTPUT_SYNCHRONOUS)
    glDebugMessageCallback(callback, None)
    # The callback handles only errors.  Disabling notifications saves the
    # driver formatting them.
    glDebugMessageControl(
        _DONT_CARE, _DONT_CARE, _DEBUG_SEVERITY_NOTIFICATION, 0, None, False
    )
    # Holds the reference the driver calls through, for as long as that
    # context has it installed.  Recorded before the checker switches over,
    # because checking depends on it from then on.
    _installed_callbacks[key] = callback
    if key:
        # A context armed before it had a handle was recorded under 0.  The
        # record under the real handle replaces it.  Keeping both would mean
        # two contexts to disarm, one of which does not exist.
        _installed_callbacks.pop(0, None)
        _offered.discard(0)
    _start_reading_debug_output()
    return True


def _follow_debug_output():
    """Read the flag only while the context that sets it is current.

    The driver installs callbacks per context, but the ctypes error checker is
    one object for the whole process.  A context without our callback never
    sets the flag.  A checker reading the flag in that context finds no
    errors.  Every ``GLError`` the driver reports is lost, and the failing
    call returns as if it had succeeded.

    :func:`_release_debug_callback` does not cover this.  It returns to
    ``glGetError`` only once no context holds a callback.  That is correct
    for the context releasing one, but ignores which context is now current.

    The Windows offscreen path does this in normal use.
    ``OpenGL.WGL.offscreen`` creates a bootstrap context to resolve entry
    points, makes it current, arms it, then restores the previous context.
    Without this function, the checker keeps reading the flag for the
    bootstrap context, which nothing draws in, and every real context goes
    unchecked.

    The compiled layer stores the mode in each context's dispatch table, so
    the mode follows the current context and this function does nothing.
    """
    global _reading_debug_output

    if _layer() is not None:
        return
    wanted = _context_key() in _installed_callbacks
    if wanted == _reading_debug_output:
        # No change.  ``make_current`` runs on every context switch, and
        # re-pointing the checker at its current reader would cost work on
        # each switch.
        return
    _reading_debug_output = wanted
    if wanted:
        _start_reading_debug_output()
    else:
        _stop_reading_debug_output()


#: Whether the ctypes checker reads the flag instead of calling glGetError.
#: :func:`_follow_debug_output` re-points the checker only when this changes.
#: The two functions that re-point the checker keep this value accurate.
_reading_debug_output = False


def _context_key():
    """Return the key installed callbacks are recorded under.

    The C implementation tracks the current context and returns its handle.
    The ctypes implementation holds one binding per process and does no
    context tracking.  It returns the handle last passed to
    :func:`make_current`, or 0 before the first call.
    """
    layer = _layer()
    if layer is not None:
        return layer.current_handle()
    return _ctypes_current_context


#: The handle last passed to :func:`make_current` under ctypes.  See
#: :func:`_context_key`.
_ctypes_current_context = 0


def _our_callback():
    """Return the ``GLDEBUGPROC`` to install for the active implementation.

    The C implementation's callback is a C function that sets a thread-local
    flag the stub reads, so no Python runs during the driver's call.  The
    ctypes implementation's callback is a Python function.  It runs only when
    the driver reports an error, so the check on the normal path is still a
    flag read.
    """
    layer = _layer()
    if layer is not None:
        address = layer.debug_callback_address()
        return ctypes.cast(ctypes.c_void_p(address), _debug_callback_type())
    global _ctypes_callback
    if _ctypes_callback is None:
        _ctypes_callback = _debug_callback_type()(_ctypes_debug_callback)
    return _ctypes_callback


#: The ctypes implementation's callback, built once.  The driver holds its
#: address, so it must outlive every context that uses it.
_ctypes_callback = None

#: GL_DEBUG_TYPE_ERROR.  Messages of other types report performance or
#: portability issues and are not raised.
_DEBUG_TYPE_ERROR = 0x824C

#: Per thread, because the thread that makes a call also checks it.
_ctypes_pending = threading.local()


def _ctypes_debug_callback(source, type_, id_, severity, length, message, user):
    """Record a pending error reported by the driver, on the ctypes path."""
    if type_ == _DEBUG_TYPE_ERROR:
        _ctypes_pending.pending = True


#: In a context checking through the callback, one glGetError per this many
#: calls.  See :func:`_read_debug_error`; the C implementation audits on the
#: same interval.
AUDIT_INTERVAL = 64

_audit_countdown = AUDIT_INTERVAL


def _read_debug_error():
    """Return the error code for the call just made, using the callback flag.

    Installed as the ctypes error checker's error reader while debug output
    is in use.  ``glGetError`` is called when the callback has set the flag,
    where an exception is about to be raised, and once every
    :data:`AUDIT_INTERVAL` calls.

    The periodic audit catches a context that no longer sets the flag.  An
    unset flag looks the same as a context with no errors.  A program can
    destroy a context and make another current without calling
    :func:`forget_context` or :func:`make_current`.  So the driver is checked
    every :data:`AUDIT_INTERVAL` calls.  If that check finds an error, the
    context goes back to a ``glGetError`` per call.
    """
    global _audit_countdown

    checker = _ctypes_error_checker()
    if checker is None:  # pragma: no cover - no desktop GL in this process
        return 0
    if getattr(_ctypes_pending, 'pending', False):
        _ctypes_pending.pending = False
        return int(checker.baseGetErrors())
    _audit_countdown -= 1
    if _audit_countdown > 0:
        return 0
    _audit_countdown = AUDIT_INTERVAL
    code = int(checker.baseGetErrors())
    if code:
        _stop_reading_debug_output()
    return code


def _start_reading_debug_output():
    """Point the implementation's error check at the flag the callback sets."""
    global _reading_debug_output

    _reading_debug_output = True
    layer = _layer()
    if layer is not None:
        layer.set_error_mode(1)
        return
    checker = _ctypes_error_checker()
    if checker is not None:
        checker.setErrorReader(_read_debug_error)


def offer_on_first_check(checker):
    """Make the ctypes error checker run the offer on its first check.

    The ctypes implementation has no resolution hook for the offer, and at
    import there is no context.  The first check is the first point where a
    context exists.  GL calls are safe right after a check, because the call
    being checked has completed.

    After the first check this costs nothing per call.  The bootstrap reader
    replaces itself with the reader the offer chose.  Each later check is a
    flag read or a ``glGetError``, with no test of whether the offer was made.
    """

    def bootstrap():
        checker.setErrorReader(None)
        offer_debug_output()
        return checker._getErrors()

    checker.setErrorReader(bootstrap)


def _stop_reading_debug_output():
    """Go back to a glGetError per call."""
    global _reading_debug_output

    _reading_debug_output = False
    layer = _layer()
    if layer is not None:
        layer.set_error_mode(0)
        return
    checker = _ctypes_error_checker()
    if checker is not None:
        checker.setErrorReader(None)


def _release_debug_callback(key):
    """Release ``key``'s callback and stop reading the flag it set.

    Which contexts stop reading depends on where the mode is stored.  The C
    implementation stores it in the context's table, so only this context
    changes.  The ctypes implementation has one checker for the process.  It
    returns to ``glGetError`` only once no context holds a callback.
    Returning earlier would leave every other context paying for synchronous
    debug output while reading neither its flag nor its own errors.

    Returns whether ``key`` had a callback to release.
    """
    held = _installed_callbacks.pop(key, None) is not None
    if _layer() is None and _installed_callbacks:
        return held
    _stop_reading_debug_output()
    return held


def _debug_callback_type():
    from OpenGL.raw.GL._types import GLDEBUGPROC

    return GLDEBUGPROC


def _foreign_callback_installed(key, ours):
    """Return whether this context already has another debug callback.

    Checked before installing, because ``glDebugMessageCallback`` holds one
    callback per context, and a second call replaces the first.  A context
    with a callback already belongs to a program using ``GL_KHR_debug``
    itself.  Replacing it would silence the program's diagnostics, and the
    program's next call would silence our error checking.
    """
    from OpenGL.GL import glGetPointerv

    try:
        address = _as_address(glGetPointerv(_DEBUG_CALLBACK_FUNCTION))
    except Exception:  # noqa: BLE001 a context that will not answer fails in its own way  # pragma: no cover
        # Without an answer there is no reason to decline.  Declining on
        # every failure would mean no context ever got debug-output checking.
        return False
    if not address:
        return False
    if address == ours:
        return False
    # Ours from an earlier enable in this same context, seen again.
    previous = _installed_callbacks.get(key)
    return previous is None or address != _callback_address(previous)


def _callback_address(callback):
    """Return the address the driver receives for a ctypes callback object."""
    return ctypes.cast(callback, ctypes.c_void_p).value


def _as_address(value):
    """Return a pointer as a plain integer, whatever type it arrived as.

    Two sources produce these values.  Context handles come from the
    platform, whose getter returns the type its API declares.  That is
    ``c_void_p`` on WGL and CGL, which arrives as an ``int``, and
    ``GLXContext`` on GLX, a ctypes pointer to an opaque struct.  Callback
    addresses come from ``glGetPointerv`` through the active array handler.
    That is a numpy scalar where numpy is installed, a ctypes pointer where it
    is not, and a one-element array holding either where
    ``SIZE_1_ARRAY_UNPACK`` is off.  If that array were read as zero, PyOpenGL
    would conclude no application callback is installed and replace the
    application's callback.

    Each type is checked explicitly instead of being passed to ``int()``.
    ``int()`` parses any object offering the buffer protocol as a string of
    digits, and every ctypes object offers one.  A pointer passed to ``int()``
    fails with an error about an invalid number instead of a type error.
    Where every byte of the address is an ASCII digit, ``int()`` returns a
    wrong value.
    """
    if value is None:
        return 0
    # A one-element array holding the pointer.  Checked by length instead of
    # by indexing: indexing a ctypes pointer dereferences it and reads memory
    # instead of raising.
    if hasattr(value, '__len__') and len(value) == 1:
        value = value[0]
        if value is None:
            return 0
    # An integer, or an object convertible to one, such as a numpy scalar.
    if hasattr(value, '__index__'):
        return int(value)
    # A pointer-sized scalar whose value is the address: c_void_p, and WGL's
    # HGLRC and HDC.  These are declared as simple types instead of pointer
    # classes.  ctypes shares every reference to c_void_p, and a shared one
    # would disable the array machinery for every other use.  So neither
    # ``isinstance`` against a pointer class nor ``ctypes.cast`` recognises
    # them.  ``OpenGL._dispatch.support.is_pointer_sized`` states the same
    # rule for the C layer.
    if (isinstance(value, ctypes._SimpleCData)
            and getattr(type(value), '_type_', None) == 'P'):
        return value.value or 0
    try:
        return ctypes.cast(value, ctypes.c_void_p).value or 0
    except ctypes.ArgumentError:  # pragma: no cover - an answer we cannot read
        return 0
