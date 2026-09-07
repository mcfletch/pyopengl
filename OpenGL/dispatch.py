"""Which implementation is running the entry points, and control of it.

PyOpenGL dispatches through one of two implementations.  The C one is
generated from the Khronos registry and compiled, so it ships in
``PyOpenGL_accelerate`` and runs where that is installed under CPython; the
ctypes one is pure Python and runs everywhere else.  Both implement the same
API, so a program need not care which it has -- until it does, and then this
is where to ask::

    >>> from OpenGL import dispatch
    >>> dispatch.active()
    'c'
    >>> dispatch.status()
    Status(requested='c', active='c', available=True, reason=None)

The extension is optional and its absence is not an error: asking for the C
implementation where none was built leaves the ctypes one in place and says
nothing.  A program or a test suite that means to be *on* the C implementation
therefore has to ask, and :func:`status` says why it is not where it is not.

The rest of the module is the dispatch layer's own controls.  Under the C
implementation each context holds its own function pointer for every entry
point, so a process with two contexts of differing capability resolves each of
them correctly; :func:`make_current` says a context has become current and
:func:`forget_context` that one has been destroyed.  Both are worth calling
under either implementation, because both decide which context PyOpenGL checks
errors in.

Error checking is the other half.  A context that offers ``GL_KHR_debug`` is
given the cheaper of the two mechanisms without being asked -- the driver
reports an error through a callback during the call, so the check is a flag
read rather than a ``glGetError`` round trip -- and
:func:`error_checking_mode` says which one a context ended up with.
"""

import ctypes
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
    'reclaim_retired',
    'set_error_checking',
    'error_checking_mode',
    'use_debug_output',
    'debug_output_available',
    'offer_debug_output',
]


class Status(NamedTuple):
    """What was asked for, what is running, and why they differ."""

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

    Read out of ``sys.modules`` rather than imported.  The extension is 13 MB
    and nothing imports it on the ctypes path, so a program that calls
    :func:`make_current` there -- as it should, unconditionally -- must not be
    the thing that loads it.  Where it is not loaded it is not installed
    either, since installing is what loads it.
    """
    module = sys.modules.get('OpenGL._dispatch')
    if module is None or not module.ACTIVE:
        return None
    return module._c


def requested():
    """Which implementation the configuration asks for: ``'c'`` or ``'ctypes'``.

    ``PYOPENGL_DISPATCH`` names one directly.  Unset, it is ``'c'`` on CPython
    and ``'ctypes'`` on every other interpreter, which is where the extension
    is not built.  ``OpenGL.USE_ACCELERATE = False`` and ``OpenGL.FULL_LOGGING``
    each ask for ctypes as well; :func:`status` says which of them did.
    """
    from OpenGL import _configflags

    if _configflags.DISPATCH == 'c' and _configflags.USE_ACCELERATE:
        return 'c'
    return 'ctypes'


def active():
    """Which implementation the entry points built so far dispatch through.

    The choice is made when the first entry point is built, so this answers
    ``'ctypes'`` in a process that has imported nothing from ``OpenGL.GL`` yet
    however it is configured.  :func:`settle` makes the choice rather than
    reporting it, for a caller that has to ask first.
    """
    return 'ctypes' if _layer() is None else 'c'


def available():
    """Whether the compiled layer is installed and importable.

    Answered from the module where it has already been loaded, and from the
    import system where it has not, so asking does not load 13 MB of extension
    to find out that it exists.
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
    """Choose the implementation now, and say which it is.

    The first entry point built would otherwise make this choice, and it reads
    ``OpenGL.ERROR_CHECKING`` and its neighbours as it does -- so call this
    *after* setting them, exactly as one would import ``OpenGL.GL`` after
    setting them.

    For a caller that has to know before it has anything to draw with: a test
    suite whose whole point is the C implementation, or a program that means to
    fail rather than run several times slower than it planned to.
    """
    if requested() != 'c':
        return 'ctypes'
    try:
        from OpenGL import _dispatch
    except ImportError:  # pragma: no cover - depends on what is installed
        return 'ctypes'
    return 'c' if _dispatch.install() else 'ctypes'


def status():
    """What was asked for, what is running, and why they differ.

    The reason is a sentence naming the switch or the absence responsible, for
    a caller to put in the message it raises::

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
    """End the glBegin block, if any, error checking is suspended for.

    A Begin/End block belongs to the context it was opened in, so a context
    change ends it.  That matters because ``glEnd`` is otherwise the only thing
    that turns checking back on, and an exception raised between the two -- a
    bad vertex, an entry point the driver does not export -- means ``glEnd``
    never runs and every later call in the process goes unchecked.

    Reads ``sys.modules`` rather than importing: a process using only ES or EGL
    has no desktop-GL checker to resume, and importing one to find that out
    would load a driver to answer a question about a block it cannot have
    opened.  The compiled layer keeps the same switch of its own, which
    ``make_current`` and ``forget_context`` clear for themselves.
    """
    module = sys.modules.get('OpenGL.raw.GL._errors')
    checker = getattr(module, '_error_checker', None) if module else None
    if checker is not None:
        checker.onEnd()


def make_current(handle):
    """Dispatch this thread through the table for ``handle``.

    Call this wherever the application makes a context current, so that N
    contexts in one process each resolve and hold their own entry points.  The
    handle is the one ``OpenGL.platform.PLATFORM.GetCurrentContext()`` returns.

    It is worth calling under either implementation.  The C one dispatches
    through the named context's table from here on; the ctypes one has no
    per-context tables to switch, but this is how it learns that error checking
    belongs to a different context now.
    """
    global _ctypes_current_context

    _end_suspended_block()
    layer = _layer()
    if layer is not None:
        layer.make_current(int(handle or 0))
    else:
        _drop_unnamed_arming()
        _ctypes_current_context = int(handle or 0)
    offer_debug_output()


def forget_context(handle):
    """Retire the dispatch table for a context that has been destroyed.

    The table is emptied and set aside rather than freed: ``make_current`` is
    per thread, so a thread that never noticed the context go still points at
    it, and freeing here would be a use-after-free in the ordinary shape of a
    program with a window per thread.  :func:`reclaim_retired` frees the set
    aside ones at a moment the caller says is quiet.
    """
    _end_suspended_block()
    handle = int(handle or 0)
    if handle in _installed_callbacks and handle == _context_key():
        # Take our callback back out while there is still a context to take it
        # out of.  The driver holds the address until something replaces it,
        # and a context is destroyed with whatever it was last given.
        use_debug_output(False)
    _offered.discard(handle)
    _installed_callbacks.pop(handle, None)
    _forget_context_data(handle)
    layer = _layer()
    if layer is not None:
        layer.forget_context(handle)
    else:
        _drop_unnamed_arming()


def _forget_context_data(handle):
    """Drop what is cached *about* a context, as well as its dispatch table.

    A context's extension list and version are cached against its handle, and a
    handle is an address the driver hands out again -- a destroyed context and
    the next one can share it.  The dispatch table is retired here already; the
    caches were not, so the new context read the dead one's extension list and
    every entry point gated on an extension only the new one has was refused.

    That is not a rare shape: a program that closes a window and opens another,
    or one that makes a GL context and then an OpenGL-ES context, hits it.  It
    surfaced as `bool(glTexParameterIivEXT)` answering False under an ES
    context that exports it, because a desktop-GL context had held the handle
    first and had not.

    Only what *describes* the context, and not everything held against it:
    ``contextdata.cleanupContext`` releases the client array pointers too, and
    its own docstring warns that doing so while the driver may still be reading
    them is a protection fault.  The queriers' answers are ours and describe
    nothing the driver holds.

    Best effort: this runs while a context is being torn down, and a failure to
    tidy up must not become the caller's exception.
    """
    if not handle:
        return
    try:
        from OpenGL import contextdata
    except ImportError:                # pragma: no cover - interpreter shutdown
        return
    for storage in contextdata.STORAGES:
        held = storage.get(handle)
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
#: answers ``BasePlatform.checkExtension`` memoises under ``'extensions'``.
_CONTEXT_DESCRIPTION_KEY = 'OpenGL.extensions'


def _describes_a_context(key):
    """Whether `key` names something cached *about* a context.

    Everything else held against a context is the caller's -- client array
    pointers the driver may still be reading -- and dropping those is what
    ``contextdata.cleanupContext`` warns about, so only these go.
    """
    if key == 'extensions':
        return True
    return isinstance(key, tuple) and key[:1] == (_CONTEXT_DESCRIPTION_KEY,)


def _drop_unnamed_arming():
    """Give up an arming made before the program named a context.

    Only the ctypes implementation records one.  It holds a single binding for
    the process and knows only what :func:`make_current` told it, so a context
    it armed while it had been told nothing is recorded under 0 -- which says
    "we were not told", and names no context.

    That record stops describing anything the moment the program says the
    situation has changed.  A context has gone, or another is current; either
    way the driver now answering has never been given our callback, and a check
    reading a flag nothing sets is a check that passes everything.  So the
    arming is given up here and the next context is offered afresh, rather than
    waiting for the audit to notice at its own pace.

    The compiled layer needs none of this: it reads the handle itself, so 0
    there is a context that genuinely had none to give.
    """
    if 0 not in _installed_callbacks:
        return
    _offered.discard(0)
    _release_debug_callback(0)


def reclaim_retired():
    """Free the tables of contexts that have been forgotten; returns how many.

    A retired table costs about 43 KB and is unreachable, so a program with one
    or two contexts need never call this.  A program that opens and closes a
    context per document window over a long session accumulates them, and this
    is how it says they can go.

    **Only call this where no thread is still dispatching through a context
    this process has destroyed** -- that is the judgement retirement exists to
    avoid making on the caller's behalf, and nothing here can make it.
    """
    layer = _layer()
    if layer is None:
        return 0
    return layer.reclaim_retired()


def set_error_checking(enable=True, entry_point=None):
    """Turn per-call error checking on or off, for one entry point or all.

    Unlike ``OpenGL.ERROR_CHECKING``, which is read once when the layer is
    configured, this takes effect immediately and can be scoped to a single
    entry point.  It is the C implementation's; under ctypes it does nothing.
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

#: The two mechanisms, as :func:`error_checking_mode` names them.
DEBUG_OUTPUT, GET_ERROR, NOT_CHECKED = 'debug-output', 'get-error', 'off'

#: Context handles debug output has already been offered to, so that the offer
#: is made once per context rather than at every entry point resolved in it.
_offered = set()

#: Set while the offer is running, because arming calls entry points and each
#: of those resolves, which is what makes the offer in the first place.
_offering = False


def error_checking_mode():
    """How GL errors are being noticed in the current context.

    ``'debug-output'`` where the driver reports them through a
    ``GL_KHR_debug`` callback and the check is a read of the flag it sets,
    ``'get-error'`` where the check is a ``glGetError`` round trip, and
    ``'off'`` where nothing is checked at all.
    """
    from OpenGL import _configflags

    if not _configflags.ERROR_CHECKING:
        return NOT_CHECKED
    layer = _layer()
    if layer is None:
        return _ctypes_checking_mode()
    return DEBUG_OUTPUT if layer.error_mode() else GET_ERROR


def _ctypes_checking_mode():
    """The mechanism the ctypes implementation's error checker is using."""
    checker = _ctypes_error_checker()
    if checker is None or not checker:
        return NOT_CHECKED
    return DEBUG_OUTPUT if getattr(checker, 'readsDebugOutput', False) else GET_ERROR


def _ctypes_error_checker():
    """The desktop-GL error checker, where one has been built.

    Read out of ``sys.modules`` for the reason :func:`_end_suspended_block`
    gives: a process that has never imported desktop GL has no checker, and
    importing one to find that out would load a driver.
    """
    module = sys.modules.get('OpenGL.raw.GL._errors')
    return getattr(module, '_error_checker', None) if module else None


def _has_current_context():
    """Whether the platform says a context is current, where it can say.

    A platform that cannot tell answers True: the ctypes implementation has
    always assumed a caller calling GL means to have a context, and a guess of
    "no" here would decline the offer forever on such a platform.
    """
    from OpenGL import platform

    try:
        return bool(platform.PLATFORM.CurrentContextIsValid())
    except Exception:  # pragma: no cover - a platform with no way to ask
        return True


def _debug_output_wanted():
    """Whether the layer should offer debug output to a context at all.

    ``OpenGL.ERROR_DEBUG_OUTPUT = False`` before the first call declines it for
    the process, for a program that installs its own ``GL_KHR_debug`` callback
    or does not want the driver put into synchronous debug output.
    """
    from OpenGL import _configflags

    return bool(_configflags.ERROR_CHECKING and _configflags.ERROR_DEBUG_OUTPUT)


def offer_debug_output():
    """Give the current context the cheaper error check, once.

    Called from entry-point resolution, which is the first moment a context
    exists to be offered anything.  Everything about it is a no-op the second
    time: the context is recorded as offered whether or not it accepted, so a
    context that has no ``GL_KHR_debug`` is asked once and never again.

    A ``glBegin`` block is the one place this must not run.  No GL query is
    legal inside one, ``glEnable`` included, and an immediate-mode entry point
    is first resolved from exactly there.
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
    if not handle and not _has_current_context():
        # Nothing to offer anything to.  Entry points are resolved before a
        # context exists -- a probe for what a platform has, a cleanup handler
        # after the window has gone -- and the GL calls that arm debug output
        # would be made into no context at all.
        return
    _offering = True
    try:
        _offered.add(handle)
        use_debug_output(True)
    finally:
        _offering = False

#: The live callback per context handle.  A dict rather than a list because the
#: reference has to outlive the enabling call and no longer: keeping every one
#: ever made would hold a callback per context for the life of the process.
_installed_callbacks = {}


def debug_output_available():
    """Whether the current context reports errors through GL_KHR_debug."""
    layer = _layer()
    if layer is None:
        from OpenGL.GL import glDebugMessageCallback

        return bool(glDebugMessageCallback)
    from OpenGL._dispatch import entry_points

    proc = entry_points.get(('GL', 'glDebugMessageCallback'))
    return bool(proc) if proc is not None else False


def use_debug_output(enable=True):
    """Notice GL errors through GL_KHR_debug rather than a glGetError per call.

    A per-call ``glGetError`` is a driver round trip and it is the whole cost of
    error checking.  With this on, the driver reports an error through a
    callback during the call itself, and the check afterwards is a read of the
    flag that callback set.  What a caller sees does not change: the same entry
    points are checked -- ``OpenGL.ERROR_CHECKING`` and :func:`set_error_checking`
    decide that either way -- and the same exception is raised from the same
    call, carrying the same GL error code.

    Both implementations use it, and a context that offers ``GL_KHR_debug`` is
    offered it without being asked, so this is mostly how a program turns it
    *off*.  Switching it off undoes what switching it on did for *this*
    context, callback and driver state together: synchronous debug output
    serialises the driver, which is the cost the switch exists to stop paying.

    Returns True when it took effect.  It needs a context offering
    ``GL_KHR_debug`` and no other callback installed in it; where either is
    missing, checking stays the ``glGetError`` round trip it was.
    """
    from OpenGL.GL import (
        glDebugMessageCallback,
        glDebugMessageControl,
        glDisable,
        glEnable,
    )

    key = _context_key()
    # Asked for either way, this context is decided: the offer is what happens
    # to a context nobody has said anything about, and it must not undo a
    # program that has.  Without this a program's ``use_debug_output(False)``
    # lasts until the next entry point it resolves.
    _offered.add(key)
    if not enable:
        if _release_debug_callback(key):
            glDisable(_DEBUG_OUTPUT_SYNCHRONOUS)
            glDisable(_DEBUG_OUTPUT)
            # A null GLDEBUGPROC rather than None: the ctypes binding is
            # declared to take one and refuses anything else, and it is what
            # the C implementation passes the driver for None in any case.
            glDebugMessageCallback(_debug_callback_type()(), None)
        return True
    if not debug_output_available():
        return False

    callback = _our_callback()
    if _foreign_callback_installed(key, _callback_address(callback)):
        # The application is using GL_KHR_debug itself.  Installing over its
        # callback would take its debug output away, and its next
        # glDebugMessageCallback would take our error checking away without
        # either of us noticing -- so the context keeps glGetError.
        return False
    glEnable(_DEBUG_OUTPUT)
    # Synchronous, because the callback has to run during the call it belongs
    # to for the error to be attributed to the right entry point.
    glEnable(_DEBUG_OUTPUT_SYNCHRONOUS)
    glDebugMessageCallback(callback, None)
    # Notifications are chatter; the callback only cares about errors, and not
    # asking for the rest keeps the driver from formatting them.
    glDebugMessageControl(
        _DONT_CARE, _DONT_CARE, _DEBUG_SEVERITY_NOTIFICATION, 0, None, False
    )
    # The callback holds the reference the driver will call through, for as
    # long as that context has it installed.  Recorded before the switch,
    # because from the switch onwards the checking depends on it.
    _installed_callbacks[key] = callback
    if key:
        # A context armed before anything could name it was recorded under 0.
        # Naming it now supersedes that: it is one context, armed once, and
        # two records of it would be two contexts to disarm and one that never
        # existed.
        _installed_callbacks.pop(0, None)
        _offered.discard(0)
    _start_reading_debug_output()
    return True


def _context_key():
    """What the installed callbacks are recorded against.

    The C implementation knows which context is current and says so.  The
    ctypes implementation cannot: it holds one binding per process and has no
    context tracking of its own, so what it has is what the program last told
    :func:`make_current`, and 0 until it says anything.
    """
    layer = _layer()
    if layer is not None:
        return layer.current_handle()
    return _ctypes_current_context


#: The context the ctypes implementation was last told about.  See
#: :func:`_context_key`.
_ctypes_current_context = 0


def _our_callback():
    """The ``GLDEBUGPROC`` to install for this implementation.

    The C one is a C function that sets a thread-local flag the stub reads --
    no Python runs during the driver's call.  The ctypes one has to be a Python
    callback, which is the same trade the ctypes implementation makes
    everywhere: it runs only when the driver reports an error, and the check on
    the ordinary path stays a flag read.
    """
    layer = _layer()
    if layer is not None:
        address = layer.debug_callback_address()
        return ctypes.cast(ctypes.c_void_p(address), _debug_callback_type())
    global _ctypes_callback
    if _ctypes_callback is None:
        _ctypes_callback = _debug_callback_type()(_ctypes_debug_callback)
    return _ctypes_callback


#: The ctypes implementation's callback, built once: the driver is given its
#: address, so it has to outlive every context that holds it.
_ctypes_callback = None

#: GL_DEBUG_TYPE_ERROR.  A message of any other type is the driver being
#: helpful about performance or portability, not an error to raise.
_DEBUG_TYPE_ERROR = 0x824C

#: Per thread, because the call the error belongs to was made by one thread and
#: is checked by that thread.
_ctypes_pending = threading.local()


def _ctypes_debug_callback(source, type_, id_, severity, length, message, user):
    """What the driver calls during a failing call, on the ctypes path."""
    if type_ == _DEBUG_TYPE_ERROR:
        _ctypes_pending.pending = True


#: One glGetError per this many calls, in a context that is checking through
#: the callback.  See :func:`_read_debug_error`; the C implementation audits
#: itself on the same interval.
AUDIT_INTERVAL = 64

_audit_countdown = AUDIT_INTERVAL


def _read_debug_error():
    """The error code for the call just made, without a round trip per call.

    Installed as the ctypes error checker's source of error codes while debug
    output is in use.  The round trip happens where the callback says there is
    something to fetch -- which is where an exception is about to be raised
    anyway -- and once every :data:`AUDIT_INTERVAL` calls besides.

    The audit is what makes the flag trustworthy.  A flag that is never set
    looks exactly like a context with nothing wrong, and a context can stop
    being ours without saying so: the ctypes implementation has no way to
    notice a program destroying a context and making another current.  So the
    driver is asked anyway, rarely, and a context that turns out to be
    reporting elsewhere goes back to a ``glGetError`` per call.
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
    layer = _layer()
    if layer is not None:
        layer.set_error_mode(1)
        return
    checker = _ctypes_error_checker()
    if checker is not None:
        checker.setErrorReader(_read_debug_error)


def offer_on_first_check(checker):
    """Have the ctypes error checker make the offer when it first checks.

    The ctypes implementation has no resolution callback to hang this on, and
    at import there is no context to offer anything to.  Its first *check* is
    the first moment there is one, and a check that has just happened is a safe
    place to make GL calls from: the call it belongs to is complete.

    Costs nothing per call afterwards.  The bootstrap replaces itself with
    whichever reader the offer settled on, so the ordinary path is a flag read
    or a ``glGetError``, never a test of whether the offer has been made.
    """

    def bootstrap():
        checker.setErrorReader(None)
        offer_debug_output()
        return checker._getErrors()

    checker.setErrorReader(bootstrap)


def _stop_reading_debug_output():
    """Go back to a glGetError per call."""
    layer = _layer()
    if layer is not None:
        layer.set_error_mode(0)
        return
    checker = _ctypes_error_checker()
    if checker is not None:
        checker.setErrorReader(None)


def _release_debug_callback(key):
    """Give up ``key``'s callback and stop reading the flag it set.

    Whose reading stops depends on where the mode is kept.  The C
    implementation keeps it with the context's table, so this context is the
    only one affected.  The ctypes one holds a single checker for the process,
    so it goes back to the round trip once nothing holds a callback any more
    and not before -- sooner would leave every other context paying for
    synchronous debug output and reading neither the flag it sets nor an error
    of its own.

    Returns whether ``key`` had a callback to give up.
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
    """Whether this context already reports debug messages somewhere else.

    Asked before installing, because ``glDebugMessageCallback`` holds one
    callback per context: a second one replaces the first rather than joining
    it.  A context that already has one belongs to a program using
    ``GL_KHR_debug`` for its own purposes, and taking that over would silence
    its diagnostics as surely as its next call would silence our checking.
    """
    from OpenGL.GL import glGetPointerv

    try:
        address = _as_address(glGetPointerv(_DEBUG_CALLBACK_FUNCTION))
    except Exception:  # pragma: no cover - a context that will not answer
        # An answer is what would let us decline; without one, declining every
        # time would mean no context ever got the cheaper check.
        return False
    if not address:
        return False
    if address == ours:
        return False
    # Ours from an earlier enable in this same context, seen again.
    previous = _installed_callbacks.get(key)
    return previous is None or address != _callback_address(previous)


def _callback_address(callback):
    """The address the driver was given for a ctypes callback object."""
    return ctypes.cast(callback, ctypes.c_void_p).value


def _as_address(value):
    """A pointer the GL handed back, as a plain integer.

    ``glGetPointerv`` answers with whatever the array handler in use returns --
    a numpy scalar where numpy is installed, a ctypes pointer where it is not,
    and a one-element array holding either where ``SIZE_1_ARRAY_UNPACK`` is
    off.  Reading that last one as zero would say no application callback is
    installed, and PyOpenGL would take one over that is not its to take.
    """
    if value is None:
        return 0
    # A one-element array holding the pointer.  Unwrapped by length rather than
    # by trying to index: a ctypes pointer answers indexing by dereferencing
    # what it points at, so asking it for element zero reads memory instead of
    # saying it is not a sequence.
    if hasattr(value, '__len__') and len(value) == 1:
        value = value[0]
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return ctypes.cast(value, ctypes.c_void_p).value or 0
        except ctypes.ArgumentError:  # pragma: no cover - an answer we cannot read
            return 0
