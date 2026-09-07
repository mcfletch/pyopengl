#! /usr/bin/env python3
"""Shared, windowing- and API-agnostic base class for rendering tests.

Every suite here rests on this: the gl, glu and gles ones, and the stand-alone
check scripts through ``testdecorator``.  It holds the machinery they share so
they differ only where they genuinely must:

* :class:`ContextTestCase` -- the API-agnostic base.  It owns the fixture
  (create a context, clear it, tear it down), the ``TEST_VISIBLE`` / dwell
  behaviour, and the readback / introspection helpers.  It never imports an
  OpenGL entry-point module itself; instead it reaches GL through ``self.gl``
  (the core module, e.g. ``OpenGL.GL`` or ``OpenGL.GLES2``) and ``self.gl3``
  (the module exporting the indexed ``glGetStringi`` query), which the
  API-specific subclasses set.  GL enum *values* are identical across the
  modules, so ``self.gl.GL_RGBA`` and friends work for every backend.

* :func:`pick_backend` -- chooses the backend mixin from ``TEST_WINDOWING`` and
  what is installed: glfw or pygame for a window, egl or cgl for none.  It is
  the suite's one backend choice -- the suite base cases and ``testdecorator``
  all ask it -- and the backend module is imported lazily, so a glfw run never
  imports pygame.

A concrete test case is ``class Case(pick_backend(), SomeAPIBase)`` -- the
backend mixin supplies ``_create_context`` / ``_swap`` / ``_destroy_context``;
the API base supplies ``self.gl`` and any API-specific helpers.
"""

from __future__ import print_function

import os
import sys
import time
import ctypes
import logging
import re

import backends
import unittest
import contextlib
import importlib.util

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------
def _installed(name):
    """Return True if ``name`` is importable, without importing it.

    Importing glfw/pygame has side effects (subsystem init, allocations), so we
    only probe for the package metadata here.
    """
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


#: The vocabulary is :mod:`backends`', so that this module and
#: ``testdecorator`` cannot disagree about which names TEST_WINDOWING may
#: take -- a name one accepts and another does not is a collection error.
_WINDOWED = backends.WINDOWED
_ALL_BACKENDS = backends.ALL


def pick_backend():
    """Return the windowing backend mixin class requested by the environment.

    Selection order:

    1. A headless backend when one is asked for by name: ``TEST_WINDOWING=egl``
       renders on an EGL device (see glcontext_egl) and ``cgl`` on a macOS CGL
       context (see glcontext_cgl).  Neither needs a toolkit or a display.
    2. Otherwise probe which windowed backends are importable (``glfw``,
       ``pygame``, ``tk``), honour ``TEST_WINDOWING`` when set and available,
       and default to glfw, then pygame, then tk.
    """
    requested = backends.requested()

    if requested == 'egl':
        log.info('Test windowing backend: egl (headless EGL device)')
        from glcontext_egl import EGLDeviceBackend
        return EGLDeviceBackend

    if requested == 'cgl':
        log.info('Test windowing backend: cgl (headless macOS context)')
        from glcontext_cgl import CGLBackend
        return CGLBackend

    available = [name for name in _WINDOWED
                 if _installed(backends.module_for(name))]
    if not available:
        raise ImportError(
            'No windowing backend available for tests; install glfw, pygame '
            'or tkinter (or run headless with TEST_WINDOWING=egl)'
        )
    if requested and requested not in available:
        raise ImportError(
            'TEST_WINDOWING=%s requested but %s is not installed'
            % (requested, requested)
        )

    backend = requested or available[0]
    log.info(
        'Test windowing backend: %s (TEST_WINDOWING=%s, available=%s)',
        backend, requested or '<unset>', ','.join(available),
    )
    if backend == 'glfw':
        from glcontext_glfw import GLFWBackend
        return GLFWBackend
    elif backend == 'pygame':
        from glcontext_pygame import PygameBackend
        return PygameBackend
    elif backend == 'tk':
        from glcontext_tk import TkBackend
        return TkBackend
    raise RuntimeError('Unhandled backend: %s' % (backend,))


#: The leading ``major.minor`` of a GL_VERSION string, past any API name.
#: Desktop GL starts with the number; OpenGL-ES puts "OpenGL ES" (or
#: "OpenGL ES-CM") in front of it.
_VERSION = re.compile(r'(?:OpenGL\s+ES(?:-CM|-SC)?\s+)?(\d+)\.(\d+)')


class Context(object):
    """A GL context outside a TestCase, on whichever backend this machine has.

    :func:`pick_backend` hands out a mixin for a rendering case; this is the
    same backend, the same ``TEST_WINDOWING`` choice and the same skips, for
    the cases that cannot be one -- a fixture holding two contexts at once, a
    worker thread taking one, a child process settling a question that is
    settled once per process.  Such a case that opens a GLFW window of its own
    is absent on every machine whose contexts come from somewhere else: an EGL
    device in a container, CGL on a macOS runner with no window server.

    Requirements are :class:`ContextTestCase`'s, as keywords::

        with Context(profile='core', gl_version=(3, 3)) as context:
            ...

    Raises :exc:`unittest.SkipTest` where the machine cannot serve the
    request -- which is what the backends raise, and what pytest and unittest
    both read as a skip -- including where the context that came back is older
    than the one asked for.  See :func:`version_shortfall` for why that gap is
    a skip and not a failure.
    """

    #: the entry-point module each API's version string is read through.
    _API_MODULES = {'gl': 'OpenGL.GL', 'gles': 'OpenGL.GLES2', 'es': 'OpenGL.GLES2'}

    def __init__(self, **requirements):
        namespace = dict(requirements, runTest=lambda self: None)
        self._case = type(
            'StandaloneContext', (pick_backend(), ContextTestCase), namespace,
        )('runTest')
        self._case._create_context()
        self._released = False
        try:
            self._check_version()
        except BaseException:
            self.release()
            raise

    def _check_version(self):
        """Refuse a context older than the one asked for, as setUp does."""
        case = self._case
        if case.profile == 'any':
            return
        module = importlib.import_module(
            self._API_MODULES[getattr(case, 'api', 'gl').lower()]
        )
        case.gl = case.gl3 = module
        shortfall = version_shortfall(
            case.getString(module.GL_VERSION), case.gl_version)
        if shortfall:
            raise unittest.SkipTest(shortfall)

    @property
    def gl_version(self):
        return self._case.gl_version

    @property
    def profile(self):
        return self._case.profile

    @property
    def handle(self):
        """This context's handle, whichever context is current now."""
        return self._case._context_handle()

    def make_current(self):
        """Make this the context the calling thread draws through."""
        self._case._make_current()
        return self

    def release(self, forget=True):
        """Destroy the context and tell the dispatch layer it is gone.

        Safe to call twice, so a caller that released explicitly can still
        leave the ``with`` block.

        ``forget=False`` destroys it *without* saying so, which is the state a
        program is in when it tears a context down and does not notify
        PyOpenGL -- what a cleanup handler running after its context has gone
        actually faces.  A case about that behaviour asks for it; everything
        else wants the notification, since the handle is an address the driver
        hands out again.
        """
        if not self._released:
            self._released = True
            if forget:
                self._case._release_context()
            else:
                self._case._destroy_context()

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.release()


#: What a child process exits with to say there is nothing here to test with.
NOTHING_TO_TEST_WITH = 77

#: The first lines of a child process that needs a context.
#:
#: Several cases run in a fresh interpreter, because what they check is settled
#: once per process: which dispatch implementation is installed, what a call
#: with no context does, what the attribute surface looks like.  They need a
#: context on the same backend the in-process suites use, or they are absent on
#: every machine whose contexts do not come from GLFW.  This puts this
#: directory on the child's path and hands it :func:`context_or_exit`;
#: interpolate it at the top of the script.
CHILD_PREAMBLE = (
    'import sys\n'
    'sys.path.insert(0, %r)\n'
    'from glcontext import context_or_exit, NOTHING_TO_TEST_WITH\n'
) % (os.path.dirname(os.path.abspath(__file__)),)


def context_or_exit(**requirements):
    """A :class:`Context` for a child process, or exit saying there is none.

    A child cannot skip itself -- the parent reads its exit status -- so a
    machine that cannot serve the request ends the child with
    :data:`NOTHING_TO_TEST_WITH` and the reason on stderr, which the parents
    here turn into a skip.
    """
    try:
        return Context(**requirements)
    except unittest.SkipTest as reason:
        print(reason, file=sys.stderr)
        raise SystemExit(NOTHING_TO_TEST_WITH)


def window_was_made(window):
    """Whether GLFW actually made the window it was asked for.

    ``glfw.create_window`` answers a **NULL** ``LP__GLFWwindow`` where it could
    not -- no accelerated pixel format, no display, a version the driver will
    not give -- and a NULL ctypes pointer is falsy but *not* ``None``.  So
    ``window is None`` reads a refusal as a window: the caller makes it
    current, gets no context, and every call through it answers zero.  The
    cases that follow then fail on what they assert rather than skipping on
    what they have, and the reason is nowhere in the failure.

    Used by the fixtures here; a child-process script writes ``if not window``,
    which is the same test.
    """
    return bool(window)


def forget_context(handle):
    """Tell the dispatch layer a context is gone.

    Its table of resolved entry points is keyed by the context handle, and a
    handle is an address the driver hands out again -- three hundred contexts
    through this suite reuse a couple of dozen addresses.  A context torn down
    without saying so leaves its resolved pointers behind for whichever context
    lands on that address next, which then answers about a context that no
    longer exists: not a leak but a wrong answer, and one that surfaces as an
    entry point reported missing where it is supported, or present where it is
    not.

    :class:`ContextTestCase` does this for every context it makes; a test that
    makes its own calls this.
    """
    if not handle:
        return
    try:
        from OpenGL import _dispatch
    except ImportError:                    # pragma: no cover - ctypes-only build
        return
    _dispatch.forget_context(int(handle))


def parse_gl_version(reported):
    """``(major, minor)`` from a GL_VERSION string, or ``None``.

    Everything after the number is the driver describing itself and differs by
    vendor, so only the front is read.
    """
    if not reported:
        return None
    found = _VERSION.match(reported.strip())
    if not found:
        return None
    return (int(found.group(1)), int(found.group(2)))


def version_shortfall(reported, wanted):
    """Why ``reported`` does not meet ``wanted``, or ``None`` where it does.

    Asking for a version is not getting it.  GLFW refuses a request its driver
    cannot meet, so a window either has the version or was never made; CGL
    accepts a pixel format naming the 3.2 core profile on a renderer that
    implements 2.1 and hands back a 2.1 context.

    That gap is not a failed test but a dead process: macOS exports every entry
    point from the framework whether or not the current context implements it,
    so a GL 3.1 call on a 2.1 context resolves, is called, and segfaults.

    A version this cannot read is let through.  Refusing there would turn one
    unrecognised driver string into a skip on every test it runs, and the entry
    points still answer for themselves.
    """
    if not wanted:
        return None
    found = parse_gl_version(reported)
    if found is None or found >= tuple(wanted):
        return None
    return ('the context provides GL %d.%d, short of the %d.%d asked for'
            % (found + tuple(wanted)))


# ---------------------------------------------------------------------------
# API-agnostic base test case
# ---------------------------------------------------------------------------
class ContextTestCase(unittest.TestCase):
    """Toolkit- and API-agnostic base for context-backed rendering tests.

    Subclasses set :attr:`gl` / :attr:`gl3` to the relevant OpenGL entry-point
    modules and may override the context-requirement attributes below; a
    backend mixin supplies the window/context creation hooks.
    """

    # --- context requirements (override on subclasses / individual tests) --
    #: 'gl' for desktop OpenGL, 'gles' for OpenGL-ES (consumed by the backend).
    api = 'gl'
    #: 'core' or 'compatibility' (a.k.a. full) profile (desktop GL only).
    profile = 'compatibility'
    #: (major, minor) version to request.
    gl_version = (2, 1)
    red_size = green_size = blue_size = alpha_size = 8
    depth_size = 24
    stencil_size = 8
    #: accumulation-buffer bits (legacy; request non-zero to use glAccum).
    accum_size = 0
    #: Ask for a debug context, so the driver will report through
    #: GL_KHR_debug.  A backend with no way to ask makes an ordinary context:
    #: the extension is the authority on whether reporting is available, and a
    #: case that needs it checks for it.
    debug_context = False
    width = height = 128
    #: Off by default: a suite that maps windows takes over the screen of
    #: whoever runs it, and steals focus while they are doing something
    #: else.  ``TEST_VISIBLE=1`` to watch a run.  A hidden window still
    #: has a real context on the real driver, so nothing is given up.
    visible = os.environ.get('TEST_VISIBLE', '0').lower() in ('1', 'true', 'yes')
    #: seconds to leave a visible window on screen after rendering.  Override
    #: with TEST_DWELL (e.g. TEST_DWELL=5 to eyeball the window/backend).
    dwell = float(os.environ.get('TEST_DWELL', '0.017' if not visible else '0.2'))

    #: core entry-point module (e.g. OpenGL.GL / OpenGL.GLES2); set by subclass.
    gl = None
    #: module exporting the indexed glGetStringi query (GL / GLES3); subclass.
    gl3 = None

    # --- backend hooks (a mixin must implement these) --------------------
    def _create_context(self):
        raise NotImplementedError(
            'No windowing backend mixed in; compose with a backend from '
            'pick_backend()'
        )

    def _swap(self):
        raise NotImplementedError

    def _make_current(self):
        """Make this instance's context current on the calling thread.

        Every backend can, and a case that holds more than one context at a
        time -- or hands one to a worker thread -- has no other way to say
        which context it means.
        """
        raise NotImplementedError

    def _destroy_context(self):
        raise NotImplementedError

    # --- giving a context back -------------------------------------------
    def _context_handle(self):
        """The GL context handle the dispatch table is keyed by, or ``None``.

        This instance's, not whichever context happens to be current: another
        case's may have been made current since, and the table to forget is
        the one belonging to the context about to be destroyed.  So the
        context is made current first.
        """
        try:
            from OpenGL import platform

            self._make_current()
            return platform.PLATFORM.GetCurrentContext()
        except Exception:              # pragma: no cover - a context already gone
            return None

    def _release_context(self):
        """Destroy the context and tell the dispatch layer it is gone.

        The layer's table of resolved entry points is keyed by the context
        handle, and a handle is an address the driver is free to hand out
        again -- three hundred contexts through this fixture reuse a couple of
        dozen addresses.  A context torn down without saying so leaves its
        resolved pointers behind for whichever context lands on that address
        next, which then answers about a context that no longer exists: not a
        leak but a wrong answer, showing up as a test passing for the wrong
        reason or a call into a function the new context does not have.

        Here rather than in each backend, because it is true of all of them.
        """
        handle = self._context_handle()
        try:
            self._destroy_context()
        finally:
            forget_context(handle)

    # --- fixture ----------------------------------------------------------
    def setUp(self):
        """Create the requested context and leave it current and cleared.

        A context that does not provide the version the case asked for skips
        it: not every backend refuses such a request, and calling an entry
        point the context does not implement is a crash rather than a failure
        on a platform whose entry points resolve regardless -- see
        :func:`version_shortfall`.
        """
        self._create_context()
        # Registered here rather than done in tearDown, for two reasons.
        # unittest runs tearDown() before doCleanups(), so destroying the
        # context there would destroy it before any addCleanup() the test
        # registered -- and cleanups run newest-first, so registering this one
        # now puts it last of all.  It also means a setUp that fails after this
        # point still gives the context back.
        self.addCleanup(self._release_context)
        self._cleanup = []
        if self.profile != 'any':
            shortfall = version_shortfall(
                self.getString(self.gl.GL_VERSION), self.gl_version)
            if shortfall:
                self.skipTest(shortfall)
        self._setup_default_objects()
        self.gl.glViewport(0, 0, self.width, self.height)
        self.gl.glClearColor(0.0, 0.0, 0.25, 1.0)
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT | self.gl.GL_DEPTH_BUFFER_BIT)
        self.check_error('setUp')

    def _setup_default_objects(self):
        """Hook for API-specific post-context setup (e.g. a core-profile VAO)."""

    def tearDown(self):
        for fn in reversed(getattr(self, '_cleanup', [])):
            try:
                fn()
            except Exception:
                pass
        self._swap()  # present, so a visible run shows the frame
        if self.visible and self.dwell:
            time.sleep(self.dwell)

    def defer_cleanup(self, fn):
        """Register ``fn`` to run (best-effort) at teardown, newest first."""
        self._cleanup.append(fn)

    # --- introspection helpers -------------------------------------------
    def getString(self, enum):
        value = self.gl.glGetString(enum)
        if isinstance(value, bytes):
            return value.decode('ascii', 'replace')
        return value

    def getStringi(self, enum, index):
        value = self.gl3.glGetStringi(enum, index)
        if isinstance(value, bytes):
            return value.decode('ascii', 'replace')
        return value

    def getInteger(self, enum, count=1):
        buf = (ctypes.c_int * count)()
        self.gl.glGetIntegerv(enum, buf)
        return buf[0] if count == 1 else list(buf)

    def version(self):
        """The context's version as a ``(major, minor)`` int tuple.

        Read from ``GL_VERSION``, which every context answers.
        ``GL_MAJOR_VERSION`` arrived with GL 3.0 and ES 3.0, so asking a 2.1
        context for it is ``GL_INVALID_ENUM`` rather than a version -- and 2.1
        is the only profile macOS gives with fixed function in it, which is the
        one every compatibility case here runs on.

        The integer queries answer where the driver's string cannot be read;
        they exist wherever such a string does.
        """
        found = parse_gl_version(self.getString(self.gl.GL_VERSION))
        if found is not None:
            return found
        return (
            self.getInteger(self.gl.GL_MAJOR_VERSION),
            self.getInteger(self.gl.GL_MINOR_VERSION),
        )

    def extensions(self):
        """Return the set of supported extension strings.

        Uses the GL3/ES3 indexed query when available, falling back to the
        space-separated ``GL_EXTENSIONS`` string for older contexts.
        """
        if self.gl_version >= (3, 0):
            count = self.getInteger(self.gl3.GL_NUM_EXTENSIONS)
            return {self.getStringi(self.gl3.GL_EXTENSIONS, i) for i in range(count)}
        raw = self.getString(self.gl.GL_EXTENSIONS) or ''
        return set(raw.split())

    def require_extension(self, name):
        if name not in self.extensions():
            self.skipTest('extension %s not available' % (name,))

    def require_feature(self, name, core, extension):
        """Skip unless this context implements `name`, by version or extension.

        ``bool(some_entry_point)`` answers a different question: whether the
        *library* exports the symbol.  macOS exports every one of them from the
        framework whatever the current context implements, so a 2.1 context
        there resolves ``glGenVertexArrays``, calls it, and answers
        ``GL_INVALID_OPERATION`` -- a GL error naming a call the guard had
        already decided was available.  What a context implements is said by
        its own version, or by an extension it lists.
        """
        found = self.version()
        if found >= tuple(core) or extension in self.extensions():
            return
        self.skipTest(
            'this context has no %s: it is GL %d.%d, below the %d.%d that '
            'introduced them, and does not offer %s'
            % (name, found[0], found[1], core[0], core[1], extension)
        )

    def require_version(self, major, minor):
        if self.version() < (major, minor):
            self.skipTest('GL %d.%d required' % (major, minor))

    @contextlib.contextmanager
    def allow_missing(self):
        """Skip the test if an entry point is not exported by the driver."""
        from OpenGL import error

        try:
            yield
        except error.NullFunctionError as err:
            self.skipTest('entry point not exported: %s' % (err,))

    @contextlib.contextmanager
    def exercise(self):
        """Smoke-test entry points: skip if unexported, tolerate GLErrors."""
        from OpenGL import error

        try:
            yield
        except error.NullFunctionError as err:
            self.skipTest('entry point not exported: %s' % (err,))
        except error.GLError:
            pass
        while self.gl.glGetError() != self.gl.GL_NO_ERROR:
            pass

    @contextlib.contextmanager
    def tolerate_glerror(self, *codes):
        """Run a block, tolerating the given GLError ``codes`` (any if omitted).

        For exercising an entry point whose *reachability* is the point, where a
        well-defined GLError is an acceptable outcome on some drivers -- e.g. a
        driver that advertises KHR_robustness but does not actually serve a
        rarely-used robust getter, which the equivalent non-robust call proves
        is otherwise valid.  An *unlisted* error still propagates, so this does
        not hide unexpected failures.  Drains the error queue afterwards.
        """
        from OpenGL import error

        try:
            yield
        except error.GLError as err:
            if codes and err.err not in codes:
                raise
        while self.gl.glGetError() != self.gl.GL_NO_ERROR:
            pass

    def require_entrypoint(self, fn, name):
        """Skip unless ``fn`` resolved to a real entry point on this driver.

        Some ES-only EXT commands share a name with a desktop-GL command; under
        the shared headless ``PYOPENGL_PLATFORM=egl`` process PyOpenGL can cache
        a null for the ES variant once the GL one has been used.  Guarding keeps
        a combined run robust instead of raising NullFunctionError.
        """
        if not bool(fn):
            self.skipTest('entry point %s did not resolve in this process' % (name,))

    #: dtype code -> ctypes scalar, for get_checked's canary buffer.
    _CANARY_CTYPES = {
        'i': ctypes.c_int, 'i4': ctypes.c_int,
        'I': ctypes.c_uint, 'u4': ctypes.c_uint,
        'f': ctypes.c_float, 'f4': ctypes.c_float,
        'd': ctypes.c_double, 'f8': ctypes.c_double,
        'B': ctypes.c_ubyte, 'u1': ctypes.c_ubyte,
        'q': ctypes.c_longlong, 'i8': ctypes.c_longlong,
        'Q': ctypes.c_ulonglong, 'u8': ctypes.c_ulonglong,
    }

    def get_checked(self, fn, args, count, dtype='i'):
        """Call a ``glGet*v``-style command with an oversized, canary-filled
        output buffer and assert it wrote no further than ``count`` elements.

        A too-small output buffer silently overruns the heap (manifesting later
        as nondeterministic corruption), so allocate generously, stamp every
        slot with a sentinel, call ``fn(*args, buffer)``, and verify the slots
        past ``count`` still hold the sentinel.  Returns the first ``count``
        elements as a list.  Uses ctypes (no numpy dependency).
        """
        sentinel = 123  # representable as int / uint / float / ubyte
        slots = max(count + 64, 256)
        buf = (self._CANARY_CTYPES[dtype] * slots)(*([sentinel] * slots))
        fn(*args, buf)
        overrun = [i for i in range(count, slots) if buf[i] != sentinel]
        self.assertFalse(
            overrun,
            'glGet overran its output buffer past %d element(s); wrote into slots %r'
            % (count, overrun[:8]),
        )
        return [buf[i] for i in range(count)]

    # --- error / pixel helpers -------------------------------------------
    def check_error(self, context=''):
        err = self.gl.glGetError()
        self.assertEqual(
            err, self.gl.GL_NO_ERROR, 'GL error 0x%x during %s' % (err, context or '?')
        )

    def read_pixel(self, x, y):
        buf = (ctypes.c_ubyte * 4)()
        self.gl.glReadPixels(
            x, y, 1, 1, self.gl.GL_RGBA, self.gl.GL_UNSIGNED_BYTE, buf
        )
        self.check_error('glReadPixels')
        return tuple(buf)

    def read_image(self, x=0, y=0, width=None, height=None):
        width = self.width if width is None else width
        height = self.height if height is None else height
        image = self.gl.glReadPixels(
            x, y, width, height, self.gl.GL_RGBA, self.gl.GL_UNSIGNED_BYTE,
            outputType=None,
        )
        self.check_error('glReadPixels')
        return image

    def assert_pixel(self, x, y, expected, tolerance=8):
        actual = self.read_pixel(x, y)
        for chan, (a, e) in enumerate(zip(actual, expected)):
            self.assertLessEqual(
                abs(a - e),
                tolerance,
                'pixel (%d,%d) channel %d = %r, expected ~%r (got %r)'
                % (x, y, chan, a, e, actual),
            )
