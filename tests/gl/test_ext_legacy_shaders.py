#! /usr/bin/env python3
"""Pre-2.0 GLSL via GL_ARB_shader_objects + GL_ARB_vertex_shader (GLhandleARB
objects), exercised against a real compile/link in a compatibility context."""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.ARB.shader_objects import *  # noqa: F401,F403
from OpenGL.GL.ARB.vertex_shader import *  # noqa: F401,F403

VS = '''attribute vec4 pos;
void main(){ gl_Position = pos; }'''
FS = '''uniform float uf; uniform vec2 uv2; uniform vec3 uv3; uniform vec4 uv4;
uniform int ui; uniform ivec2 ui2; uniform ivec3 ui3; uniform ivec4 ui4;
uniform mat2 m2; uniform mat3 m3; uniform mat4 m4;
void main(){ gl_FragColor = vec4(uf+uv2.x+uv3.y+uv4.z) + vec4(float(ui+ui2.x+ui3.y+ui4.z))
    + vec4(m2[0][0]+m3[0][0]+m4[0][0]); }'''


class TestLegacyShaders(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def _compile(self, src, stage):
        sh = glCreateShaderObjectARB(stage)
        glShaderSourceARB(sh, [src])
        glCompileShaderARB(sh)
        status = glGetObjectParameterivARB(sh, GL_OBJECT_COMPILE_STATUS_ARB)
        self.assertTrue(status, glGetInfoLogARB(sh))
        return sh

    def test_shader_objects(self):
        self.require_extension('GL_ARB_shader_objects')
        self.require_extension('GL_ARB_vertex_shader')
        vs = self._compile(VS, GL_VERTEX_SHADER)
        fs = self._compile(FS, GL_FRAGMENT_SHADER)
        prog = glCreateProgramObjectARB()
        glAttachObjectARB(prog, vs)
        glAttachObjectARB(prog, fs)
        glBindAttribLocationARB(prog, 0, b'pos')
        glLinkProgramARB(prog)
        self.assertTrue(
            glGetObjectParameterivARB(prog, GL_OBJECT_LINK_STATUS_ARB),
            glGetInfoLogARB(prog),
        )
        glValidateProgramARB(prog)
        glUseProgramObjectARB(prog)
        glGetObjectParameterfvARB(prog, GL_OBJECT_LINK_STATUS_ARB, np.zeros(1, 'f'))

        self.assertEqual(glGetHandleARB(GL_PROGRAM_OBJECT_ARB), prog)
        self.assertIn(vs, list(glGetAttachedObjectsARB(prog)))
        glGetActiveUniformARB(prog, 0)
        glGetActiveAttribARB(prog, 0)
        self.assertIn(b'pos', glGetShaderSourceARB(vs))
        self.assertEqual(glGetAttribLocationARB(prog, b'pos'), 0)

        def loc(n):
            return glGetUniformLocationARB(prog, n)
        glUniform1fARB(loc('uf'), 1)
        glUniform1fvARB(loc('uf'), 1, np.ones(1, 'f'))
        glUniform2fARB(loc('uv2'), 1, 2)
        glUniform2fvARB(loc('uv2'), 1, np.ones(2, 'f'))
        glUniform3fARB(loc('uv3'), 1, 2, 3)
        glUniform3fvARB(loc('uv3'), 1, np.ones(3, 'f'))
        glUniform4fARB(loc('uv4'), 1, 2, 3, 4)
        glUniform4fvARB(loc('uv4'), 1, np.ones(4, 'f'))
        glUniform1iARB(loc('ui'), 1)
        glUniform1ivARB(loc('ui'), 1, np.ones(1, 'i'))
        glUniform2iARB(loc('ui2'), 1, 2)
        glUniform2ivARB(loc('ui2'), 1, np.ones(2, 'i'))
        glUniform3iARB(loc('ui3'), 1, 2, 3)
        glUniform3ivARB(loc('ui3'), 1, np.ones(3, 'i'))
        glUniform4iARB(loc('ui4'), 1, 2, 3, 4)
        glUniform4ivARB(loc('ui4'), 1, np.ones(4, 'i'))
        glUniformMatrix2fvARB(loc('m2'), 1, False, np.eye(2, dtype='f'))
        glUniformMatrix3fvARB(loc('m3'), 1, False, np.eye(3, dtype='f'))
        glUniformMatrix4fvARB(loc('m4'), 1, False, np.eye(4, dtype='f'))
        glGetUniformfvARB(prog, loc('uf'), np.zeros(1, 'f'))
        glGetUniformivARB(prog, loc('ui'), np.zeros(1, 'i'))

        # vertex-attrib ARB entry points
        glEnableVertexAttribArrayARB(0)
        glDisableVertexAttribArrayARB(0)
        glVertexAttrib1dARB(1, 1)
        glVertexAttrib1dvARB(1, np.zeros(1, 'd'))
        glVertexAttrib1fARB(1, 1)
        glVertexAttrib1fvARB(1, np.zeros(1, 'f'))
        glVertexAttrib1sARB(1, 1)
        glVertexAttrib1svARB(1, np.zeros(1, 'h'))
        glVertexAttrib2dARB(1, 1, 2)
        glVertexAttrib2dvARB(1, np.zeros(2, 'd'))
        glVertexAttrib2fARB(1, 1, 2)
        glVertexAttrib2fvARB(1, np.zeros(2, 'f'))
        glVertexAttrib2sARB(1, 1, 2)
        glVertexAttrib2svARB(1, np.zeros(2, 'h'))
        glVertexAttrib3dARB(1, 1, 2, 3)
        glVertexAttrib3dvARB(1, np.zeros(3, 'd'))
        glVertexAttrib3fARB(1, 1, 2, 3)
        glVertexAttrib3fvARB(1, np.zeros(3, 'f'))
        glVertexAttrib3sARB(1, 1, 2, 3)
        glVertexAttrib3svARB(1, np.zeros(3, 'h'))
        glVertexAttrib4dARB(1, 1, 2, 3, 4)
        glVertexAttrib4dvARB(1, np.zeros(4, 'd'))
        glVertexAttrib4fARB(1, 1, 2, 3, 4)
        glVertexAttrib4fvARB(1, np.zeros(4, 'f'))
        glVertexAttrib4sARB(1, 1, 2, 3, 4)
        glVertexAttrib4svARB(1, np.zeros(4, 'h'))
        glVertexAttrib4bvARB(1, np.zeros(4, 'b'))
        glVertexAttrib4ivARB(1, np.zeros(4, 'i'))
        glVertexAttrib4ubvARB(1, np.zeros(4, 'B'))
        glVertexAttrib4uivARB(1, np.zeros(4, 'I'))
        glVertexAttrib4usvARB(1, np.zeros(4, 'H'))
        glVertexAttrib4NbvARB(1, np.zeros(4, 'b'))
        glVertexAttrib4NivARB(1, np.zeros(4, 'i'))
        glVertexAttrib4NsvARB(1, np.zeros(4, 'h'))
        glVertexAttrib4NubARB(1, 0, 0, 0, 0)
        glVertexAttrib4NubvARB(1, np.zeros(4, 'B'))
        glVertexAttrib4NuivARB(1, np.zeros(4, 'I'))
        glVertexAttrib4NusvARB(1, np.zeros(4, 'H'))
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, np.zeros(16, 'f'), GL_STATIC_DRAW)
        glVertexAttribPointerARB(0, 4, GL_FLOAT, GL_FALSE, 0, None)
        glGetVertexAttribdvARB(1, GL_CURRENT_VERTEX_ATTRIB, np.zeros(4, 'd'))
        glGetVertexAttribfvARB(1, GL_CURRENT_VERTEX_ATTRIB, np.zeros(4, 'f'))
        glGetVertexAttribivARB(0, GL_VERTEX_ATTRIB_ARRAY_ENABLED, np.zeros(1, 'i'))
        import ctypes

        ptr = ctypes.c_void_p()
        glGetVertexAttribPointervARB(
            0, GL_VERTEX_ATTRIB_ARRAY_POINTER, ctypes.byref(ptr)
        )
        self.check_error('legacy shaders')

        glDetachObjectARB(prog, vs)
        glDeleteObjectARB(vs)
        glDeleteObjectARB(fs)
        glUseProgramObjectARB(0)
        glDeleteObjectARB(prog)


if __name__ == '__main__':
    unittest.main()
