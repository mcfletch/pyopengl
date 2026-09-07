#! /usr/bin/env python3
"""GL 3.3 (compatibility): sampler objects, instanced divisor, timestamp query,
dual-source fragment output, packed (P-type) vertex specification."""

import unittest
from arraycompat import np, object_names

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403

P = GL_UNSIGNED_INT_2_10_10_10_REV


class TestGL33(GLTestCase):
    profile = 'compatibility'
    gl_version = (3, 3)

    def test_samplers(self):
        s = glGenSamplers(1)
        s = int(s[0]) if hasattr(s, '__len__') else int(s)
        glBindSampler(0, s)
        glSamplerParameteri(s, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glSamplerParameterf(s, GL_TEXTURE_MAX_LOD, 1.0)
        glSamplerParameteriv(s, GL_TEXTURE_WRAP_S, np.array([GL_CLAMP_TO_EDGE], 'i'))
        glSamplerParameterfv(s, GL_TEXTURE_MIN_LOD, np.array([0.0], 'f'))
        glSamplerParameterIiv(s, GL_TEXTURE_BORDER_COLOR, np.array([0, 0, 0, 0], 'i'))
        glSamplerParameterIuiv(s, GL_TEXTURE_BORDER_COLOR, np.array([0, 0, 0, 0], 'I'))
        glGetSamplerParameteriv(s, GL_TEXTURE_MIN_FILTER, np.zeros(1, 'i'))
        glGetSamplerParameterfv(s, GL_TEXTURE_MAX_LOD, np.zeros(1, 'f'))
        glGetSamplerParameterIiv(s, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'i'))
        glGetSamplerParameterIuiv(s, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'I'))
        self.assertTrue(glIsSampler(s))
        glDeleteSamplers(1, object_names(s))
        self.check_error('samplers')

    def test_divisor_and_query(self):
        glVertexAttribDivisor(0, 1)
        q = glGenQueries(1)
        q = int(q[0]) if hasattr(q, '__len__') else int(q)
        glQueryCounter(q, GL_TIMESTAMP)
        glGetQueryObjecti64v(q, GL_QUERY_RESULT, np.zeros(1, 'q'))
        glGetQueryObjectui64v(q, GL_QUERY_RESULT, np.zeros(1, 'Q'))
        glDeleteQueries(1, object_names(q))
        self.check_error('divisor/query')

    def test_dual_source(self):
        vs = '#version 330 compatibility\nvoid main(){gl_Position=gl_Vertex;}'
        fs = (
            '#version 330 compatibility\n'
            'out vec4 c0; out vec4 c1;\n'
            'void main(){ c0 = vec4(1.0); c1 = vec4(0.5); }'
        )
        program = self.compile_program(vs, fs)
        glBindFragDataLocationIndexed(program, 0, 0, 'c0')
        glBindFragDataLocationIndexed(program, 0, 1, 'c1')
        glLinkProgram(program)
        glGetFragDataIndex(program, 'c0')
        self.check_error('dual source')

    def test_packed_vertex_attrib(self):
        glVertexAttribP1ui(1, P, GL_FALSE, 0)
        glVertexAttribP2ui(1, P, GL_FALSE, 0)
        glVertexAttribP3ui(1, P, GL_FALSE, 0)
        glVertexAttribP4ui(1, P, GL_FALSE, 0)
        glVertexAttribP1uiv(1, P, GL_FALSE, np.zeros(1, 'I'))
        glVertexAttribP2uiv(1, P, GL_FALSE, np.zeros(1, 'I'))
        glVertexAttribP3uiv(1, P, GL_FALSE, np.zeros(1, 'I'))
        glVertexAttribP4uiv(1, P, GL_FALSE, np.zeros(1, 'I'))
        self.check_error('packed vertex attrib')

    def test_packed_immediate(self):
        glBegin(GL_POINTS)
        glVertexP2ui(P, 0)
        glVertexP3ui(P, 0)
        glVertexP4ui(P, 0)
        glVertexP2uiv(P, np.zeros(1, 'I'))
        glVertexP3uiv(P, np.zeros(1, 'I'))
        glVertexP4uiv(P, np.zeros(1, 'I'))
        glColorP3ui(P, 0)
        glColorP4ui(P, 0)
        glColorP3uiv(P, np.zeros(1, 'I'))
        glColorP4uiv(P, np.zeros(1, 'I'))
        glTexCoordP1ui(P, 0)
        glTexCoordP2ui(P, 0)
        glTexCoordP3ui(P, 0)
        glTexCoordP4ui(P, 0)
        glTexCoordP1uiv(P, np.zeros(1, 'I'))
        glTexCoordP2uiv(P, np.zeros(1, 'I'))
        glTexCoordP3uiv(P, np.zeros(1, 'I'))
        glTexCoordP4uiv(P, np.zeros(1, 'I'))
        glMultiTexCoordP1ui(GL_TEXTURE0, P, 0)
        glMultiTexCoordP2ui(GL_TEXTURE0, P, 0)
        glMultiTexCoordP3ui(GL_TEXTURE0, P, 0)
        glMultiTexCoordP4ui(GL_TEXTURE0, P, 0)
        glMultiTexCoordP1uiv(GL_TEXTURE0, P, np.zeros(1, 'I'))
        glMultiTexCoordP2uiv(GL_TEXTURE0, P, np.zeros(1, 'I'))
        glMultiTexCoordP3uiv(GL_TEXTURE0, P, np.zeros(1, 'I'))
        glMultiTexCoordP4uiv(GL_TEXTURE0, P, np.zeros(1, 'I'))
        glNormalP3ui(P, 0)
        glNormalP3uiv(P, np.zeros(1, 'I'))
        glSecondaryColorP3ui(P, 0)
        glSecondaryColorP3uiv(P, np.zeros(1, 'I'))
        glEnd()
        self.check_error('packed immediate')


if __name__ == '__main__':
    unittest.main()
