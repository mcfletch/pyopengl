#! /usr/bin/env python3
"""KHR/EXT debug, robustness, debug-label, EGL-image and remaining
multi-draw / separate-program entry points."""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase
from OpenGL.GLES2 import (
    GL_DONT_CARE,
    GL_TRUE,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    GL_NO_ERROR,
    GL_VERTEX_SHADER,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    glGenBuffers,
    glBindBuffer,
    GL_ARRAY_BUFFER,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_STATIC_DRAW,
    glBufferData,
    GL_TEXTURE_2D,
    glGenTextures,
    glBindTexture,
    GL_RENDERBUFFER,
    glGenRenderbuffers,
    glBindRenderbuffer,
)

from OpenGL.GLES2.KHR import debug as khr_debug
from OpenGL.GLES2.KHR.debug import (
    GL_BUFFER_KHR as GL_BUFFER,
    GL_DEBUG_SOURCE_APPLICATION_KHR as GL_DEBUG_SOURCE_APPLICATION,
    GL_DEBUG_TYPE_OTHER_KHR as GL_DEBUG_TYPE_OTHER,
    GL_DEBUG_SEVERITY_NOTIFICATION_KHR as GL_DEBUG_SEVERITY_NOTIFICATION,
    GL_DEBUG_CALLBACK_FUNCTION_KHR,
)
from OpenGL.GLES2.KHR import robustness as khr_rob
from OpenGL.GLES2.EXT import robustness as ext_rob
from OpenGL.GLES2.EXT import debug_label as ext_label
from OpenGL.GLES2.OES import EGL_image as oes_eglimage
from OpenGL.GLES2.OES import EGL_image_external as oes_eglimage_ext
from OpenGL.GLES2.EXT import EGL_image_storage as ext_eglstore
from OpenGL.GLES2.EXT import separate_shader_objects as sso
from OpenGL.GLES2.EXT import multi_draw_arrays as mda
from OpenGL.GLES2.EXT import multi_draw_indirect as mdi
from OpenGL.GLES2.EXT import draw_elements_base_vertex as debv
from OpenGL.GLES2.EXT import memory_object_fd as mem_fd


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestDebugRobustExtensions(ESTestCase):
    api = 'gles'
    gl_version = (3, 0)

    def test_khr_debug(self):
        self.require_extension('GL_KHR_debug')
        with self.exercise(
            'GL_KHR_debug is advertised; a driver need not serve every entry point in it'
        ):
            captured = []

            @khr_debug.GLDEBUGPROCKHR
            def cb(source, t, i, sev, length, message, user):
                captured.append(1)
                return 0

            self._cb = cb
            khr_debug.glDebugMessageCallbackKHR(cb, None)
            khr_debug.glDebugMessageControlKHR(
                GL_DONT_CARE, GL_DONT_CARE, GL_DONT_CARE, 0, None, GL_TRUE
            )
            khr_debug.glDebugMessageInsertKHR(
                GL_DEBUG_SOURCE_APPLICATION,
                GL_DEBUG_TYPE_OTHER,
                1,
                GL_DEBUG_SEVERITY_NOTIFICATION,
                -1,
                b'hi',
            )
            khr_debug.glPushDebugGroupKHR(GL_DEBUG_SOURCE_APPLICATION, 0, -1, b'grp')
            khr_debug.glPopDebugGroupKHR()
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            khr_debug.glObjectLabelKHR(GL_BUFFER, buf, -1, b'lbl')
            khr_debug.glGetObjectLabelKHR(
                GL_BUFFER, buf, 64, (ctypes.c_int * 1)(), (ctypes.c_char * 64)()
            )
            ptr = ctypes.c_void_p()
            khr_debug.glGetPointervKHR(
                GL_DEBUG_CALLBACK_FUNCTION_KHR, ctypes.byref(ptr)
            )
            khr_debug.glGetDebugMessageLogKHR(
                4,
                256,
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'I'),
                np.zeros(4, 'i'),
                (ctypes.c_char * 256)(),
            )
            from OpenGL.GLES3 import (
                glFenceSync,
                glDeleteSync,
                GL_SYNC_GPU_COMMANDS_COMPLETE,
            )

            sync = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
            khr_debug.glObjectPtrLabelKHR(sync, -1, b'sync')
            khr_debug.glGetObjectPtrLabelKHR(
                sync, 64, (ctypes.c_int * 1)(), (ctypes.c_char * 64)()
            )
            glDeleteSync(sync)

    def test_khr_robustness(self):
        self.require_extension('GL_KHR_robustness')
        with self.exercise(
            'GL_KHR_robustness is advertised; a driver need not serve every entry point in it'
        ):
            khr_rob.glGetGraphicsResetStatusKHR()
            size = self.width * self.height * 4
            khr_rob.glReadnPixelsKHR(
                0,
                0,
                self.width,
                self.height,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                size,
                (ctypes.c_ubyte * size)(),
            )
            program = self.compile_program(
                'attribute vec4 p; void main(){gl_Position=p;}',
                'precision mediump float; uniform vec4 u; void main(){gl_FragColor=u;}',
            )
            from OpenGL.GLES2 import glUseProgram, glGetUniformLocation

            glUseProgram(program)
            loc = glGetUniformLocation(program, 'u')
            khr_rob.glGetnUniformfvKHR(program, loc, 16, np.zeros(4, 'f'))
            khr_rob.glGetnUniformivKHR(program, loc, 16, np.zeros(4, 'i'))
            khr_rob.glGetnUniformuivKHR(program, loc, 16, np.zeros(4, 'u4'))

    def test_ext_robustness(self):
        self.require_extension('GL_EXT_robustness')
        with self.exercise(
            'GL_EXT_robustness is advertised; a driver need not serve every entry point in it'
        ):
            ext_rob.glGetGraphicsResetStatusEXT()
            size = self.width * self.height * 4
            ext_rob.glReadnPixelsEXT(
                0,
                0,
                self.width,
                self.height,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                size,
                (ctypes.c_ubyte * size)(),
            )
            program = self.compile_program(
                'attribute vec4 p; void main(){gl_Position=p;}',
                'precision mediump float; uniform vec4 u; void main(){gl_FragColor=u;}',
            )
            from OpenGL.GLES2 import glUseProgram, glGetUniformLocation

            glUseProgram(program)
            loc = glGetUniformLocation(program, 'u')
            ext_rob.glGetnUniformfvEXT(program, loc, 16, np.zeros(4, 'f'))
            ext_rob.glGetnUniformivEXT(program, loc, 16, np.zeros(4, 'i'))

    def test_ext_debug_label(self):
        self.require_extension('GL_EXT_debug_label')
        with self.exercise(
            'GL_EXT_debug_label is advertised; a driver need not serve every entry point in it'
        ):
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            ext_label.glLabelObjectEXT(GL_BUFFER, buf, -1, b'lbl')
            ext_label.glGetObjectLabelEXT(
                GL_BUFFER, buf, 64, (ctypes.c_int * 1)(), (ctypes.c_char * 64)()
            )

    def test_ext_separate_shader_objects_legacy(self):
        self.require_extension('GL_EXT_separate_shader_objects')
        with self.exercise(
            'GL_EXT_separate_shader_objects is advertised; a driver need not serve every entry point in it'
        ):
            p = sso.glCreateShaderProgramEXT(
                GL_VERTEX_SHADER, 'void main(){gl_Position=vec4(0);}'
            )
            sso.glActiveProgramEXT(p)
            sso.glUseShaderProgramEXT(GL_VERTEX_SHADER, p)

    def test_egl_image_targets(self):
        self.require_extension('GL_OES_EGL_image')
        # no real EGLImage handle here, so these fail GL validation; the calls
        # still drive the wrappers (handle/target marshalling) -- exercise() tolerates
        with self.exercise(
            'GL_OES_EGL_image is advertised; a driver need not serve every entry point in it'
        ):
            glBindTexture(GL_TEXTURE_2D, one(glGenTextures(1)))
            img = ctypes.c_void_p(0)
            oes_eglimage.glEGLImageTargetTexture2DOES(GL_TEXTURE_2D, img)
            rb = one(glGenRenderbuffers(1))
            glBindRenderbuffer(GL_RENDERBUFFER, rb)
            oes_eglimage.glEGLImageTargetRenderbufferStorageOES(GL_RENDERBUFFER, img)
            oes_eglimage_ext.glEGLImageTargetTexture2DOES(GL_TEXTURE_2D, img)
            ext_eglstore.glEGLImageTargetTexStorageEXT(GL_TEXTURE_2D, img, None)
            ext_eglstore.glEGLImageTargetTextureStorageEXT(
                one(glGenTextures(1)), img, None
            )

    def test_multi_draw_elements_leftovers(self):
        self.require_extension('GL_EXT_multi_draw_arrays')
        with self.exercise(
            'GL_EXT_multi_draw_arrays is advertised; a driver need not serve every entry point in it'
        ):
            ebo = one(glGenBuffers(1))
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
            glBufferData(
                GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW
            )
            counts = np.array([3], 'i')
            offsets = (ctypes.c_void_p * 1)(0)  # byte offsets into bound EBO
            mda.glMultiDrawElementsEXT(
                GL_TRIANGLES, counts, GL_UNSIGNED_INT, offsets, 1
            )
            mdi.glMultiDrawElementsIndirectEXT(
                GL_TRIANGLES, GL_UNSIGNED_INT, None, 1, 0
            )
            debv.glMultiDrawElementsBaseVertexEXT(
                GL_TRIANGLES, counts, GL_UNSIGNED_INT, offsets, 1, np.array([0], 'i')
            )

    def test_ext_memory_object_fd(self):
        self.require_extension('GL_EXT_memory_object_fd')
        from OpenGL.GLES2.EXT import memory_object as _mem
        from OpenGL.GLES2.EXT.memory_object_fd import GL_HANDLE_TYPE_OPAQUE_FD_EXT

        # fd=-1 is invalid so the import fails GL validation; the wrapper still runs
        with self.exercise(
            'GL_EXT_memory_object_fd is advertised; a driver need not serve every entry point in it'
        ):
            ids = np.zeros(1, 'u4')
            _mem.glCreateMemoryObjectsEXT(1, ids)
            mem_fd.glImportMemoryFdEXT(
                int(ids[0]), 1024, GL_HANDLE_TYPE_OPAQUE_FD_EXT, -1
            )


if __name__ == '__main__':
    unittest.main()
