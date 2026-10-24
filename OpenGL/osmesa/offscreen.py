"""Offscreen OpenGL contexts with OSMesa, which needs no window system.

OSMesa is Mesa's off-screen rendering API.  It is a separate API, used without
GLX or EGL.  The caller allocates the framebuffer and OSMesa rasterises into
it.  It needs no display server, no device node and no drawable.  It works on
a build machine, in a container with no ``/dev/dri`` and on a render farm
node.  It is also the slowest option, because it always rasterises in
software.

Set ``PYOPENGL_PLATFORM=osmesa`` before importing PyOpenGL.  The platform
selects the library every entry point is loaded from::

    import os
    os.environ['PYOPENGL_PLATFORM'] = 'osmesa'

    from OpenGL.osmesa.offscreen import OffscreenContext
    from OpenGL.GL import *

    with OffscreenContext(width=256, height=256) as context:
        glClearColor(0, 0, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        image = context.read()          # (height, width, 4) of GLubyte

The array is the default framebuffer.  ``glClear``, ``glReadPixels`` and
queries against framebuffer zero all use the array the context allocated, so
drawing code needs no changes for offscreen use.

The image rows are bottom-up, as ``glReadPixels`` returns them.
:meth:`OffscreenContext.read` returns them in that order.
``read(top_down=True)`` flips the rows into the order image files use.

``profile`` and ``version`` are passed to ``OSMesaCreateContextAttribs``,
which Mesa has had since 12.0.  Without that entry point the module uses
``OSMesaCreateContext``, which takes neither.  A request for a core profile
on such a build raises :class:`OSMesaError`, so it never gets a legacy
context in its place.
"""

import ctypes

from OpenGL import _dispatch, arrays
from OpenGL.raw.GL.VERSION.GL_1_1 import GL_UNSIGNED_BYTE
from OpenGL.raw.osmesa import mesa as _mesa

__all__ = (
    'OSMesaError',
    'PROFILES',
    'available',
    'OffscreenContext',
    'headless_context',
)

#: The profile names accepted, and the OSMesa enum each selects.
PROFILES = {
    'core': _mesa.OSMESA_CORE_PROFILE,
    'compatibility': _mesa.OSMESA_COMPAT_PROFILE,
}

#: Bytes per pixel of RGBA, the only format this module uses.  RGBA has an
#: unambiguous readback shape, and every OSMesa build has it.  The packed
#: formats (``OSMESA_RGB_565``) are a Mesa build option.
_CHANNELS = 4


class OSMesaError(RuntimeError):
    """An OSMesa call failed, or OSMesa cannot meet the request."""


def available():
    """The OSMesa entry points this build lacks, as a tuple.

    An empty tuple means a context can be created.  A program choosing a
    renderer can call this instead of catching :class:`OSMesaError` from a
    construction attempt.
    """
    missing = []
    if not _mesa.OSMesaCreateContext:
        missing.append('OSMesaCreateContext')
    if not _mesa.OSMesaMakeCurrent:
        missing.append('OSMesaMakeCurrent')
    return tuple(missing)


def context_attributes(profile='core', version=(3, 3), depth_bits=24,
                       stencil_bits=8, accum_bits=0):
    """The attribute list for ``OSMesaCreateContextAttribs``.

    The function makes no OSMesa calls, so it runs without Mesa installed.
    """
    if profile not in PROFILES:
        raise OSMesaError(
            '%r is not a profile OSMesa offers; use one of %s'
            % (profile, ', '.join(sorted(PROFILES))))
    major, minor = (tuple(version) + (0, 0))[:2]
    attributes = [
        _mesa.OSMESA_FORMAT, _mesa.OSMESA_RGBA,
        _mesa.OSMESA_DEPTH_BITS, depth_bits,
        _mesa.OSMESA_STENCIL_BITS, stencil_bits,
        _mesa.OSMESA_ACCUM_BITS, accum_bits,
        _mesa.OSMESA_PROFILE, PROFILES[profile],
        _mesa.OSMESA_CONTEXT_MAJOR_VERSION, int(major),
        _mesa.OSMESA_CONTEXT_MINOR_VERSION, int(minor),
        0,
    ]
    return (ctypes.c_int * len(attributes))(*[int(one) for one in attributes])


class OffscreenContext(object):
    """An OpenGL context rendering into an array this object owns.

    The context is current after construction and after :meth:`make_current`.
    Release it with :meth:`release`, or use it as a context manager.  An
    unreleased context is released when it is garbage-collected.  Mesa holds
    a pointer to the array, so the context must not outlive the array.

    ``width`` and ``height`` are in pixels, ``profile`` is one of
    :data:`PROFILES`, and ``version`` is the requested GL version.  If Mesa
    cannot meet the request, the constructor raises :class:`OSMesaError`
    describing what failed.
    """

    context = None
    buffer = None

    def __init__(self, width=256, height=256, profile='core', version=(3, 3),
                 depth_bits=24, stencil_bits=8, accum_bits=0):
        width, height = int(width), int(height)
        if width <= 0 or height <= 0:
            raise OSMesaError('cannot render at %dx%d' % (width, height))
        missing = available()
        if missing:
            raise OSMesaError(
                'this build has no OSMesa: %s missing' % (', '.join(missing),))
        self.width, self.height = width, height
        self.profile = profile
        self.version = tuple(version)
        try:
            self.context = self._create(depth_bits, stencil_bits, accum_bits)
            # The framebuffer, allocated here and written by the rasteriser.
            # Held for the life of the context, because OSMesa keeps the
            # pointer.
            self.buffer = arrays.GLubyteArray.zeros(
                (height, width, _CHANNELS))
            self.make_current()
        except BaseException:
            # Release what was created, so a program that tries this and falls
            # back to another renderer does not leak a Mesa context.
            self.release()
            raise

    def _create(self, depth_bits, stencil_bits, accum_bits):
        if _mesa.OSMesaCreateContextAttribs:
            attributes = context_attributes(
                self.profile, self.version,
                depth_bits=depth_bits, stencil_bits=stencil_bits,
                accum_bits=accum_bits)
            context = _mesa.OSMesaCreateContextAttribs(attributes, None)
            if context:
                return context
            raise OSMesaError(
                'OSMesa would not make a %s GL %d.%d context'
                % ((self.profile,) + self.version[:2]))
        if self.profile != 'compatibility' or self.version[:2] > (2, 1):
            raise OSMesaError(
                'this OSMesa has no OSMesaCreateContextAttribs, so it can '
                'serve neither a profile nor a version: asked for %s GL '
                '%d.%d' % ((self.profile,) + self.version[:2]))
        context = _mesa.OSMesaCreateContext(_mesa.OSMESA_RGBA, None)
        if not context:
            raise OSMesaError('OSMesaCreateContext would not make a context')
        return context

    # -- current context ----------------------------------------------------

    def make_current(self):
        """Bind this context and its buffer to the calling thread.

        The new current context is recorded in the dispatch layer, which has
        no other way to learn of the switch.  The compiled dispatch layer keeps
        a table of resolved entry points per context.  It reads the current
        context only on the resolution slow path.  Without this call, a second
        context would keep using the first context's table, including its
        flags for which commands that context has.  ``OpenGL.WGL.offscreen``
        and ``OpenGL.Tk.context`` make the same call for the same reason.
        """
        if self.context is None:
            raise OSMesaError('this context has been released')
        if not _mesa.OSMesaMakeCurrent(self.context, self.buffer,
                                       GL_UNSIGNED_BYTE,
                                       self.width, self.height):
            raise OSMesaError(
                'OSMesaMakeCurrent refused a %dx%d RGBA buffer'
                % (self.width, self.height))
        _dispatch.make_current(self.context)
        return self

    # -- readback -----------------------------------------------------------

    def read(self, top_down=False):
        """Return the framebuffer, after ``glFinish``.

        With numpy, the result is a copy: a ``(height, width, 4)`` array of
        bytes that later frames do not change.  Rows are bottom-up, as
        ``glReadPixels`` returns them, and ``top_down=True`` flips them into
        the order image files use.  Without numpy, the result is the context's
        own flat ctypes buffer, which the next frame overwrites.
        """
        if self.buffer is None:
            raise OSMesaError('this context has been released')
        from OpenGL.raw.GL.VERSION.GL_1_1 import glFinish

        glFinish()
        image = _as_image(self.buffer, self.height, self.width, _CHANNELS)
        return image[::-1] if top_down else image

    # -- teardown -----------------------------------------------------------

    @staticmethod
    def _address(context):
        """An OSMesa context pointer as an integer, for comparing contexts.

        ``==`` between two ``OSMesaContext`` pointers is False even when both
        point to the same context.  They are distinct ctypes objects, and the
        opaque pointer type compares objects, not addresses.
        """
        return ctypes.cast(context, ctypes.c_void_p).value

    def _finish_if_current(self, context):
        """Finish outstanding rasterisation before the buffer is freed.

        OSMesa may still be rasterising into the caller's array when the
        context is destroyed.  Destroying a context with work outstanding
        faults inside ``OSMesaDestroyContext``.  One draw call is enough to
        cause it.  A context that was only cleared is destroyed safely, and one
        that drew a single rectangle faults.  The fault happens during
        teardown, so the traceback does not show the frame that caused it.

        ``glFinish`` acts on the current context, so it is called only when
        this context is current.  Calling it for another context would stall
        that context's caller.
        """
        if self._address(_mesa.OSMesaGetCurrentContext()) != self._address(context):
            return
        from OpenGL.raw.GL.VERSION.GL_1_1 import glFinish

        glFinish()

    def release(self, forget=True):
        """Destroy the context.  Safe to call twice, and during construction.

        The buffer is freed one statement after the context is destroyed.
        OSMesa holds the pointer passed to ``OSMesaMakeCurrent`` and reads
        through it during teardown.  If this object dropped its reference
        first, Python could free the array while Mesa still uses it.  The
        local variable keeps the array alive across the call.

        With ``forget=True`` (the default), the context is removed from the
        dispatch layer.  Its table of resolved entry points is then discarded,
        and is not reused for a later context Mesa creates at the same
        address.  See :meth:`make_current`.

        ``forget=False`` destroys the context without removing it from the
        dispatch layer.  This reproduces a program that destroys a context
        without notifying PyOpenGL, for tests of that case.
        """
        context, self.context = self.context, None
        buffer, self.buffer = self.buffer, None
        if context is not None:
            self._finish_if_current(context)
            if forget:
                _dispatch.forget_context(context)
            _mesa.OSMesaDestroyContext(context)
        del buffer

    def __del__(self):
        """Release a context the program dropped without releasing it.

        The array must not be freed before the context.  OSMesa rasterises
        into the array this object owns, and holds the pointer for as long as
        the context exists.  If the array were freed first, the next
        ``OSMesaMakeCurrent`` on that thread would flush this context's front
        buffer into freed memory.  That corrupts other allocations, and the
        process crashes later in an unrelated call.

        Call :meth:`release` directly; this finaliser is a fallback.  Calling
        :meth:`release` twice is safe.  Errors are ignored, because a finaliser
        cannot raise to a caller, and at interpreter shutdown the library may
        already be unloaded.
        """
        try:
            self.release()
        except Exception:  # noqa: BLE001, S110 a finaliser has nobody to raise to
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.release()

    def __repr__(self):
        return '%s(%dx%d, %s GL %d.%d)' % (
            (self.__class__.__name__, self.width, self.height, self.profile)
            + self.version[:2])


def _as_image(buffer, height, width, channels):
    """The framebuffer as an array, through numpy where there is numpy."""
    try:
        import numpy
    except ImportError:
        return buffer
    return numpy.frombuffer(
        bytes(bytearray(buffer)), dtype=numpy.uint8,
    ).reshape((height, width, channels)).copy()


def headless_context(width=256, height=256, **named):
    """An :class:`OffscreenContext`, named to match ``OpenGL.WGL.offscreen``."""
    return OffscreenContext(width=width, height=height, **named)
