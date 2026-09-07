#! /usr/bin/env python3
"""GL 4.1 (core): separable program pipelines + glProgramUniform*, viewport/
scissor/depth-range arrays, double vertex attribs, program binary, ES compat."""

import unittest
import ctypes
from arraycompat import np, object_names, one

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403

FRAGMENT = '''#version 410 core
uniform float uf; uniform vec2 uv2; uniform vec3 uv3; uniform vec4 uv4;
uniform int ui; uniform ivec2 ui2; uniform ivec3 ui3; uniform ivec4 ui4;
uniform uint uu; uniform uvec2 uu2; uniform uvec3 uu3; uniform uvec4 uu4;
uniform double ud; uniform dvec2 ud2v; uniform dvec3 ud3v; uniform dvec4 ud4v;
uniform mat2 m2; uniform mat3 m3; uniform mat4 m4;
uniform mat2x3 m23; uniform mat3x2 m32; uniform mat2x4 m24;
uniform mat4x2 m42; uniform mat3x4 m34; uniform mat4x3 m43;
uniform dmat2 dm2; uniform dmat3 dm3; uniform dmat4 dm4;
uniform dmat2x3 dm23; uniform dmat3x2 dm32; uniform dmat2x4 dm24;
uniform dmat4x2 dm42; uniform dmat3x4 dm34; uniform dmat4x3 dm43;
out vec4 fragColor;
void main() {
    float a = uf + uv2.x + uv3.y + uv4.z + float(ui+ui2.x+ui3.y+ui4.z)
        + float(uu+uu2.x+uu3.y+uu4.z) + float(ud+ud2v.x+ud3v.y+ud4v.z)
        + m2[0][0]+m3[0][0]+m4[0][0]+m23[0][0]+m32[0][0]+m24[0][0]+m42[0][0]+m34[0][0]+m43[0][0]
        + float(dm2[0][0]+dm3[0][0]+dm4[0][0]+dm23[0][0]+dm32[0][0]+dm24[0][0]+dm42[0][0]+dm34[0][0]+dm43[0][0]);
    fragColor = vec4(a);
}'''


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestGL41(GLTestCase):
    profile = 'core'
    gl_version = (4, 5)

    def test_pipeline_and_program_uniforms(self):
        p = glCreateShaderProgramv(GL_FRAGMENT_SHADER, 1, _char_pp([FRAGMENT]))
        self.assertEqual(
            glGetProgramiv(p, GL_LINK_STATUS), GL_TRUE, glGetProgramInfoLog(p)
        )
        pipe = one(glGenProgramPipelines(1))
        pipe = int(pipe[0]) if hasattr(pipe, '__len__') else int(pipe)
        glBindProgramPipeline(pipe)
        glUseProgramStages(pipe, GL_FRAGMENT_SHADER_BIT, p)
        glActiveShaderProgram(pipe, p)
        glValidateProgramPipeline(pipe)
        self.assertTrue(glIsProgramPipeline(pipe))
        glGetProgramPipelineiv(pipe, GL_ACTIVE_PROGRAM, np.zeros(1, 'i'))
        glGetProgramPipelineInfoLog(pipe, 256)
        glProgramParameteri(p, GL_PROGRAM_SEPARABLE, GL_TRUE)

        def loc(n):
            return glGetUniformLocation(p, n)
        glProgramUniform1f(p, loc('uf'), 1)
        glProgramUniform2f(p, loc('uv2'), 1, 2)
        glProgramUniform3f(p, loc('uv3'), 1, 2, 3)
        glProgramUniform4f(p, loc('uv4'), 1, 2, 3, 4)
        glProgramUniform1i(p, loc('ui'), 1)
        glProgramUniform2i(p, loc('ui2'), 1, 2)
        glProgramUniform3i(p, loc('ui3'), 1, 2, 3)
        glProgramUniform4i(p, loc('ui4'), 1, 2, 3, 4)
        glProgramUniform1ui(p, loc('uu'), 1)
        glProgramUniform2ui(p, loc('uu2'), 1, 2)
        glProgramUniform3ui(p, loc('uu3'), 1, 2, 3)
        glProgramUniform4ui(p, loc('uu4'), 1, 2, 3, 4)
        glProgramUniform1d(p, loc('ud'), 1.0)
        glProgramUniform2d(p, loc('ud2v'), 1, 2)
        glProgramUniform3d(p, loc('ud3v'), 1, 2, 3)
        glProgramUniform4d(p, loc('ud4v'), 1, 2, 3, 4)
        glProgramUniform2dv(p, loc('ud2v'), 1, np.array([1, 2], 'd'))
        glProgramUniform3dv(p, loc('ud3v'), 1, np.array([1, 2, 3], 'd'))
        glProgramUniform4dv(p, loc('ud4v'), 1, np.array([1, 2, 3, 4], 'd'))
        glProgramUniform1fv(p, loc('uf'), 1, np.array([1], 'f'))
        glProgramUniform2fv(p, loc('uv2'), 1, np.array([1, 2], 'f'))
        glProgramUniform3fv(p, loc('uv3'), 1, np.array([1, 2, 3], 'f'))
        glProgramUniform4fv(p, loc('uv4'), 1, np.array([1, 2, 3, 4], 'f'))
        glProgramUniform1iv(p, loc('ui'), 1, np.array([1], 'i'))
        glProgramUniform2iv(p, loc('ui2'), 1, np.array([1, 2], 'i'))
        glProgramUniform3iv(p, loc('ui3'), 1, np.array([1, 2, 3], 'i'))
        glProgramUniform4iv(p, loc('ui4'), 1, np.array([1, 2, 3, 4], 'i'))
        glProgramUniform1uiv(p, loc('uu'), 1, np.array([1], 'I'))
        glProgramUniform2uiv(p, loc('uu2'), 1, np.array([1, 2], 'I'))
        glProgramUniform3uiv(p, loc('uu3'), 1, np.array([1, 2, 3], 'I'))
        glProgramUniform4uiv(p, loc('uu4'), 1, np.array([1, 2, 3, 4], 'I'))
        glProgramUniform1dv(p, loc('ud'), 1, np.array([1], 'd'))
        glProgramUniformMatrix2fv(p, loc('m2'), 1, False, np.eye(2, dtype='f'))
        glProgramUniformMatrix3fv(p, loc('m3'), 1, False, np.eye(3, dtype='f'))
        glProgramUniformMatrix4fv(p, loc('m4'), 1, False, np.eye(4, dtype='f'))
        glProgramUniformMatrix2x3fv(p, loc('m23'), 1, False, np.zeros((2, 3), 'f'))
        glProgramUniformMatrix3x2fv(p, loc('m32'), 1, False, np.zeros((3, 2), 'f'))
        glProgramUniformMatrix2x4fv(p, loc('m24'), 1, False, np.zeros((2, 4), 'f'))
        glProgramUniformMatrix4x2fv(p, loc('m42'), 1, False, np.zeros((4, 2), 'f'))
        glProgramUniformMatrix3x4fv(p, loc('m34'), 1, False, np.zeros((3, 4), 'f'))
        glProgramUniformMatrix4x3fv(p, loc('m43'), 1, False, np.zeros((4, 3), 'f'))
        glProgramUniformMatrix2dv(p, loc('dm2'), 1, False, np.eye(2, dtype='d'))
        glProgramUniformMatrix3dv(p, loc('dm3'), 1, False, np.eye(3, dtype='d'))
        glProgramUniformMatrix4dv(p, loc('dm4'), 1, False, np.eye(4, dtype='d'))
        glProgramUniformMatrix2x3dv(p, loc('dm23'), 1, False, np.zeros((2, 3), 'd'))
        glProgramUniformMatrix3x2dv(p, loc('dm32'), 1, False, np.zeros((3, 2), 'd'))
        glProgramUniformMatrix2x4dv(p, loc('dm24'), 1, False, np.zeros((2, 4), 'd'))
        glProgramUniformMatrix4x2dv(p, loc('dm42'), 1, False, np.zeros((4, 2), 'd'))
        glProgramUniformMatrix3x4dv(p, loc('dm34'), 1, False, np.zeros((3, 4), 'd'))
        glProgramUniformMatrix4x3dv(p, loc('dm43'), 1, False, np.zeros((4, 3), 'd'))
        self.check_error('program uniforms')
        glBindProgramPipeline(0)
        glDeleteProgramPipelines(1, object_names(pipe))

    def test_viewport_scissor_depth_arrays(self):
        glViewportArrayv(0, 1, np.array([0, 0, 16, 16], 'f'))
        glViewportIndexedf(0, 0, 0, 16, 16)
        glViewportIndexedfv(0, np.array([0, 0, 16, 16], 'f'))
        glScissorArrayv(0, 1, np.array([0, 0, 16, 16], 'i'))
        glScissorIndexed(0, 0, 0, 16, 16)
        glScissorIndexedv(0, np.array([0, 0, 16, 16], 'i'))
        glDepthRangeArrayv(0, 1, np.array([0.0, 1.0], 'd'))
        glDepthRangeIndexed(0, 0.0, 1.0)
        glGetFloati_v(GL_VIEWPORT, 0, np.zeros(4, 'f'))
        glGetDoublei_v(GL_DEPTH_RANGE, 0, np.zeros(2, 'd'))
        self.check_error('viewport/scissor/depth arrays')

    def test_double_attribs_and_es_compat(self):
        glVertexAttribL1d(2, 1.0)
        glVertexAttribL2d(2, 1, 2)
        glVertexAttribL3d(2, 1, 2, 3)
        glVertexAttribL4d(2, 1, 2, 3, 4)
        glVertexAttribL1dv(2, np.zeros(1, 'd'))
        glVertexAttribL2dv(2, np.zeros(2, 'd'))
        glVertexAttribL3dv(2, np.zeros(3, 'd'))
        glVertexAttribL4dv(2, np.zeros(4, 'd'))
        buf = one(glGenBuffers(1))
        glBindBuffer(GL_ARRAY_BUFFER, buf)
        glBufferData(GL_ARRAY_BUFFER, np.zeros(8, 'd'), GL_STATIC_DRAW)
        glVertexAttribLPointer(2, 4, GL_DOUBLE, 0, None)
        glGetVertexAttribLdv(2, GL_CURRENT_VERTEX_ATTRIB, np.zeros(4, 'd'))
        glClearDepthf(1.0)
        glDepthRangef(0.0, 1.0)
        rng = np.zeros(2, 'i')
        prec = np.zeros(1, 'i')
        glGetShaderPrecisionFormat(GL_FRAGMENT_SHADER, GL_HIGH_FLOAT, rng, prec)
        glReleaseShaderCompiler()
        self.assertGreaterEqual(self.getInteger(GL_NUM_SHADER_BINARY_FORMATS), 0)
        with self.exercise(
            'no portable binary format/blob here, so the load is expected to '
            'fail; the call still drives the wrapper'
        ):
            sh = glCreateShader(GL_VERTEX_SHADER)
            glShaderBinary(
                1,
                np.array([sh], 'I'),
                GL_SHADER_BINARY_FORMAT_SPIR_V,
                np.zeros(4, 'B'),
                4,
            )
        self.check_error('double attribs / es compat')

    def test_program_binary(self):
        p = glCreateShaderProgramv(GL_FRAGMENT_SHADER, 1, _char_pp([FRAGMENT]))
        glProgramParameteri(p, GL_PROGRAM_BINARY_RETRIEVABLE_HINT, GL_TRUE)
        glLinkProgram(p)
        length = one(glGetProgramiv(p, GL_PROGRAM_BINARY_LENGTH))
        if length < 1:
            self.skipTest('no retrievable binary')
        out_len = (ctypes.c_int * 1)()
        fmt = (ctypes.c_uint * 1)()
        binary = (ctypes.c_ubyte * length)()
        glGetProgramBinary(p, length, out_len, fmt, binary)
        p2 = glCreateProgram()
        glProgramBinary(p2, fmt[0], binary, out_len[0])
        self.check_error('program binary')


if __name__ == '__main__':
    unittest.main()
