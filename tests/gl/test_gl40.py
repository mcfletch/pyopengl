#! /usr/bin/env python3
"""GL 4.0 (core): transform-feedback objects, double uniforms, subroutines,
indirect draw, tessellation patch params, per-buffer blend, indexed queries."""

import unittest
import ctypes
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403

VS = '#version 400 core\nin vec4 position; void main(){ gl_Position = position; }'
FS = '''#version 400 core
uniform double ud; uniform dvec2 ud2; uniform dvec3 ud3; uniform dvec4 ud4;
uniform dmat2 dm2; uniform dmat3 dm3; uniform dmat4 dm4;
uniform dmat2x3 dm23; uniform dmat3x2 dm32; uniform dmat2x4 dm24;
uniform dmat4x2 dm42; uniform dmat3x4 dm34; uniform dmat4x3 dm43;
subroutine vec4 colorFn();
subroutine uniform colorFn chooser;
subroutine(colorFn) vec4 red() { return vec4(1.0, 0.0, 0.0, 1.0); }
subroutine(colorFn) vec4 green() { return vec4(0.0, 1.0, 0.0, 1.0); }
out vec4 fragColor;
void main() {
    double s = ud + ud2.x + ud3.y + ud4.z + dm2[0][0] + dm3[1][1] + dm4[2][2]
        + dm23[0][0] + dm32[0][0] + dm24[0][0] + dm42[0][0] + dm34[0][0] + dm43[0][0];
    fragColor = chooser() * float(s);
}'''


def _char_pp(strings):
    arr = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
    return ctypes.cast(arr, ctypes.POINTER(ctypes.POINTER(ctypes.c_char)))


class TestGL40(GLTestCase):
    profile = 'core'
    gl_version = (4, 5)

    def test_double_uniforms(self):
        program = self.compile_program(VS, FS)
        glUseProgram(program)
        def loc(n):
            return glGetUniformLocation(program, n)
        glUniform1d(loc('ud'), 1.0)
        glUniform2d(loc('ud2'), 1, 2)
        glUniform3d(loc('ud3'), 1, 2, 3)
        glUniform4d(loc('ud4'), 1, 2, 3, 4)
        glUniform1dv(loc('ud'), 1, np.array([1], 'd'))
        glUniform2dv(loc('ud2'), 1, np.array([1, 2], 'd'))
        glUniform3dv(loc('ud3'), 1, np.array([1, 2, 3], 'd'))
        glUniform4dv(loc('ud4'), 1, np.array([1, 2, 3, 4], 'd'))
        glUniformMatrix2dv(loc('dm2'), 1, False, np.eye(2, dtype='d'))
        glUniformMatrix3dv(loc('dm3'), 1, False, np.eye(3, dtype='d'))
        glUniformMatrix4dv(loc('dm4'), 1, False, np.eye(4, dtype='d'))
        glGetUniformdv(program, loc('ud'), np.zeros(1, 'd'))
        glUniformMatrix2x3dv(loc('dm23'), 1, False, np.zeros((2, 3), 'd'))
        glUniformMatrix3x2dv(loc('dm32'), 1, False, np.zeros((3, 2), 'd'))
        glUniformMatrix2x4dv(loc('dm24'), 1, False, np.zeros((2, 4), 'd'))
        glUniformMatrix4x2dv(loc('dm42'), 1, False, np.zeros((4, 2), 'd'))
        glUniformMatrix3x4dv(loc('dm34'), 1, False, np.zeros((3, 4), 'd'))
        glUniformMatrix4x3dv(loc('dm43'), 1, False, np.zeros((4, 3), 'd'))
        self.check_error('double uniforms')

    def test_subroutines(self):
        program = self.compile_program(VS, FS)
        glUseProgram(program)
        idx = glGetSubroutineIndex(program, GL_FRAGMENT_SHADER, 'red')
        self.assertNotEqual(idx, GL_INVALID_INDEX)
        suloc = glGetSubroutineUniformLocation(program, GL_FRAGMENT_SHADER, 'chooser')
        glGetActiveSubroutineName(program, GL_FRAGMENT_SHADER, idx, 64)
        glGetActiveSubroutineUniformName(program, GL_FRAGMENT_SHADER, 0, 64)
        glGetActiveSubroutineUniformiv(
            program,
            GL_FRAGMENT_SHADER,
            0,
            GL_NUM_COMPATIBLE_SUBROUTINES,
            np.zeros(1, 'i'),
        )
        glGetProgramStageiv(
            program, GL_FRAGMENT_SHADER, GL_ACTIVE_SUBROUTINES, np.zeros(1, 'i')
        )
        glUniformSubroutinesuiv(GL_FRAGMENT_SHADER, 1, np.array([idx], 'I'))
        glGetUniformSubroutineuiv(GL_FRAGMENT_SHADER, suloc, np.zeros(1, 'I'))
        self.check_error('subroutines')

    def test_transform_feedback_objects(self):
        from OpenGL.GL import shaders

        fb_vs = '#version 400 core\nin vec4 position; out vec4 vout;\nvoid main(){ vout = position; gl_Position = position; }'
        prog = glCreateProgram()
        glAttachShader(prog, shaders.compileShader(fb_vs, GL_VERTEX_SHADER))
        glAttachShader(
            prog,
            shaders.compileShader(
                '#version 400 core\nout vec4 c; void main(){ c = vec4(1.0); }',
                GL_FRAGMENT_SHADER,
            ),
        )
        glTransformFeedbackVaryings(prog, 1, _char_pp(['vout']), GL_INTERLEAVED_ATTRIBS)
        glLinkProgram(prog)
        glUseProgram(prog)
        tfo = glGenTransformFeedbacks(1)
        tfo = int(tfo[0]) if hasattr(tfo, '__len__') else int(tfo)
        glBindTransformFeedback(GL_TRANSFORM_FEEDBACK, tfo)
        self.assertTrue(glIsTransformFeedback(tfo))
        buf = glGenBuffers(1)
        glBindBuffer(GL_TRANSFORM_FEEDBACK_BUFFER, buf)
        glBufferData(GL_TRANSFORM_FEEDBACK_BUFFER, 256, None, GL_DYNAMIC_COPY)
        glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER, 0, buf)
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER, np.array([(-1, -1), (1, -1), (0, 1)], 'f'), GL_STATIC_DRAW
        )
        ploc = glGetAttribLocation(prog, 'position')
        glEnableVertexAttribArray(ploc)
        glVertexAttribPointer(ploc, 2, GL_FLOAT, False, 0, None)
        glEnable(GL_RASTERIZER_DISCARD)
        glBeginTransformFeedback(GL_TRIANGLES)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        glPauseTransformFeedback()
        glResumeTransformFeedback()
        glEndTransformFeedback()
        glDisable(GL_RASTERIZER_DISCARD)
        glDrawTransformFeedback(GL_TRIANGLES, tfo)
        glDrawTransformFeedbackStream(GL_TRIANGLES, tfo, 0)
        glBindTransformFeedback(GL_TRANSFORM_FEEDBACK, 0)
        glDeleteTransformFeedbacks(1, [tfo])
        self.check_error('transform feedback objects')

    def test_indirect_blend_patch_query(self):
        program = self.compile_program(VS, FS)
        glUseProgram(program)
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(
            GL_ARRAY_BUFFER, np.array([(-1, -1), (1, -1), (0, 1)], 'f'), GL_STATIC_DRAW
        )
        loc = glGetAttribLocation(program, 'position')
        glEnableVertexAttribArray(loc)
        glVertexAttribPointer(loc, 2, GL_FLOAT, False, 0, None)
        ind = glGenBuffers(1)
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, ind)
        glBufferData(
            GL_DRAW_INDIRECT_BUFFER, np.array([3, 1, 0, 0], 'I'), GL_STATIC_DRAW
        )
        glDrawArraysIndirect(GL_TRIANGLES, ctypes.c_void_p(0))
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW)
        glBindBuffer(GL_DRAW_INDIRECT_BUFFER, ind)
        glBufferData(
            GL_DRAW_INDIRECT_BUFFER, np.array([3, 1, 0, 0, 0], 'I'), GL_STATIC_DRAW
        )
        # Intel's Windows driver serves this only when no glDrawArraysIndirect
        # has run against the same vertex array: on its own, with exactly these
        # bindings, the call succeeds. Exercise the entry point regardless.
        with self.tolerate_glerror(GL_INVALID_OPERATION):
            glDrawElementsIndirect(GL_TRIANGLES, GL_UNSIGNED_INT, ctypes.c_void_p(0))

        glEnablei(GL_BLEND, 0)
        glBlendEquationi(0, GL_FUNC_ADD)
        glBlendEquationSeparatei(0, GL_FUNC_ADD, GL_FUNC_SUBTRACT)
        glBlendFunci(0, GL_ONE, GL_ZERO)
        glBlendFuncSeparatei(0, GL_ONE, GL_ZERO, GL_ONE, GL_ZERO)
        glDisablei(GL_BLEND, 0)
        glMinSampleShading(1.0)
        glPatchParameteri(GL_PATCH_VERTICES, 3)
        glPatchParameterfv(GL_PATCH_DEFAULT_OUTER_LEVEL, np.array([1, 1, 1, 1], 'f'))

        q = glGenQueries(1)
        q = int(q[0]) if hasattr(q, '__len__') else int(q)
        glBeginQueryIndexed(GL_PRIMITIVES_GENERATED, 0, q)
        glEndQueryIndexed(GL_PRIMITIVES_GENERATED, 0)
        glGetQueryIndexediv(
            GL_PRIMITIVES_GENERATED, 0, GL_CURRENT_QUERY, np.zeros(1, 'i')
        )
        glDeleteQueries(1, [q])
        self.check_error('indirect/blend/patch/query')


if __name__ == '__main__':
    unittest.main()
