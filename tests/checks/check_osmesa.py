#! /usr/bin/env python
# requires: osmesa numpy
"""OSMesa renders into a buffer the caller owns, with no window system.

A platform of its own rather than a driver behind GLX or EGL: the context is
made by ``OSMesaCreateContext`` and made current against an array the caller
allocated, which is also the framebuffer.  ``PYOPENGL_PLATFORM`` selects it,
and selection happens at import -- which is why this is a script rather than a
test case.

What it walks through is what the tickets on this platform report:

- the namespace imports and the entry points resolve (#70, #129)
- a context can be made current against a caller's array (#10, #18)
- ``glClear`` runs and the cleared colour is in that array afterwards (#34)
- ``glVertexAttribPointer`` records against the current context, which needs
  that context to be hashable (#33)

The last two matter most.  ``contextdata`` keys per-context state by whatever
``GetCurrentContext`` answers, so a platform whose context is not hashable
fails on the first call that stores anything -- and OSMesa's is an opaque
pointer where every other platform's is an integer.
"""
import os

os.environ['PYOPENGL_PLATFORM'] = 'osmesa'

import ctypes  # noqa: E402
import faulthandler  # noqa: E402

import checkutils  # noqa: E402

faulthandler.enable()

WIDTH, HEIGHT = 64, 48

#: The clear colour, and what the buffer must hold afterwards.
GREEN = (0.0, 1.0, 0.0, 1.0)
GREEN_BYTES = (0, 255, 0, 255)


def check_osmesa():
    import numpy
    from OpenGL import arrays, contextdata, platform
    from OpenGL.GL import (
        GL_COLOR_BUFFER_BIT, GL_FLOAT, GL_RENDERER, GL_UNSIGNED_BYTE,
        GL_VERSION, glClear, glClearColor, glFinish, glGetError, glGetString,
        glVertexAttribPointer,
    )
    from OpenGL.osmesa import (
        OSMESA_RGBA, OSMesaCreateContext, OSMesaDestroyContext,
        OSMesaMakeCurrent,
    )

    if platform.PLATFORM.__class__.__name__ != 'OSMesaPlatform':
        checkutils.skip(
            'PYOPENGL_PLATFORM did not select OSMesa; got %s'
            % (platform.PLATFORM.__class__.__name__,))

    context = OSMesaCreateContext(OSMESA_RGBA, None)
    if not context:
        checkutils.skip('OSMesaCreateContext would not make a context')
    try:
        # The framebuffer is the caller's: OSMesa rasterises straight into it.
        buffer = arrays.GLubyteArray.zeros((HEIGHT, WIDTH, 4))
        if not OSMesaMakeCurrent(context, buffer, GL_UNSIGNED_BYTE,
                                 WIDTH, HEIGHT):
            checkutils.skip('OSMesaMakeCurrent refused the buffer')

        print('renderer: %s' % (glGetString(GL_RENDERER).decode(),))
        print('version : %s' % (glGetString(GL_VERSION).decode(),))

        # The context has to be usable as a dict key before anything stores
        # per-context state against it.  Asked directly, so a failure says
        # "not hashable" rather than arriving from inside an unrelated call.
        current = platform.PLATFORM.GetCurrentContext()
        assert current, 'no current context after OSMesaMakeCurrent'
        hash(current)

        glClearColor(*GREEN)
        glClear(GL_COLOR_BUFFER_BIT)
        glFinish()

        rendered = numpy.frombuffer(
            bytes(bytearray(buffer)), dtype=numpy.uint8,
        ).reshape((HEIGHT, WIDTH, 4))
        centre = tuple(int(channel) for channel in rendered[HEIGHT // 2,
                                                            WIDTH // 2])
        assert centre == GREEN_BYTES, (
            'cleared to %r, the buffer holds %r' % (GREEN_BYTES, centre))

        # Keying per-context state by this context, which is what #33 reports
        # failing: `storage.get(context)` raised `TypeError: unhashable type`
        # before anything had a chance to say which context it meant.
        contextdata.setValue('a-probe', [1, 2, 3], context=current)
        assert contextdata.getValue('a-probe', context=current) == [1, 2, 3], (
            'per-context storage did not answer with what was put in it')
        contextdata.delValue('a-probe', context=current)

        # And the call the ticket was making when it met that.
        glVertexAttribPointer(0, 2, GL_FLOAT, False, 0,
                              numpy.zeros((3, 2), dtype=numpy.float32))
        assert glGetError() == 0, 'glVertexAttribPointer left an error pending'

        print('OK')
    finally:
        OSMesaDestroyContext(context)


if __name__ == '__main__':
    checkutils.run_check(check_osmesa)
