#! /usr/bin/env python3
"""GLES3.1: separable program objects, pipelines and the glProgramUniform* family."""

import unittest
import ctypes
from arraycompat import np, object_names, one

from egltestcase import ESTestCase

from OpenGL.GLES3 import (
    GL_VERTEX_SHADER,
    GL_FRAGMENT_SHADER,
    GL_VERTEX_SHADER_BIT,
    GL_FRAGMENT_SHADER_BIT,
    GL_LINK_STATUS,
    GL_TRUE,
    GL_ACTIVE_PROGRAM,
    glGetProgramiv,
    glGetUniformLocation,
    glCreateShaderProgramv,
    glGenProgramPipelines,
    glBindProgramPipeline,
    glUseProgramStages,
    glActiveShaderProgram,
    glValidateProgramPipeline,
    glGetProgramPipelineiv,
    glGetProgramPipelineInfoLog,
    glIsProgramPipeline,
    glDeleteProgramPipelines,
    glProgramUniform1f,
    glProgramUniform2f,
    glProgramUniform3f,
    glProgramUniform4f,
    glProgramUniform1i,
    glProgramUniform2i,
    glProgramUniform3i,
    glProgramUniform4i,
    glProgramUniform1ui,
    glProgramUniform2ui,
    glProgramUniform3ui,
    glProgramUniform4ui,
    glProgramUniform1fv,
    glProgramUniform2fv,
    glProgramUniform3fv,
    glProgramUniform4fv,
    glProgramUniform1iv,
    glProgramUniform2iv,
    glProgramUniform3iv,
    glProgramUniform4iv,
    glProgramUniform1uiv,
    glProgramUniform2uiv,
    glProgramUniform3uiv,
    glProgramUniform4uiv,
    glProgramUniformMatrix2fv,
    glProgramUniformMatrix3fv,
    glProgramUniformMatrix4fv,
    glProgramUniformMatrix2x3fv,
    glProgramUniformMatrix3x2fv,
    glProgramUniformMatrix2x4fv,
    glProgramUniformMatrix4x2fv,
    glProgramUniformMatrix3x4fv,
    glProgramUniformMatrix4x3fv,
)

VERTEX = '''#version 310 es
void main() { gl_Position = vec4( 0.0, 0.0, 0.0, 1.0 ); gl_PointSize = 1.0; }'''

FRAGMENT = '''#version 310 es
precision mediump float;
precision highp int;
uniform float uf; uniform vec2 uv2; uniform vec3 uv3; uniform vec4 uv4;
uniform int ui; uniform ivec2 ui2; uniform ivec3 ui3; uniform ivec4 ui4;
uniform uint uu; uniform uvec2 uu2; uniform uvec3 uu3; uniform uvec4 uu4;
uniform mat2 m2; uniform mat3 m3; uniform mat4 m4;
uniform mat2x3 m23; uniform mat3x2 m32; uniform mat2x4 m24;
uniform mat4x2 m42; uniform mat3x4 m34; uniform mat4x3 m43;
out vec4 c;
void main() {
    c = vec4(uf + uv2.x + uv3.y + uv4.z)
      + vec4(float(ui + ui2.x + ui3.y + ui4.z))
      + vec4(float(uu + uu2.x + uu3.y + uu4.z))
      + vec4(m2[0][0] + m3[0][0] + m4[0][0] + m23[0][0] + m32[0][0]
             + m24[0][0] + m42[0][0] + m34[0][0] + m43[0][0]);
}'''


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestES31ProgramPipeline(ESTestCase):
    api = 'gles'
    gl_version = (3, 1)

    def test_pipeline(self):
        vprog = glCreateShaderProgramv(GL_VERTEX_SHADER, 1, _char_pp([VERTEX]))
        fprog = glCreateShaderProgramv(GL_FRAGMENT_SHADER, 1, _char_pp([FRAGMENT]))
        self.assertEqual(glGetProgramiv(vprog, GL_LINK_STATUS), GL_TRUE)
        self.assertEqual(glGetProgramiv(fprog, GL_LINK_STATUS), GL_TRUE)

        pipeline = one(glGenProgramPipelines(1))
        glBindProgramPipeline(pipeline)
        glUseProgramStages(pipeline, GL_VERTEX_SHADER_BIT, vprog)
        glUseProgramStages(pipeline, GL_FRAGMENT_SHADER_BIT, fprog)
        glActiveShaderProgram(pipeline, fprog)
        glValidateProgramPipeline(pipeline)
        self.assertTrue(glIsProgramPipeline(pipeline))

        active = np.zeros(1, 'i')
        glGetProgramPipelineiv(pipeline, GL_ACTIVE_PROGRAM, active)
        glGetProgramPipelineInfoLog(pipeline, 256)
        self.check_error('pipeline')

        self._set_uniforms(fprog)
        glBindProgramPipeline(0)
        glDeleteProgramPipelines(1, object_names(pipeline))

    def _set_uniforms(self, p):
        def loc(n):
            return glGetUniformLocation(p, n)
        glProgramUniform1f(p, loc('uf'), 1.0)
        glProgramUniform2f(p, loc('uv2'), 1.0, 2.0)
        glProgramUniform3f(p, loc('uv3'), 1.0, 2.0, 3.0)
        glProgramUniform4f(p, loc('uv4'), 1.0, 2.0, 3.0, 4.0)
        glProgramUniform1i(p, loc('ui'), 1)
        glProgramUniform2i(p, loc('ui2'), 1, 2)
        glProgramUniform3i(p, loc('ui3'), 1, 2, 3)
        glProgramUniform4i(p, loc('ui4'), 1, 2, 3, 4)
        glProgramUniform1ui(p, loc('uu'), 1)
        glProgramUniform2ui(p, loc('uu2'), 1, 2)
        glProgramUniform3ui(p, loc('uu3'), 1, 2, 3)
        glProgramUniform4ui(p, loc('uu4'), 1, 2, 3, 4)

        glProgramUniform1fv(p, loc('uf'), 1, np.array([1], 'f'))
        glProgramUniform2fv(p, loc('uv2'), 1, np.array([1, 2], 'f'))
        glProgramUniform3fv(p, loc('uv3'), 1, np.array([1, 2, 3], 'f'))
        glProgramUniform4fv(p, loc('uv4'), 1, np.array([1, 2, 3, 4], 'f'))
        glProgramUniform1iv(p, loc('ui'), 1, np.array([1], 'i'))
        glProgramUniform2iv(p, loc('ui2'), 1, np.array([1, 2], 'i'))
        glProgramUniform3iv(p, loc('ui3'), 1, np.array([1, 2, 3], 'i'))
        glProgramUniform4iv(p, loc('ui4'), 1, np.array([1, 2, 3, 4], 'i'))
        glProgramUniform1uiv(p, loc('uu'), 1, np.array([1], 'u4'))
        glProgramUniform2uiv(p, loc('uu2'), 1, np.array([1, 2], 'u4'))
        glProgramUniform3uiv(p, loc('uu3'), 1, np.array([1, 2, 3], 'u4'))
        glProgramUniform4uiv(p, loc('uu4'), 1, np.array([1, 2, 3, 4], 'u4'))

        glProgramUniformMatrix2fv(p, loc('m2'), 1, False, np.eye(2, dtype='f'))
        glProgramUniformMatrix3fv(p, loc('m3'), 1, False, np.eye(3, dtype='f'))
        glProgramUniformMatrix4fv(p, loc('m4'), 1, False, np.eye(4, dtype='f'))
        glProgramUniformMatrix2x3fv(p, loc('m23'), 1, False, np.zeros((2, 3), 'f'))
        glProgramUniformMatrix3x2fv(p, loc('m32'), 1, False, np.zeros((3, 2), 'f'))
        glProgramUniformMatrix2x4fv(p, loc('m24'), 1, False, np.zeros((2, 4), 'f'))
        glProgramUniformMatrix4x2fv(p, loc('m42'), 1, False, np.zeros((4, 2), 'f'))
        glProgramUniformMatrix3x4fv(p, loc('m34'), 1, False, np.zeros((3, 4), 'f'))
        glProgramUniformMatrix4x3fv(p, loc('m43'), 1, False, np.zeros((4, 3), 'f'))
        self.check_error('program uniforms')


if __name__ == '__main__':
    unittest.main()
