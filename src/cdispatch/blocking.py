"""Which entry points can block, and therefore must release the GIL.

The ctypes implementation reaches the driver through a ``CDLL`` function
pointer, and ctypes releases the GIL around every foreign call.  A generated
stub calls a raw function pointer, so it holds the GIL unless it is written not
to -- and a call that waits on the GPU then stops every other Python thread for
as long as it waits.  Measured on a 4096x4096 ``glReadPixels``: 36 ms during
which a second thread ran three times, where ctypes let it run 559 times.

Releasing costs 15-25 ns against ``glBindTexture``'s 57, so doing it on every
call would be a third of the dispatch win spent on calls that never block.
This is the list of the ones that do.

Being wrong in one direction costs a little speed; being wrong in the other
costs the property that makes a threaded program work at all.  So where a
family is arguable it is listed.
"""

import re

__all__ = ['blocks', 'BLOCKING_EXACT', 'BLOCKING_PATTERNS']

#: Names that block, exactly.  Suffixed vendor forms are covered by the
#: patterns below rather than repeated here.
BLOCKING_EXACT = frozenset(
    [
        # Waiting for the driver to catch up is the whole purpose of these.
        'glFinish',
        'glFlush',
        # Fences and queries: the caller is asking to be told when the GPU is
        # done, and may be told by waiting.
        'glClientWaitSync',
        'glWaitSync',
        'glFinishFenceNV',
        'glTestFenceNV',
        'glFinishFenceAPPLE',
        'glTestObjectAPPLE',
        # Compilation and linking happen on the CPU and take milliseconds.
        'glCompileShader',
        'glLinkProgram',
        'glSpecializeShader',
        'glValidateProgram',
        'glProgramBinary',
        'glGetProgramBinary',
        # Swap: under vsync this is the frame wait.
        'eglSwapBuffers',
        'eglWaitClient',
        'eglWaitGL',
        'eglWaitNative',
        'eglClientWaitSync',
        'eglClientWaitSyncKHR',
        'eglClientWaitSyncNV',
        'glXSwapBuffers',
        'glXWaitGL',
        'glXWaitX',
        'wglSwapBuffers',
        'wglSwapLayerBuffers',
    ]
)

#: Families, matched on the whole name.  A readback or a mapping stalls the
#: pipeline; a large upload can too, and the upload families are the ones a
#: loader thread is most likely to be running alongside.
BLOCKING_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r'^gl(Read|Readn)Pixels\w*$',
        r'^glGet(n?)(Compressed)?Tex(ture)?(Sub)?Image\w*$',
        r'^glGetTextureSubImage\w*$',
        r'^gl(Map|Unmap)(Named)?Buffer\w*$',
        r'^glFlushMapped(Named)?BufferRange\w*$',
        r'^glGetBufferSubData\w*$',
        r'^glGetQueryObject\w*$',        # may wait for the result to be ready
        r'^glGetSynciv\w*$',
        r'^gl(Named)?BufferData\w*$',    # a large upload stalls
        r'^gl(Named)?BufferSubData\w*$',
        r'^glTex(ture)?(Sub)?Image[123]D\w*$',
        r'^glCompressedTex(ture)?(Sub)?Image[123]D\w*$',
        r'^glCopyTex(ture)?(Sub)?Image[123]D\w*$',
        r'^glBlitFramebuffer\w*$',
        r'^glDispatchCompute\w*$',
        r'^glWaitSemaphore\w*$',
        r'^glSignalSemaphore\w*$',
        r'^egl(Create|Destroy)Sync\w*$',
        r'^eglSwapBuffersWithDamage\w*$',
    )
)


def blocks(name):
    """Whether this entry point can wait, and so must release the GIL."""
    if name in BLOCKING_EXACT:
        return True
    return any(pattern.match(name) for pattern in BLOCKING_PATTERNS)
