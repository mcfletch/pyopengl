#! /usr/bin/env python3
"""GL 2.0: programmable shaders, uniforms, vertex attributes, separate stencil."""

import unittest
from arraycompat import np, object_names, one

from gltestcase import GLTestCase
from OpenGL import error
from OpenGL.GL import *  # noqa: F401,F403

#: The smallest legal 3.30 vertex shader, for the case about `glShaderSource`
#: taking a `str` rather than about what the shader does.
SIMPLE_VERTEX_SHADER = '''#version 330 core
void main() { gl_Position = vec4(0, 0, 0, 1); }
'''

VERTEX = '''#version 110
attribute vec4 position;
uniform float uf; uniform vec2 uv2; uniform vec3 uv3; uniform vec4 uv4;
uniform int ui; uniform ivec2 ui2; uniform ivec3 ui3; uniform ivec4 ui4;
uniform mat2 m2; uniform mat3 m3; uniform mat4 m4;
void main() {
    float s = uf + uv2.x + uv3.y + uv4.z + float(ui + ui2.x + ui3.y + ui4.z)
        + m2[0][0] + m3[1][1] + m4[2][2];
    gl_Position = position * s;
}'''
FRAGMENT = '''#version 110
void main() { gl_FragColor = vec4(1.0); }'''


class TestGL20(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def _build_program(self):
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, VERTEX)
        glCompileShader(vs)
        self.assertEqual(
            one(glGetShaderiv(vs, GL_COMPILE_STATUS)), GL_TRUE, glGetShaderInfoLog(vs)
        )
        self.assertTrue(glIsShader(vs))
        self.assertIn(
            'position',
            glGetShaderSource(vs).decode()
            if isinstance(glGetShaderSource(vs), bytes)
            else glGetShaderSource(vs),
        )
        fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(fs, FRAGMENT)
        glCompileShader(fs)

        program = glCreateProgram()
        glAttachShader(program, vs)
        glAttachShader(program, fs)
        glBindAttribLocation(program, 0, 'position')
        glLinkProgram(program)
        self.assertEqual(
            one(glGetProgramiv(program, GL_LINK_STATUS)),
            GL_TRUE,
            glGetProgramInfoLog(program),
        )
        self.assertTrue(glIsProgram(program))
        self.assertEqual(
            set(int(s) for s in glGetAttachedShaders(program)), {int(vs), int(fs)}
        )
        glValidateProgram(program)
        glUseProgram(program)
        glGetActiveAttrib(program, 0)
        glGetActiveUniform(program, 0)
        self.assertEqual(glGetAttribLocation(program, 'position'), 0)
        self.assertNotEqual(glGetUniformLocation(program, 'uf'), -1)
        self.check_error('program lifecycle')
        return program

    def test_program_lifecycle(self):
        self._build_program()

    def test_uniforms(self):
        program = self._build_program()
        def loc(n):
            return glGetUniformLocation(program, n)
        glUniform1f(loc('uf'), 1.0)
        glUniform2f(loc('uv2'), 1, 2)
        glUniform3f(loc('uv3'), 1, 2, 3)
        glUniform4f(loc('uv4'), 1, 2, 3, 4)
        glUniform1i(loc('ui'), 1)
        glUniform2i(loc('ui2'), 1, 2)
        glUniform3i(loc('ui3'), 1, 2, 3)
        glUniform4i(loc('ui4'), 1, 2, 3, 4)
        glUniform1fv(loc('uf'), 1, np.array([2], 'f'))
        glUniform2fv(loc('uv2'), 1, np.array([1, 2], 'f'))
        glUniform3fv(loc('uv3'), 1, np.array([1, 2, 3], 'f'))
        glUniform4fv(loc('uv4'), 1, np.array([1, 2, 3, 4], 'f'))
        glUniform1iv(loc('ui'), 1, np.array([2], 'i'))
        glUniform2iv(loc('ui2'), 1, np.array([1, 2], 'i'))
        glUniform3iv(loc('ui3'), 1, np.array([1, 2, 3], 'i'))
        glUniform4iv(loc('ui4'), 1, np.array([1, 2, 3, 4], 'i'))
        glUniformMatrix2fv(loc('m2'), 1, False, np.eye(2, dtype='f'))
        glUniformMatrix3fv(loc('m3'), 1, False, np.eye(3, dtype='f'))
        glUniformMatrix4fv(loc('m4'), 1, False, np.eye(4, dtype='f'))
        glGetUniformfv(program, loc('uf'), np.zeros(1, 'f'))
        glGetUniformiv(program, loc('ui'), np.zeros(1, 'i'))
        self.check_error('uniforms')

    def test_vertex_attribs(self):
        glVertexAttrib1s(1, 0)
        glVertexAttrib1f(1, 0.0)
        glVertexAttrib1d(1, 0.0)
        glVertexAttrib2s(1, 0, 0)
        glVertexAttrib2f(1, 0, 0)
        glVertexAttrib2d(1, 0, 0)
        glVertexAttrib3s(1, 0, 0, 0)
        glVertexAttrib3f(1, 0, 0, 0)
        glVertexAttrib3d(1, 0, 0, 0)
        glVertexAttrib4s(1, 0, 0, 0, 1)
        glVertexAttrib4f(1, 0, 0, 0, 1)
        glVertexAttrib4d(1, 0, 0, 0, 1)
        glVertexAttrib1sv(1, np.zeros(1, 'h'))
        glVertexAttrib1fv(1, np.zeros(1, 'f'))
        glVertexAttrib1dv(1, np.zeros(1, 'd'))
        glVertexAttrib2sv(1, np.zeros(2, 'h'))
        glVertexAttrib2fv(1, np.zeros(2, 'f'))
        glVertexAttrib2dv(1, np.zeros(2, 'd'))
        glVertexAttrib3sv(1, np.zeros(3, 'h'))
        glVertexAttrib3fv(1, np.zeros(3, 'f'))
        glVertexAttrib3dv(1, np.zeros(3, 'd'))
        glVertexAttrib4sv(1, np.zeros(4, 'h'))
        glVertexAttrib4fv(1, np.zeros(4, 'f'))
        glVertexAttrib4dv(1, np.zeros(4, 'd'))
        glVertexAttrib4bv(1, np.zeros(4, 'b'))
        glVertexAttrib4iv(1, np.zeros(4, 'i'))
        glVertexAttrib4ubv(1, np.zeros(4, 'B'))
        glVertexAttrib4uiv(1, np.zeros(4, 'I'))
        glVertexAttrib4usv(1, np.zeros(4, 'H'))
        glVertexAttrib4Nbv(1, np.zeros(4, 'b'))
        glVertexAttrib4Niv(1, np.zeros(4, 'i'))
        glVertexAttrib4Nsv(1, np.zeros(4, 'h'))
        glVertexAttrib4Nub(1, 0, 0, 0, 0)
        glVertexAttrib4Nubv(1, np.zeros(4, 'B'))
        glVertexAttrib4Nuiv(1, np.zeros(4, 'I'))
        glVertexAttrib4Nusv(1, np.zeros(4, 'H'))
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, np.zeros(12, 'f'), GL_STATIC_DRAW)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 0, None)
        glGetVertexAttribfv(1, GL_CURRENT_VERTEX_ATTRIB)
        glGetVertexAttribdv(1, GL_CURRENT_VERTEX_ATTRIB)
        glGetVertexAttribiv(1, GL_VERTEX_ATTRIB_ARRAY_SIZE)
        glGetVertexAttribPointerv(1, GL_VERTEX_ATTRIB_ARRAY_POINTER)
        glDisableVertexAttribArray(1)
        self.check_error('vertex attribs')

    def test_shader_deletion(self):
        vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(vs, VERTEX)
        glCompileShader(vs)
        program = glCreateProgram()
        glAttachShader(program, vs)
        glDetachShader(program, vs)
        glDeleteShader(vs)
        glDeleteProgram(program)
        self.check_error('shader deletion')

    def test_separate_state(self):
        # Which name is right depends on what is bound to draw into, and
        # that is the backend's choice: a framebuffer object takes
        # GL_COLOR_ATTACHMENTi, the default framebuffer the per-buffer
        # names (glDrawBuffers did not accept GL_BACK until GL 4.5).
        glDrawBuffers(1, object_names(self.colour_buffer_name()))
        glStencilFuncSeparate(GL_FRONT, GL_ALWAYS, 1, 0xFF)
        glStencilMaskSeparate(GL_FRONT, 0xFF)
        glStencilOpSeparate(GL_FRONT, GL_KEEP, GL_KEEP, GL_KEEP)
        glBlendEquationSeparate(GL_FUNC_ADD, GL_FUNC_SUBTRACT)
        self.check_error('separate state')


class TestCompilingAShaderFromAString(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_a_source_string_reaches_the_compiler(self):
        """``glShaderSource`` takes str, and has to encode it itself.

        The driver wants a char** and a length; what it is given here is one
        Python string, so the wrapper builds both.  A compile failure is
        reported with the driver's own log, since a shader this small failing
        is a fact about the wrapper rather than about the shader.
        """
        self.require_feature('shaders', (2, 0), 'GL_ARB_shader_objects')
        glsl = self.getString(GL_SHADING_LANGUAGE_VERSION)
        leading = glsl.split(' ')[0].split('.')[:2]
        if [int(part) for part in leading] < [3, 3]:
            self.skipTest('this driver offers GLSL %s, below the 3.30 asked for'
                          % (glsl,))

        shader = glCreateShader(GL_VERTEX_SHADER)
        self.defer_cleanup(lambda: glDeleteShader(shader))
        glShaderSource(shader, SIMPLE_VERTEX_SHADER)
        glCompileShader(shader)
        self.assertTrue(
            one(glGetShaderiv(shader, GL_COMPILE_STATUS)),
            'the shader did not compile: %s' % (glGetShaderInfoLog(shader),),
        )


class TestSelectingSeveralDrawBuffers(GLTestCase):
    """``glDrawBuffers`` takes a count and an array of buffer names."""

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_naming_attachments_the_default_framebuffer_has_not_got(self):
        """Framebuffer zero has no colour attachments, so this is an error.

        Which is the point: the call has to reach the driver and be refused by
        it, rather than being refused by the wrapper for the wrong reason.
        """
        self.require_feature('glDrawBuffers', (2, 0), 'GL_ARB_draw_buffers')
        if self.draw_framebuffer():
            self.skipTest('this backend draws into a framebuffer object, which '
                          'does accept colour attachments')
        names = (GLenum * 2)(GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1)
        with self.assertRaises(error.GLError) as caught:
            glDrawBuffers(2, names)
        self.assertEqual(caught.exception.err, GL_INVALID_OPERATION)

    def test_naming_attachments_a_framebuffer_object_does_have(self):
        self.require_feature('framebuffer objects', (3, 0),
                             'GL_ARB_framebuffer_object')
        previous = one(glGetIntegerv(GL_READ_BUFFER))
        fbo = one(glGenFramebuffers(1))
        self.defer_cleanup(lambda: glDeleteFramebuffers(1, object_names(fbo)))
        with self.framebuffer(fbo):
            textures = glGenTextures(2)
            for index, texture in enumerate(textures):
                glBindTexture(GL_TEXTURE_2D, int(texture))
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 32, 32, 0,
                             GL_RGB, GL_UNSIGNED_BYTE, None)
                glFramebufferTexture2D(
                    GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0 + index,
                    GL_TEXTURE_2D, int(texture), 0,
                )
            names = (GLenum * 2)(GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1)
            glDrawBuffers(2, names)
            self.check_error('glDrawBuffers on a framebuffer object')

            if glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE:
                glReadBuffer(GL_COLOR_ATTACHMENT1)
                pixels = glReadPixels(0, 0, 10, 10, GL_RGB, GL_UNSIGNED_BYTE)
                self.assertEqual(len(pixels), 300, len(pixels))
            glDeleteTextures(2, object_names(*textures))
        # Back on the framebuffer the fixture draws into, so the buffer read
        # off it at the start is one it still accepts.
        glReadBuffer(previous)


if __name__ == '__main__':
    unittest.main()
