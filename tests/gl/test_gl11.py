#! /usr/bin/env python3
"""GL 1.1 (compatibility): client vertex arrays, texture objects, polygon offset."""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *


class TestGL11(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_texture_objects(self):
        tex = glGenTextures(2)
        glBindTexture(GL_TEXTURE_2D, int(tex[0]))
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            4,
            4,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            np.zeros((4, 4, 4), 'B'),
        )
        glTexSubImage2D(
            GL_TEXTURE_2D,
            0,
            0,
            0,
            2,
            2,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            np.zeros((2, 2, 4), 'B'),
        )
        glBindTexture(GL_TEXTURE_1D, int(tex[1]))
        glTexImage1D(
            GL_TEXTURE_1D,
            0,
            GL_RGBA,
            4,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            np.zeros((4, 4), 'B'),
        )
        glTexSubImage1D(
            GL_TEXTURE_1D, 0, 0, 2, GL_RGBA, GL_UNSIGNED_BYTE, np.zeros((2, 4), 'B')
        )
        glBindTexture(GL_TEXTURE_2D, int(tex[0]))
        glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 0, 0, 4, 4, 0)
        glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, 2, 2)
        glBindTexture(GL_TEXTURE_1D, int(tex[1]))
        glCopyTexImage1D(GL_TEXTURE_1D, 0, GL_RGBA, 0, 0, 4, 0)
        glCopyTexSubImage1D(GL_TEXTURE_1D, 0, 0, 0, 0, 2)
        self.assertTrue(glIsTexture(int(tex[0])))
        glAreTexturesResident(2, tex, np.zeros(2, 'B'))
        glPrioritizeTextures(2, tex, np.array([1.0, 1.0], 'f'))
        glPolygonOffset(1.0, 1.0)
        glDeleteTextures(tex)
        self.check_error('texture objects')

    def test_client_arrays(self):
        verts = np.array([(-1, -1), (1, -1), (0, 1)], 'f')
        colors = np.array([(1, 0, 0, 1)] * 3, 'f')
        normals = np.array([(0, 0, 1)] * 3, 'f')
        texc = np.array([(0, 0), (1, 0), (0.5, 1)], 'f')
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_EDGE_FLAG_ARRAY)
        glEnableClientState(GL_INDEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, verts)
        glColorPointer(4, GL_FLOAT, 0, colors)
        glNormalPointer(GL_FLOAT, 0, normals)
        glTexCoordPointer(2, GL_FLOAT, 0, texc)
        glEdgeFlagPointer(0, np.array([1, 1, 1], 'B'))
        glIndexPointer(GL_INT, 0, np.array([0, 0, 0], 'i'))
        glArrayElement(0)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        glDrawElements(GL_TRIANGLES, 3, GL_UNSIGNED_INT, np.array([0, 1, 2], 'I'))
        glGetPointerv(GL_VERTEX_ARRAY_POINTER)
        for state in (
            GL_VERTEX_ARRAY,
            GL_COLOR_ARRAY,
            GL_NORMAL_ARRAY,
            GL_TEXTURE_COORD_ARRAY,
            GL_EDGE_FLAG_ARRAY,
            GL_INDEX_ARRAY,
        ):
            glDisableClientState(state)
        glInterleavedArrays(GL_V2F, 0, verts)
        glDisableClientState(GL_VERTEX_ARRAY)
        self.check_error('client arrays')

    def test_index_ub(self):
        glBegin(GL_POINTS)
        glIndexub(0)
        glIndexubv(np.array([0], 'B'))
        glEnd()
        self.check_error('index ub')


if __name__ == '__main__':
    unittest.main()
