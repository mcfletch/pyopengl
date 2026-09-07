#! /usr/bin/env python3
"""GLES3.2: KHR_debug -- message callback/insert/control, groups and labels."""

import unittest
import ctypes

from arraycompat import one
from egltestcase import ESTestCase

from OpenGL.GLES2 import (
    GL_DONT_CARE,
    GL_TRUE,
    GL_NO_ERROR,
    glEnable,
    glGenBuffers,
    glBindBuffer,
    GL_ARRAY_BUFFER,
)
from OpenGL.GLES2.ES.VERSION_3_2 import (
    GLDEBUGPROC,
    GL_DEBUG_OUTPUT,
    GL_DEBUG_OUTPUT_SYNCHRONOUS,
    GL_DEBUG_SOURCE_APPLICATION,
    GL_DEBUG_TYPE_OTHER,
    GL_DEBUG_SEVERITY_NOTIFICATION,
    GL_DEBUG_CALLBACK_FUNCTION,
    GL_BUFFER,
    glDebugMessageControl,
    glDebugMessageInsert,
    glDebugMessageCallback,
    glGetDebugMessageLog,
    glPushDebugGroup,
    glPopDebugGroup,
    glObjectLabel,
    glGetObjectLabel,
    glObjectPtrLabel,
    glGetObjectPtrLabel,
    glGetPointerv,
)


def _decode_label(result):
    """Decode a [chars, length] (or [length, chars]) label return to str."""
    chars = next(x for x in result if hasattr(x, '__len__') and len(x) > 1)
    return bytes(bytearray(int(c) for c in chars)).split(b'\x00')[0].decode()


class TestES32Debug(ESTestCase):
    api = 'gles'
    gl_version = (3, 2)

    def test_debug_messages(self):
        captured = []

        @GLDEBUGPROC
        def callback(source, msgtype, msgid, severity, length, message, user):
            if isinstance(message, bytes):
                captured.append(message[:length])
            else:
                captured.append(ctypes.string_at(message, length))
            return 0

        self._callback = callback  # keep alive
        glEnable(GL_DEBUG_OUTPUT)
        glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS)
        glDebugMessageCallback(callback, None)
        glDebugMessageControl(
            GL_DONT_CARE, GL_DONT_CARE, GL_DONT_CARE, 0, None, GL_TRUE
        )
        glDebugMessageInsert(
            GL_DEBUG_SOURCE_APPLICATION,
            GL_DEBUG_TYPE_OTHER,
            1,
            GL_DEBUG_SEVERITY_NOTIFICATION,
            -1,
            b'hello-debug',
        )
        self.assertTrue(
            any(b'hello-debug' in m for m in captured),
            'synchronous debug callback did not fire: %r' % (captured,),
        )

        # the callback pointer is retrievable
        ptr = ctypes.c_void_p()
        glGetPointerv(GL_DEBUG_CALLBACK_FUNCTION, ctypes.byref(ptr))

        # draining the log is a no-op now (synchronous callback consumed it)
        try:
            glGetDebugMessageLog(1, 256)
        except Exception:
            pass

    def test_groups_and_labels(self):
        glPushDebugGroup(GL_DEBUG_SOURCE_APPLICATION, 0, -1, b'group')
        glPopDebugGroup()

        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glObjectLabel(GL_BUFFER, buf, -1, b'my-buffer')
        self.assertEqual(
            _decode_label(glGetObjectLabel(GL_BUFFER, buf, 64)), 'my-buffer'
        )
        self.check_error('groups/labels')

    def test_ptr_label(self):
        from OpenGL.GLES3 import (
            glFenceSync,
            glDeleteSync,
            GL_SYNC_GPU_COMMANDS_COMPLETE,
        )

        sync = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
        glObjectPtrLabel(sync, -1, b'my-sync')
        glGetObjectPtrLabel(sync, 64)
        self.check_error('ptr label')
        glDeleteSync(sync)


if __name__ == '__main__':
    unittest.main()
