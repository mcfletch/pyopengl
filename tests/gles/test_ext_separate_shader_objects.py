#! /usr/bin/env python3
"""GL_EXT_separate_shader_objects: EXT separable programs and glProgramUniform*EXT."""

import unittest
import ctypes
from arraycompat import np, object_names

from egltestcase import ESTestCase

from OpenGL.GLES2 import GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_TRUE
from OpenGL.GLES3 import GL_FRAGMENT_SHADER_BIT
from OpenGL.GLES2.EXT.separate_shader_objects import (
    glCreateShaderProgramvEXT,
    glGenProgramPipelinesEXT,
    glBindProgramPipelineEXT,
    glUseProgramStagesEXT,
    glActiveShaderProgramEXT,
    glValidateProgramPipelineEXT,
    glGetProgramPipelineivEXT,
    glGetProgramPipelineInfoLogEXT,
    glIsProgramPipelineEXT,
    glDeleteProgramPipelinesEXT,
    glProgramParameteriEXT,
    glProgramUniform1fEXT,
    glProgramUniform2fEXT,
    glProgramUniform3fEXT,
    glProgramUniform4fEXT,
    glProgramUniform1iEXT,
    glProgramUniform2iEXT,
    glProgramUniform3iEXT,
    glProgramUniform4iEXT,
    glProgramUniform1uiEXT,
    glProgramUniform2uiEXT,
    glProgramUniform3uiEXT,
    glProgramUniform4uiEXT,
    glProgramUniform1fvEXT,
    glProgramUniform2fvEXT,
    glProgramUniform3fvEXT,
    glProgramUniform4fvEXT,
    glProgramUniform1ivEXT,
    glProgramUniform2ivEXT,
    glProgramUniform3ivEXT,
    glProgramUniform4ivEXT,
    glProgramUniform1uivEXT,
    glProgramUniform2uivEXT,
    glProgramUniform3uivEXT,
    glProgramUniform4uivEXT,
    glProgramUniformMatrix2fvEXT,
    glProgramUniformMatrix3fvEXT,
    glProgramUniformMatrix4fvEXT,
    glProgramUniformMatrix2x3fvEXT,
    glProgramUniformMatrix3x2fvEXT,
    glProgramUniformMatrix2x4fvEXT,
    glProgramUniformMatrix4x2fvEXT,
    glProgramUniformMatrix3x4fvEXT,
    glProgramUniformMatrix4x3fvEXT,
    GL_ACTIVE_PROGRAM_EXT,
    GL_PROGRAM_SEPARABLE_EXT,
)
from OpenGL.GLES3 import glGetUniformLocation

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
    c = vec4(uf + uv2.x + uv3.y + uv4.z) + vec4(float(ui + ui2.x + ui3.y + ui4.z))
      + vec4(float(uu + uu2.x + uu3.y + uu4.z))
      + vec4(m2[0][0]+m3[0][0]+m4[0][0]+m23[0][0]+m32[0][0]+m24[0][0]+m42[0][0]+m34[0][0]+m43[0][0]);
}'''


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestEXTSeparateShaderObjects(ESTestCase):
    api = 'gles'
    gl_version = (3, 1)

    def test_ext_pipeline(self):
        self.require_extension('GL_EXT_separate_shader_objects')
        with self.exercise():
            self._run()

    def _run(self):
        p = glCreateShaderProgramvEXT(GL_FRAGMENT_SHADER, 1, _char_pp([FRAGMENT]))

        pids = np.zeros(1, 'u4')
        glGenProgramPipelinesEXT(1, pids)
        pipeline = int(pids[0])
        glBindProgramPipelineEXT(pipeline)
        glUseProgramStagesEXT(pipeline, GL_FRAGMENT_SHADER_BIT, p)
        glActiveShaderProgramEXT(pipeline, p)
        glValidateProgramPipelineEXT(pipeline)
        self.assertTrue(glIsProgramPipelineEXT(pipeline))
        glProgramParameteriEXT(p, GL_PROGRAM_SEPARABLE_EXT, GL_TRUE)
        info = np.zeros(1, 'i')
        glGetProgramPipelineivEXT(pipeline, GL_ACTIVE_PROGRAM_EXT, info)
        length = (ctypes.c_int * 1)()
        log = (ctypes.c_char * 256)()
        glGetProgramPipelineInfoLogEXT(pipeline, 256, length, log)

        def loc(n):
            return glGetUniformLocation(p, n)
        glProgramUniform1fEXT(p, loc('uf'), 1.0)
        glProgramUniform2fEXT(p, loc('uv2'), 1.0, 2.0)
        glProgramUniform3fEXT(p, loc('uv3'), 1.0, 2.0, 3.0)
        glProgramUniform4fEXT(p, loc('uv4'), 1.0, 2.0, 3.0, 4.0)
        glProgramUniform1iEXT(p, loc('ui'), 1)
        glProgramUniform2iEXT(p, loc('ui2'), 1, 2)
        glProgramUniform3iEXT(p, loc('ui3'), 1, 2, 3)
        glProgramUniform4iEXT(p, loc('ui4'), 1, 2, 3, 4)
        glProgramUniform1uiEXT(p, loc('uu'), 1)
        glProgramUniform2uiEXT(p, loc('uu2'), 1, 2)
        glProgramUniform3uiEXT(p, loc('uu3'), 1, 2, 3)
        glProgramUniform4uiEXT(p, loc('uu4'), 1, 2, 3, 4)
        glProgramUniform1fvEXT(p, loc('uf'), 1, np.array([1], 'f'))
        glProgramUniform2fvEXT(p, loc('uv2'), 1, np.array([1, 2], 'f'))
        glProgramUniform3fvEXT(p, loc('uv3'), 1, np.array([1, 2, 3], 'f'))
        glProgramUniform4fvEXT(p, loc('uv4'), 1, np.array([1, 2, 3, 4], 'f'))
        glProgramUniform1ivEXT(p, loc('ui'), 1, np.array([1], 'i'))
        glProgramUniform2ivEXT(p, loc('ui2'), 1, np.array([1, 2], 'i'))
        glProgramUniform3ivEXT(p, loc('ui3'), 1, np.array([1, 2, 3], 'i'))
        glProgramUniform4ivEXT(p, loc('ui4'), 1, np.array([1, 2, 3, 4], 'i'))
        glProgramUniform1uivEXT(p, loc('uu'), 1, np.array([1], 'u4'))
        glProgramUniform2uivEXT(p, loc('uu2'), 1, np.array([1, 2], 'u4'))
        glProgramUniform3uivEXT(p, loc('uu3'), 1, np.array([1, 2, 3], 'u4'))
        glProgramUniform4uivEXT(p, loc('uu4'), 1, np.array([1, 2, 3, 4], 'u4'))
        glProgramUniformMatrix2fvEXT(p, loc('m2'), 1, False, np.eye(2, dtype='f'))
        glProgramUniformMatrix3fvEXT(p, loc('m3'), 1, False, np.eye(3, dtype='f'))
        glProgramUniformMatrix4fvEXT(p, loc('m4'), 1, False, np.eye(4, dtype='f'))
        glProgramUniformMatrix2x3fvEXT(p, loc('m23'), 1, False, np.zeros((2, 3), 'f'))
        glProgramUniformMatrix3x2fvEXT(p, loc('m32'), 1, False, np.zeros((3, 2), 'f'))
        glProgramUniformMatrix2x4fvEXT(p, loc('m24'), 1, False, np.zeros((2, 4), 'f'))
        glProgramUniformMatrix4x2fvEXT(p, loc('m42'), 1, False, np.zeros((4, 2), 'f'))
        glProgramUniformMatrix3x4fvEXT(p, loc('m34'), 1, False, np.zeros((3, 4), 'f'))
        glProgramUniformMatrix4x3fvEXT(p, loc('m43'), 1, False, np.zeros((4, 3), 'f'))
        self.check_error('ext program uniforms')

        glBindProgramPipelineEXT(0)
        glDeleteProgramPipelinesEXT(1, object_names(pipeline))


if __name__ == '__main__':
    unittest.main()
