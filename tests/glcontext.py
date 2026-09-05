#! /usr/bin/env python3
"""Shared, windowing- and API-agnostic base class for rendering tests.

Every suite here rests on this: the gl, glu and gles ones, and the legacy
root-level tests through ``basetestcase`` and ``testdecorator``.  It holds the
machinery they share so they differ only where they genuinely must:

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
  the suite's one backend choice -- ``basetestcase`` and ``testdecorator`` ask
  it too -- and the backend module is imported lazily, so a glfw run never
  imports pygame.

A concrete test case is ``class Case(pick_backend(), SomeAPIBase)`` -- the
backend mixin supplies ``_create_context`` / ``_swap`` / ``_destroy_context``;
the API base supplies ``self.gl`` and any API-specific helpers.
"""

from __future__ import print_function

import os
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
# Backend selection (mirrors basetestcase.py / testdecorator.py)
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


#: The vocabulary is :mod:`backends`', so that this module, ``basetestcase``
#: and ``testdecorator`` cannot disagree about which names TEST_WINDOWING may
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
       ``pygame``), honour ``TEST_WINDOWING`` when set and available, and
       default to glfw then pygame.
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

    available = [name for name in _WINDOWED if _installed(name)]
    if not available:
        raise ImportError(
            'No windowing backend available for tests; install glfw or pygame '
            '(or run headless with TEST_WINDOWING=egl)'
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
    raise RuntimeError('Unhandled backend: %s' % (backend,))


#: The leading ``major.minor`` of a GL_VERSION string, past any API name.
#: Desktop GL starts with the number; OpenGL-ES puts "OpenGL ES" (or
#: "OpenGL ES-CM") in front of it.
_VERSION = re.compile(r'(?:OpenGL\s+ES(?:-CM|-SC)?\s+)?(\d+)\.(\d+)')


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
    return ('the context provides GL %d.%d, and this case needs %d.%d'
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

    def _destroy_context(self):
        raise NotImplementedError

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
        self.addCleanup(self._destroy_context)
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
        """Return the context version as a (major, minor) int tuple."""
        major = self.getInteger(self.gl.GL_MAJOR_VERSION)
        minor = self.getInteger(self.gl.GL_MINOR_VERSION)
        return (major, minor)

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
