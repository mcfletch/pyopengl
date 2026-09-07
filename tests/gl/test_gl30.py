#! /usr/bin/env python3
"""GL 3.0 (core): FBO/renderbuffer/VAO, transform feedback, integer attribs,
unsigned uniforms, per-buffer clears and conditional render."""

import unittest
import ctypes
from arraycompat import np, object_names

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestGL30(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def test_introspection_and_string(self):
        self.assertTrue(self.getString(GL_VERSION))
        n = self.getInteger(GL_NUM_EXTENSIONS)
        self.assertTrue(self.getStringi(GL_EXTENSIONS, 0))
        self.assertGreater(n, 0)
        glGetBooleani_v(GL_COLOR_WRITEMASK, 0, np.zeros(4, 'B'))
        glGetIntegeri_v(GL_TRANSFORM_FEEDBACK_BUFFER_BINDING, 0, np.zeros(1, 'i'))
        self.check_error('introspection')

    def test_vertex_arrays_and_fbo(self):
        vao = glGenVertexArrays(1)
        glBindVertexArray(int(vao))
        self.assertTrue(glIsVertexArray(int(vao)))

        # a multisample renderbuffer (exercises the multisample storage call)
        ms = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, ms)
        glRenderbufferStorageMultisample(GL_RENDERBUFFER, 4, GL_RGBA8, 16, 16)
        # a depth renderbuffer for the FBO
        depth = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, depth)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, 16, 16)
        self.assertTrue(glIsRenderbuffer(depth))
        glGetRenderbufferParameteriv(GL_RENDERBUFFER, GL_RENDERBUFFER_WIDTH)

        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA8, 16, 16, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )
        glGenerateMipmap(GL_TEXTURE_2D)

        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0
        )
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depth
        )
        self.assertEqual(
            glCheckFramebufferStatus(GL_FRAMEBUFFER), GL_FRAMEBUFFER_COMPLETE
        )
        self.assertTrue(glIsFramebuffer(fbo))
        glGetFramebufferAttachmentParameteriv(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE
        )

        # blit into a second colour FBO
        tex2 = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex2)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA8, 16, 16, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )
        fbo2 = glGenFramebuffers(1)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fbo2)
        glFramebufferTexture2D(
            GL_DRAW_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex2, 0
        )
        glBindFramebuffer(GL_READ_FRAMEBUFFER, fbo)
        glBlitFramebuffer(0, 0, 16, 16, 0, 0, 16, 16, GL_COLOR_BUFFER_BIT, GL_NEAREST)
        # 1D/3D/array colour attachments via the dimension-specific entry points
        f3 = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, f3)
        t1 = glGenTextures(1)
        glBindTexture(GL_TEXTURE_1D, t1)
        glTexImage1D(GL_TEXTURE_1D, 0, GL_RGBA8, 16, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glFramebufferTexture1D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_1D, t1, 0
        )
        t3 = glGenTextures(1)
        glBindTexture(GL_TEXTURE_3D, t3)
        glTexImage3D(
            GL_TEXTURE_3D, 0, GL_RGBA8, 16, 16, 2, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
        )
        glFramebufferTexture3D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_3D, t3, 0, 0
        )
        ta = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, ta)
        glTexImage3D(
            GL_TEXTURE_2D_ARRAY,
            0,
            GL_RGBA8,
            16,
            16,
            2,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            None,
        )
        glFramebufferTextureLayer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, ta, 0, 1)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glDeleteFramebuffers(1, object_names(fbo))
        glDeleteRenderbuffers(1, object_names(depth))
        glDeleteVertexArrays(1, object_names(int(vao)))
        self.check_error('vao/fbo')

    def test_clear_and_masks(self):
        glClearBufferfv(GL_COLOR, 0, np.array([0, 0.25, 0, 1], 'f'))
        glClearBufferfi(GL_DEPTH_STENCIL, 0, 1.0, 0)
        glColorMaski(0, GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        glEnablei(GL_BLEND, 0)
        self.assertTrue(glIsEnabledi(GL_BLEND, 0))
        glDisablei(GL_BLEND, 0)
        glClampColor(GL_CLAMP_READ_COLOR, GL_FALSE)
        # integer/unsigned clears need correctly-typed colour attachments
        itex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, itex)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA32I, 4, 4, 0, GL_RGBA_INTEGER, GL_INT, None
        )
        ifbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, ifbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, itex, 0
        )
        glClearBufferiv(GL_COLOR, 0, np.zeros(4, 'i'))
        utex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, utex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA32UI,
            4,
            4,
            0,
            GL_RGBA_INTEGER,
            GL_UNSIGNED_INT,
            None,
        )
        ufbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, ufbo)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, utex, 0
        )
        glClearBufferuiv(GL_COLOR, 0, np.zeros(4, 'I'))
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.check_error('clears/masks')

    def test_uint_and_integer_attribs(self):
        program = _build_uint_program()
        glUseProgram(program)
        def loc(n):
            return glGetUniformLocation(program, n)
        glUniform1ui(loc('uu'), 1)
        glUniform2ui(loc('uu2'), 1, 2)
        glUniform3ui(loc('uu3'), 1, 2, 3)
        glUniform4ui(loc('uu4'), 1, 2, 3, 4)
        glUniform1uiv(loc('uu'), 1, np.array([1], 'I'))
        glUniform2uiv(loc('uu2'), 1, np.array([1, 2], 'I'))
        glUniform3uiv(loc('uu3'), 1, np.array([1, 2, 3], 'I'))
        glUniform4uiv(loc('uu4'), 1, np.array([1, 2, 3, 4], 'I'))
        glGetUniformuiv(program, loc('uu'), np.zeros(1, 'I'))
        self.assertNotEqual(glGetFragDataLocation(program, 'fragColor'), -1)
        glBindFragDataLocation(program, 0, 'fragColor')

        glVertexAttribI1i(3, 1)
        glVertexAttribI2i(3, 1, 2)
        glVertexAttribI3i(3, 1, 2, 3)
        glVertexAttribI4i(3, 1, 2, 3, 4)
        glVertexAttribI1ui(3, 1)
        glVertexAttribI2ui(3, 1, 2)
        glVertexAttribI3ui(3, 1, 2, 3)
        glVertexAttribI4ui(3, 1, 2, 3, 4)
        glVertexAttribI1iv(3, np.zeros(1, 'i'))
        glVertexAttribI2iv(3, np.zeros(2, 'i'))
        glVertexAttribI3iv(3, np.zeros(3, 'i'))
        glVertexAttribI4iv(3, np.zeros(4, 'i'))
        glVertexAttribI1uiv(3, np.zeros(1, 'I'))
        glVertexAttribI2uiv(3, np.zeros(2, 'I'))
        glVertexAttribI3uiv(3, np.zeros(3, 'I'))
        glVertexAttribI4uiv(3, np.zeros(4, 'I'))
        glVertexAttribI4bv(3, np.zeros(4, 'b'))
        glVertexAttribI4sv(3, np.zeros(4, 'h'))
        glVertexAttribI4ubv(3, np.zeros(4, 'B'))
        glVertexAttribI4usv(3, np.zeros(4, 'H'))
        buf = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, np.zeros(16, 'i'), GL_STATIC_DRAW)
        glVertexAttribIPointer(3, 4, GL_INT, 0, None)
        glGetVertexAttribIiv(3, GL_VERTEX_ATTRIB_ARRAY_SIZE)
        glGetVertexAttribIuiv(3, GL_VERTEX_ATTRIB_ARRAY_SIZE)
        self.check_error('uint/integer attribs')

    def test_integer_texture_params(self):
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameterIiv(
            GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1, 2, 3, 4], 'i')
        )
        glTexParameterIuiv(
            GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.array([1, 2, 3, 4], 'I')
        )
        glGetTexParameterIiv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'i'))
        glGetTexParameterIuiv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'I'))
        self.check_error('integer tex params')

    def test_transform_feedback_and_conditional(self):
        vs = '#version 150 core\nin float v; out float o; void main(){o=v*2.0; gl_Position=vec4(0);}'
        fs = '#version 150 core\nout vec4 c; void main(){c=vec4(1.0);}'
        from OpenGL.GL import shaders

        vso = shaders.compileShader(vs, GL_VERTEX_SHADER)
        fso = shaders.compileShader(fs, GL_FRAGMENT_SHADER)
        prog = glCreateProgram()
        glAttachShader(prog, vso)
        glAttachShader(prog, fso)
        glTransformFeedbackVaryings(prog, 1, _char_pp(['o']), GL_INTERLEAVED_ATTRIBS)
        glLinkProgram(prog)
        glUseProgram(prog)
        glGetTransformFeedbackVarying(prog, 0, 64)

        src = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, src)
        glBufferData(GL_ARRAY_BUFFER, np.array([1, 2, 3], 'f'), GL_STATIC_DRAW)
        loc = glGetAttribLocation(prog, 'v')
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 1, GL_FLOAT, False, 0, None)
        dst = glGenBuffers(1)
        glBindBuffer(GL_TRANSFORM_FEEDBACK_BUFFER, dst)
        glBufferData(GL_TRANSFORM_FEEDBACK_BUFFER, 12, None, GL_DYNAMIC_COPY)
        glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, dst)
        glBindBufferRange(GL_TRANSFORM_FEEDBACK_BUFFER, 0, dst, 0, 12)
        glEnable(GL_RASTERIZER_DISCARD)
        glBeginTransformFeedback(GL_POINTS)
        glDrawArrays(GL_POINTS, 0, 3)
        glEndTransformFeedback()
        glDisable(GL_RASTERIZER_DISCARD)
        glMapBufferRange(GL_TRANSFORM_FEEDBACK_BUFFER, 0, 12, GL_MAP_READ_BIT)
        glUnmapBuffer(GL_TRANSFORM_FEEDBACK_BUFFER)
        # exercise flush-explicit on a write mapping
        glBindBuffer(GL_ARRAY_BUFFER, src)
        glMapBufferRange(
            GL_ARRAY_BUFFER, 0, 12, GL_MAP_WRITE_BIT | GL_MAP_FLUSH_EXPLICIT_BIT
        )
        glFlushMappedBufferRange(GL_ARRAY_BUFFER, 0, 12)
        glUnmapBuffer(GL_ARRAY_BUFFER)
        q = glGenQueries(1)
        q = int(q[0]) if hasattr(q, '__len__') else int(q)
        glBeginQuery(GL_SAMPLES_PASSED, q)
        glEndQuery(GL_SAMPLES_PASSED)
        glBeginConditionalRender(q, GL_QUERY_WAIT)
        glEndConditionalRender()
        self.check_error('transform feedback')


def _build_uint_program():
    from OpenGL.GL import shaders

    vs = '''#version 150 core
    in ivec4 iattr;
    uniform uint uu; uniform uvec2 uu2; uniform uvec3 uu3; uniform uvec4 uu4;
    flat out uint vo;
    void main(){ vo = uu+uu2.x+uu3.y+uu4.z+uint(iattr.x); gl_Position=vec4(0); }'''
    fs = '''#version 150 core
    flat in uint vo; out vec4 fragColor;
    void main(){ fragColor = vec4(float(vo)); }'''
    return shaders.compileProgram(
        shaders.compileShader(vs, GL_VERTEX_SHADER),
        shaders.compileShader(fs, GL_FRAGMENT_SHADER),
    )


class TestRenderingIntoAFramebufferObject(GLTestCase):
    """A colour texture and a depth renderbuffer, drawn into and textured from.

    The round trip rather than the pieces: an attachment set up wrongly is
    reported by glCheckFramebufferStatus, and one set up in a way the driver
    accepts but PyOpenGL described wrongly shows up as a draw that goes
    nowhere.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    SIDE = 128

    def test_a_texture_attachment_can_be_drawn_into_and_then_read_from(self):
        self.require_feature('framebuffer objects', (3, 0),
                             'GL_ARB_framebuffer_object')
        fbo = int(glGenFramebuffers(1))
        self.defer_cleanup(lambda: glDeleteFramebuffers(1, object_names(fbo)))

        with self.framebuffer(fbo):
            depth = int(glGenRenderbuffers(1))
            self.defer_cleanup(lambda: glDeleteRenderbuffers(1, object_names(depth)))
            glBindRenderbuffer(GL_RENDERBUFFER, depth)
            glRenderbufferStorage(
                GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.SIDE, self.SIDE
            )
            glFramebufferRenderbuffer(
                GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depth
            )

            colour = int(glGenTextures(1))
            self.defer_cleanup(lambda: glDeleteTextures(1, object_names(colour)))
            glBindTexture(GL_TEXTURE_2D, colour)
            # Without a filter the texture is incomplete and the driver
            # answers GL_FRAMEBUFFER_UNSUPPORTED rather than saying why.
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexImage2D(
                GL_TEXTURE_2D, 0, GL_RGB8, self.SIDE, self.SIDE, 0,
                GL_RGB, GL_UNSIGNED_BYTE, None,
            )
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, colour, 0
            )

            self.assertEqual(
                glCheckFramebufferStatus(GL_FRAMEBUFFER), GL_FRAMEBUFFER_COMPLETE
            )

            glPushAttrib(GL_VIEWPORT_BIT)  # the viewport is the context's
            try:
                glViewport(0, 0, self.SIDE, self.SIDE)
                glClearColor(1.0, 0.0, 0.0, 1.0)
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                self.assert_pixel(self.SIDE // 2, self.SIDE // 2, (255, 0, 0, 255))
            finally:
                glPopAttrib()
        self.check_error('rendering into a framebuffer object')


if __name__ == '__main__':
    unittest.main()
