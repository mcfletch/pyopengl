#! /usr/bin/env python3
"""EXT / OVR OpenGL-ES extensions the NVIDIA driver exposes beyond the Mesa
baseline: transform-feedback draws, multisampled render-to-texture, raster
multisample, external-semaphore object management, sparse textures, window
rectangles and multiview multisampled render-to-texture.

Functional tests -- real objects and real calls with a clean error state.
External-semaphore signal/wait/import operate only on imported Vulkan/Direct3D
handles and are skipped with a reason (not counted as covered).
"""

import unittest
import ctypes
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from egltestcase import ESTestCase

from OpenGL.GLES3 import *  # noqa: F401,F403


class TestESNVIDIAExtra(ESTestCase):
    api = 'gles'
    gl_version = (3, 2)

    # --- GL_EXT_multisampled_render_to_texture ---------------------------
    def test_ext_multisampled_render_to_texture(self):
        self.require_extension('GL_EXT_multisampled_render_to_texture')
        from OpenGL.GLES2.EXT.multisampled_render_to_texture import (
            glRenderbufferStorageMultisampleEXT,
        )
        # name collides with a desktop-GL command; see require_entrypoint
        self.require_entrypoint(
            glRenderbufferStorageMultisampleEXT, 'glRenderbufferStorageMultisampleEXT'
        )

        rbo = one(glGenRenderbuffers(1))
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorageMultisampleEXT(GL_RENDERBUFFER, 4, GL_RGBA8, 8, 8)
        fbo = one(glGenFramebuffers(1))
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_RENDERBUFFER, rbo
        )
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('ext multisampled render to texture')
        # The implicit-multisample *texture* attach drives an on-screen resolve
        # and needs a window-system framebuffer; under a headless pbuffer the
        # desktop driver null-derefs (segfault), so it is not exercised here.

    # --- GL_EXT_raster_multisample ---------------------------------------
    def test_ext_raster_multisample(self):
        self.require_extension('GL_EXT_raster_multisample')
        from OpenGL.GLES2.EXT.raster_multisample import glRasterSamplesEXT

        glRasterSamplesEXT(4, GL_TRUE)
        glRasterSamplesEXT(0, GL_FALSE)
        self.check_error('ext raster multisample')

    # --- GL_EXT_semaphore ------------------------------------------------
    def test_ext_semaphore(self):
        self.require_extension('GL_EXT_semaphore')
        from OpenGL.GLES2.EXT.semaphore import (
            glGenSemaphoresEXT, glDeleteSemaphoresEXT, glIsSemaphoreEXT,
            glGetUnsignedBytevEXT, glGetUnsignedBytei_vEXT,
        )
        from OpenGL.GLES2.EXT.memory_object import (
            GL_DRIVER_UUID_EXT, GL_DEVICE_UUID_EXT, GL_NUM_DEVICE_UUIDS_EXT,
        )

        sems = np.zeros(2, 'u4')
        glGenSemaphoresEXT(2, sems)
        # only imported semaphores report TRUE; just exercise the query
        glIsSemaphoreEXT(int(sems[0]))
        glGetUnsignedBytevEXT(GL_DRIVER_UUID_EXT, np.zeros(16, 'B'))
        count = int(self.getInteger(GL_NUM_DEVICE_UUIDS_EXT))
        if count:
            glGetUnsignedBytei_vEXT(GL_DEVICE_UUID_EXT, 0, np.zeros(16, 'B'))
        glDeleteSemaphoresEXT(2, sems)
        self.check_error('ext semaphore')
        # signal/wait and the D3D12 fence parameter need imported handles.

    def test_ext_semaphore_fd(self):
        self.require_extension('GL_EXT_semaphore_fd')
        self.skipTest('importing a semaphore requires an external Vulkan/opaque fd')

    # --- GL_EXT_sparse_texture -------------------------------------------
    def test_ext_sparse_texture(self):
        self.require_extension('GL_EXT_sparse_texture')
        from OpenGL.GLES2.EXT.sparse_texture import (
            glTexPageCommitmentEXT, GL_TEXTURE_SPARSE_EXT,
            GL_VIRTUAL_PAGE_SIZE_X_EXT, GL_VIRTUAL_PAGE_SIZE_Y_EXT,
        )
        # name collides with a desktop-GL command; see require_entrypoint
        self.require_entrypoint(glTexPageCommitmentEXT, 'glTexPageCommitmentEXT')

        tex = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_SPARSE_EXT, GL_TRUE)
        buf = np.zeros(1, 'i')
        glGetInternalformativ(GL_TEXTURE_2D, GL_RGBA8, GL_VIRTUAL_PAGE_SIZE_X_EXT, 1, buf)
        px = int(buf[0]) or 128
        glGetInternalformativ(GL_TEXTURE_2D, GL_RGBA8, GL_VIRTUAL_PAGE_SIZE_Y_EXT, 1, buf)
        py = int(buf[0]) or 128
        glTexStorage2D(GL_TEXTURE_2D, 1, GL_RGBA8, px, py)
        glTexPageCommitmentEXT(GL_TEXTURE_2D, 0, 0, 0, 0, px, py, 1, GL_TRUE)
        self.check_error('ext sparse texture')

    # --- GL_EXT_window_rectangles ----------------------------------------
    def test_ext_window_rectangles(self):
        self.require_extension('GL_EXT_window_rectangles')
        from OpenGL.GLES2.EXT.window_rectangles import (
            glWindowRectanglesEXT, GL_INCLUSIVE_EXT, GL_EXCLUSIVE_EXT,
        )

        rects = np.array([0, 0, 4, 4], 'i')
        glWindowRectanglesEXT(GL_EXCLUSIVE_EXT, 1, rects)
        glWindowRectanglesEXT(GL_INCLUSIVE_EXT, 1, rects)
        glWindowRectanglesEXT(GL_EXCLUSIVE_EXT, 0, None)
        self.check_error('ext window rectangles')

    # --- GL_EXT_draw_transform_feedback ----------------------------------
    def test_ext_draw_transform_feedback(self):
        self.require_extension('GL_EXT_draw_transform_feedback')
        from OpenGL.GLES2.EXT.draw_transform_feedback import (
            glDrawTransformFeedbackEXT, glDrawTransformFeedbackInstancedEXT,
        )
        # These ES-only EXT entry points resolve fine in an ES-only process, but
        # PyOpenGL caches the pointer as null when desktop-GL tests have already
        # run earlier under the shared PYOPENGL_PLATFORM=egl process; guard so a
        # combined run skips rather than spuriously failing.
        if not bool(glDrawTransformFeedbackEXT):
            self.skipTest('draw_transform_feedback entry point unresolved in this process')
        from OpenGL.GLES3 import (
            glTransformFeedbackVaryings, glBeginTransformFeedback,
            glEndTransformFeedback, glGenTransformFeedbacks,
            glBindTransformFeedback, GL_TRANSFORM_FEEDBACK,
            GL_INTERLEAVED_ATTRIBS, glBindBufferBase, GL_TRANSFORM_FEEDBACK_BUFFER,
            GL_RASTERIZER_DISCARD,
        )

        vs = '#version 320 es\nin float v; out float w; void main(){ w = v + 1.0; gl_Position = vec4(0.0); gl_PointSize = 1.0; }'
        fs = '#version 320 es\nprecision mediump float; out vec4 c; void main(){ c = vec4(1.0); }'
        from OpenGL.GLES2 import shaders
        from OpenGL.GLES2 import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER
        vso = shaders.compileShader(vs, GL_VERTEX_SHADER)
        fso = shaders.compileShader(fs, GL_FRAGMENT_SHADER)
        program = glCreateProgram()
        glAttachShader(program, vso)
        glAttachShader(program, fso)
        glTransformFeedbackVaryings(program, ['w'], GL_INTERLEAVED_ATTRIBS)
        glLinkProgram(program)
        glUseProgram(program)

        vao = one(glGenVertexArrays(1))
        glBindVertexArray(vao)
        tf = one(glGenTransformFeedbacks(1))
        glBindTransformFeedback(GL_TRANSFORM_FEEDBACK, tf)
        tbo = one(glGenBuffers(1))
        glBindBuffer(GL_TRANSFORM_FEEDBACK_BUFFER, tbo)
        glBufferData(GL_TRANSFORM_FEEDBACK_BUFFER, 16 * 4, None, GL_DYNAMIC_COPY)
        glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, tbo)

        glEnable(GL_RASTERIZER_DISCARD)
        glBeginTransformFeedback(GL_POINTS)
        glDrawArrays(GL_POINTS, 0, 4)
        glEndTransformFeedback()
        # now replay the captured primitives
        glDrawTransformFeedbackEXT(GL_POINTS, tf)
        glDrawTransformFeedbackInstancedEXT(GL_POINTS, tf, 2)
        glDisable(GL_RASTERIZER_DISCARD)
        glBindTransformFeedback(GL_TRANSFORM_FEEDBACK, 0)
        glUseProgram(0)
        self.check_error('ext draw transform feedback')

    # --- GL_OVR_multiview_multisampled_render_to_texture -----------------
    def test_ovr_multiview_multisampled_render_to_texture(self):
        self.require_extension('GL_OVR_multiview_multisampled_render_to_texture')
        # The multiview multisample attach drives an implicit on-screen resolve
        # and needs a window-system framebuffer; under a headless pbuffer the
        # desktop driver null-derefs (segfault), so it cannot be exercised here.
        self.skipTest('multiview multisampled attach requires a window-system framebuffer')


if __name__ == '__main__':
    unittest.main()
