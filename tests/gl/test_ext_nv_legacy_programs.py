#! /usr/bin/env python3
"""Legacy NVIDIA assembly-program extensions: NV_vertex_program (VP1.0 assembly,
generic vertex attributes, matrix tracking) and NV_fragment_program (named
fragment-program parameters).

Functional tests -- real program objects, real assembly, real calls with a clean
error state.
"""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.NV.vertex_program import *  # noqa: F401,F403

VP = b'''!!VP1.0
MOV o[HPOS], v[OPOS];
END'''
VSP = b'''!!VSP1.0
MOV c[0], c[0];
END'''
FP = b'''!!FP1.0
DECLARE color;
MOV o[COLR], color;
END'''


class TestNVVertexProgram(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def test_nv_vertex_program(self):
        self.require_extension('GL_NV_vertex_program')
        progs = np.zeros(2, 'u4')
        glGenProgramsNV(2, progs)
        vp = int(progs[0])
        glBindProgramNV(GL_VERTEX_PROGRAM_NV, vp)
        glLoadProgramNV(GL_VERTEX_PROGRAM_NV, vp, len(VP), VP)
        self.assertTrue(glIsProgramNV(vp))

        # program parameters (env registers c[])
        glProgramParameter4fNV(GL_VERTEX_PROGRAM_NV, 0, 1, 2, 3, 4)
        glProgramParameter4dNV(GL_VERTEX_PROGRAM_NV, 1, 1, 2, 3, 4)
        glProgramParameter4fvNV(GL_VERTEX_PROGRAM_NV, 0, np.array([1, 2, 3, 4], 'f'))
        glProgramParameter4dvNV(GL_VERTEX_PROGRAM_NV, 1, np.array([1, 2, 3, 4], 'd'))
        glProgramParameters4fvNV(GL_VERTEX_PROGRAM_NV, 0, 2, np.zeros(8, 'f'))
        glProgramParameters4dvNV(GL_VERTEX_PROGRAM_NV, 0, 2, np.zeros(8, 'd'))

        # matrix tracking
        glTrackMatrixNV(GL_VERTEX_PROGRAM_NV, 4, GL_MODELVIEW, GL_IDENTITY_NV)
        glGetTrackMatrixivNV(GL_VERTEX_PROGRAM_NV, 4, GL_TRACK_MATRIX_NV, np.zeros(1, 'i'))

        # generic vertex attributes -- scalar setters
        glVertexAttrib1fNV(8, 1.0)
        glVertexAttrib1dNV(8, 1.0)
        glVertexAttrib1sNV(8, 1)
        glVertexAttrib2fNV(8, 1, 2)
        glVertexAttrib2dNV(8, 1, 2)
        glVertexAttrib2sNV(8, 1, 2)
        glVertexAttrib3fNV(8, 1, 2, 3)
        glVertexAttrib3dNV(8, 1, 2, 3)
        glVertexAttrib3sNV(8, 1, 2, 3)
        glVertexAttrib4fNV(8, 1, 2, 3, 4)
        glVertexAttrib4dNV(8, 1, 2, 3, 4)
        glVertexAttrib4sNV(8, 1, 2, 3, 4)
        glVertexAttrib4ubNV(8, 1, 2, 3, 4)
        # vector setters
        glVertexAttrib1fvNV(8, np.array([1], 'f'))
        glVertexAttrib1dvNV(8, np.array([1], 'd'))
        glVertexAttrib1svNV(8, np.array([1], 'i2'))
        glVertexAttrib2fvNV(8, np.array([1, 2], 'f'))
        glVertexAttrib2dvNV(8, np.array([1, 2], 'd'))
        glVertexAttrib2svNV(8, np.array([1, 2], 'i2'))
        glVertexAttrib3fvNV(8, np.array([1, 2, 3], 'f'))
        glVertexAttrib3dvNV(8, np.array([1, 2, 3], 'd'))
        glVertexAttrib3svNV(8, np.array([1, 2, 3], 'i2'))
        glVertexAttrib4fvNV(8, np.array([1, 2, 3, 4], 'f'))
        glVertexAttrib4dvNV(8, np.array([1, 2, 3, 4], 'd'))
        glVertexAttrib4svNV(8, np.array([1, 2, 3, 4], 'i2'))
        glVertexAttrib4ubvNV(8, np.array([1, 2, 3, 4], 'u1'))
        # array setters
        glVertexAttribs1fvNV(8, 1, np.array([1], 'f'))
        glVertexAttribs1dvNV(8, 1, np.array([1], 'd'))
        glVertexAttribs1svNV(8, 1, np.array([1], 'i2'))
        glVertexAttribs2fvNV(8, 1, np.array([1, 2], 'f'))
        glVertexAttribs2dvNV(8, 1, np.array([1, 2], 'd'))
        glVertexAttribs2svNV(8, 1, np.array([1, 2], 'i2'))
        glVertexAttribs3fvNV(8, 1, np.array([1, 2, 3], 'f'))
        glVertexAttribs3dvNV(8, 1, np.array([1, 2, 3], 'd'))
        glVertexAttribs3svNV(8, 1, np.array([1, 2, 3], 'i2'))
        glVertexAttribs4fvNV(8, 1, np.array([1, 2, 3, 4], 'f'))
        glVertexAttribs4dvNV(8, 1, np.array([1, 2, 3, 4], 'd'))
        glVertexAttribs4svNV(8, 1, np.array([1, 2, 3, 4], 'i2'))
        glVertexAttribs4ubvNV(8, 1, np.array([1, 2, 3, 4], 'u1'))

        # attribute array + queries
        glVertexAttribPointerNV(8, 4, GL_FLOAT, 0, np.zeros(16, 'f'))
        glGetVertexAttribfvNV(8, GL_CURRENT_ATTRIB_NV, np.zeros(4, 'f'))
        glGetVertexAttribdvNV(8, GL_CURRENT_ATTRIB_NV, np.zeros(4, 'd'))
        glGetVertexAttribivNV(8, GL_ATTRIB_ARRAY_SIZE_NV, np.zeros(1, 'i'))
        glGetVertexAttribPointervNV(8, GL_ATTRIB_ARRAY_POINTER_NV, np.zeros(1, 'u8'))

        # program object queries / residency
        glGetProgramivNV(vp, GL_PROGRAM_LENGTH_NV, np.zeros(1, 'i'))
        glGetProgramStringNV(vp, GL_PROGRAM_STRING_NV, np.zeros(len(VP), 'u1'))
        glGetProgramParameterfvNV(GL_VERTEX_PROGRAM_NV, 0, GL_PROGRAM_PARAMETER_NV, np.zeros(4, 'f'))
        glGetProgramParameterdvNV(GL_VERTEX_PROGRAM_NV, 0, GL_PROGRAM_PARAMETER_NV, np.zeros(4, 'd'))
        glRequestResidentProgramsNV(1, np.array([vp], 'u4'))
        glAreProgramsResidentNV(1, np.array([vp], 'u4'), np.zeros(1, 'u1'))

        # a vertex-state program, executed to update program parameters
        sp = int(progs[1])
        glLoadProgramNV(GL_VERTEX_STATE_PROGRAM_NV, sp, len(VSP), VSP)
        glExecuteProgramNV(GL_VERTEX_STATE_PROGRAM_NV, sp, np.zeros(4, 'f'))

        glDeleteProgramsNV(2, progs)
        self.check_error('nv vertex program')

    def test_nv_fragment_program(self):
        self.require_extension('GL_NV_fragment_program')
        from OpenGL.GL.NV.vertex_program import glGenProgramsNV, glBindProgramNV, glLoadProgramNV, glDeleteProgramsNV
        from OpenGL.GL.NV.fragment_program import (
            glProgramNamedParameter4fNV, glProgramNamedParameter4dNV,
            glProgramNamedParameter4fvNV, glProgramNamedParameter4dvNV,
            glGetProgramNamedParameterfvNV, glGetProgramNamedParameterdvNV,
            GL_FRAGMENT_PROGRAM_NV,
        )

        progs = np.zeros(1, 'u4')
        glGenProgramsNV(1, progs)
        fp = int(progs[0])
        glBindProgramNV(GL_FRAGMENT_PROGRAM_NV, fp)
        glLoadProgramNV(GL_FRAGMENT_PROGRAM_NV, fp, len(FP), FP)

        name = np.array(list(b'color'), 'u1')
        n = len(name)
        glProgramNamedParameter4fNV(fp, n, name, 1, 1, 1, 1)
        glProgramNamedParameter4dNV(fp, n, name, 1, 1, 1, 1)
        glProgramNamedParameter4fvNV(fp, n, name, np.array([1, 1, 1, 1], 'f'))
        glProgramNamedParameter4dvNV(fp, n, name, np.array([1, 1, 1, 1], 'd'))
        glGetProgramNamedParameterfvNV(fp, n, name, np.zeros(4, 'f'))
        glGetProgramNamedParameterdvNV(fp, n, name, np.zeros(4, 'd'))

        glDeleteProgramsNV(1, progs)
        self.check_error('nv fragment program')


if __name__ == '__main__':
    unittest.main()
