"""Rendering with OSMesa: a context with no window system behind it.

OSMesa is Mesa's off-screen interface.  It is not a driver reached through GLX
or EGL but an API of its own: the caller allocates the framebuffer, OSMesa
rasterises into it, and there is no display server, no device node and no
drawable anywhere in the arrangement.  That makes it the last resort that
always works -- a build machine, a container with no ``/dev/dri``, a render
farm node -- and the slowest, since it is software rasterisation by definition.

``PYOPENGL_PLATFORM=osmesa`` must be set before PyOpenGL is imported, because
the platform decides which library every entry point is loaded from:

    import os
    os.environ['PYOPENGL_PLATFORM'] = 'osmesa'

    from OpenGL.osmesa.offscreen import OffscreenContext
    from OpenGL.GL import *

    with OffscreenContext(width=256, height=256) as context:
        glClearColor(0, 0, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        image = context.read()          # (height, width, 4) of GLubyte

**The buffer is the default framebuffer.**  ``glClear``, ``glReadPixels`` and
the queries a program makes against framebuffer zero all land in the array the
context allocated, so nothing has to be told it is rendering off-screen.

**The image is bottom-up** as OpenGL hands it over, matching ``glReadPixels``.
:meth:`OffscreenContext.read` returns it that way; ``read(top_down=True)``
flips it, which is what an image file wants.

``profile`` and ``version`` are served by ``OSMesaCreateContextAttribs``,
which Mesa has had since 12.0.  Where that entry point is absent this falls
back to ``OSMesaCreateContext``, which takes neither -- so a request for a
core profile on such a build is refused rather than quietly answered with a
legacy context.
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

#: Bytes per pixel of the one format this serves.  RGBA is the only format
#: whose readback shape is unambiguous, and the only one every OSMesa build
#: has; the packed ones (``OSMESA_RGB_565``) are a Mesa build option.
_CHANNELS = 4


class OSMesaError(RuntimeError):
    """Something OSMesa would not do."""


def available():
    """What is missing before an OSMesa context can be made, as a tuple.

    Empty when one can be.  A program deciding between renderers asks this
    rather than catching :class:`OSMesaError` from a construction attempt.
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

    Pure, so what is asked for can be read without a Mesa to ask it of.
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

    Created current, and current again after :meth:`make_current`.  Release it
    with :meth:`release`, or use it as a context manager; one that is simply
    dropped releases itself when it is collected, because Mesa holds the
    pointer to the array it renders into and must not outlive it.

    ``width`` and ``height`` are in pixels, ``profile`` one of
    :data:`PROFILES`, and ``version`` the GL version asked for.  A Mesa that
    cannot serve the request raises :class:`OSMesaError` saying what it could
    not do.
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
            # The framebuffer, allocated by us and written by the rasteriser.
            # Held for the life of the context: OSMesa keeps the pointer.
            self.buffer = arrays.GLubyteArray.zeros(
                (height, width, _CHANNELS))
            self.make_current()
        except BaseException:
            # A part-built context leaks the Mesa-side one otherwise, and a
            # program is invited to try this and fall back to something else.
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

    # -- being the current context -----------------------------------------

    def make_current(self):
        """Bind this context and its buffer to the calling thread.

        The dispatch layer is told, because it cannot see the switch: the
        compiled one keeps a table of resolved entry points per context and
        reads which one is current on the resolution slow path, so a second
        context taken without a word goes on dispatching through the first
        one's table -- holding the slots, and the flags saying which commands
        that context has, of a context it has left.  ``OpenGL.WGL.offscreen``
        and ``OpenGL.Tk.context`` say so for the same reason.
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

    # -- what was drawn ----------------------------------------------------

    def read(self, top_down=False):
        """The framebuffer as an ``(height, width, 4)`` array of bytes.

        Bottom-up as OpenGL hands it over, which is what ``glReadPixels``
        answers with; ``top_down=True`` flips it, which is what an image file
        wants.  A copy, so what it returns does not change under the next
        frame.
        """
        if self.buffer is None:
            raise OSMesaError('this context has been released')
        from OpenGL.raw.GL.VERSION.GL_1_1 import glFinish

        glFinish()
        image = _as_image(self.buffer, self.height, self.width, _CHANNELS)
        return image[::-1] if top_down else image

    # -- giving it back ----------------------------------------------------

    @staticmethod
    def _address(context):
        """An OSMesa context as an integer, which is how two are compared.

        ``==`` between two ``OSMesaContext`` pointers is False even when both
        name the same context: they are distinct ctypes objects, and the
        opaque pointer type defines no equality that looks through them.
        """
        return ctypes.cast(context, ctypes.c_void_p).value

    def _finish_if_current(self, context):
        """Complete outstanding rasterisation before the buffer can go away.

        OSMesa rasterises into the caller's array and need not have finished
        when the context is destroyed: tearing one down with work outstanding
        faults inside ``OSMesaDestroyContext``.  Any draw at all is enough --
        a cleared context tears down happily, one that has drawn a single
        rectangle does not -- and the fault lands in the teardown rather than
        in the drawing, so nothing in the traceback names the frame that
        caused it.

        Only when this context is the current one: ``glFinish`` acts on
        whatever is current, and finishing somebody else's context here would
        be a stall charged to the wrong caller.
        """
        if self._address(_mesa.OSMesaGetCurrentContext()) != self._address(context):
            return
        from OpenGL.raw.GL.VERSION.GL_1_1 import glFinish

        glFinish()

    def release(self, forget=True):
        """Destroy the context.  Idempotent, and safe part-way through init.

        **The buffer outlives the context, by one statement.**  OSMesa holds
        the pointer it was made current with and reads through it while the
        context is torn down; dropping this object's reference first lets
        Python free the array under a Mesa that is still using it.  The local
        binding is what keeps it alive across the call.

        The dispatch layer is told the context has gone, so that its table of
        resolved entry points is retired rather than left for whichever context
        Mesa hands that address to next.  See :meth:`make_current`.

        ``forget=False`` destroys it *without* saying so, which is the state a
        program is in when it tears a context down and does not notify
        PyOpenGL.  A caller testing that behaviour asks for it; everything else
        wants the notification.
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

        **Mesa keeps the pointer, so the array cannot be collected first.**
        OSMesa rasterises into the array this object owns, and holds that
        pointer for as long as the context lives.  Letting go of both leaves
        Mesa with a context whose framebuffer Python has freed, and the next
        ``OSMesaMakeCurrent`` on that thread flushes this context's front
        buffer through it -- a write into freed memory, which corrupts
        whatever the allocator has since put there and brings the process
        down in some later call that did nothing wrong.

        :meth:`release` is the ordinary way and this is the backstop; it is
        idempotent, so a caller who released loses nothing by having one.
        Errors are swallowed because a finaliser has nobody to raise to, and
        because at interpreter shutdown the library may already be gone.
        """
        try:
            self.release()
        except Exception:                  # pragma: no cover - shutdown only
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
    """An :class:`OffscreenContext`, for symmetry with ``OpenGL.WGL.offscreen``."""
    return OffscreenContext(width=width, height=height, **named)
