#! /usr/bin/env python3
"""GL 1.0 (compatibility): evaluators, maps and grids."""

import unittest
from arraycompat import np, astype  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *

CTRL = np.array([[-1, -1, 0], [1, 1, 0]], 'f')
CTRL2 = np.array([[[-1, -1, 0], [1, -1, 0]], [[-1, 1, 0], [1, 1, 0]]], 'f')


class TestGL1Eval(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_map1(self):
        # PyOpenGL's friendly wrapper derives stride/order from the array
        glMap1f(GL_MAP1_VERTEX_3, 0.0, 1.0, CTRL)
        glMap1d(GL_MAP1_VERTEX_3, 0.0, 1.0, astype(CTRL, 'd'))
        glEnable(GL_MAP1_VERTEX_3)
        glMapGrid1f(4, 0.0, 1.0)
        glMapGrid1d(4, 0.0, 1.0)
        glBegin(GL_LINE_STRIP)
        glEvalCoord1f(0.5)
        glEvalCoord1d(0.5)
        glEvalCoord1fv(np.array([0.5], 'f'))
        glEvalCoord1dv(np.array([0.5], 'd'))
        glEnd()
        glEvalMesh1(GL_LINE, 0, 4)
        glEvalPoint1(2)
        glGetMapfv(GL_MAP1_VERTEX_3, GL_COEFF, np.zeros((2, 3), 'f'))
        glGetMapdv(GL_MAP1_VERTEX_3, GL_COEFF, np.zeros((2, 3), 'd'))
        glGetMapiv(GL_MAP1_VERTEX_3, GL_ORDER, np.zeros(1, 'i'))
        glDisable(GL_MAP1_VERTEX_3)
        self.check_error('map1')

    def test_map2(self):
        glMap2f(GL_MAP2_VERTEX_3, 0.0, 1.0, 0.0, 1.0, CTRL2)
        glMap2d(GL_MAP2_VERTEX_3, 0.0, 1.0, 0.0, 1.0, astype(CTRL2, 'd'))
        glEnable(GL_MAP2_VERTEX_3)
        glMapGrid2f(4, 0.0, 1.0, 4, 0.0, 1.0)
        glMapGrid2d(4, 0.0, 1.0, 4, 0.0, 1.0)
        glBegin(GL_POINTS)
        glEvalCoord2f(0.5, 0.5)
        glEvalCoord2d(0.5, 0.5)
        glEvalCoord2fv(np.array([0.5, 0.5], 'f'))
        glEvalCoord2dv(np.array([0.5, 0.5], 'd'))
        glEnd()
        glEvalMesh2(GL_FILL, 0, 4, 0, 4)
        glEvalPoint2(2, 2)
        glDisable(GL_MAP2_VERTEX_3)
        self.check_error('map2')


if __name__ == '__main__':
    unittest.main()
