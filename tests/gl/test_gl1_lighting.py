#! /usr/bin/env python3
"""GL 1.0 (compatibility): lighting, materials, fog, color material."""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *


class TestGL1Lighting(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_lights(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightf(GL_LIGHT0, GL_SPOT_CUTOFF, 45.0)
        glLighti(GL_LIGHT0, GL_SPOT_EXPONENT, 2)
        glLightfv(GL_LIGHT0, GL_POSITION, np.array([0, 0, 1, 0], 'f'))
        glLightiv(GL_LIGHT0, GL_AMBIENT, np.array([0, 0, 0, 1], 'i'))
        glGetLightfv(GL_LIGHT0, GL_POSITION, np.zeros(4, 'f'))
        glGetLightiv(GL_LIGHT0, GL_SPOT_EXPONENT, np.zeros(1, 'i'))
        glLightModelf(GL_LIGHT_MODEL_LOCAL_VIEWER, 1.0)
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, 1)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, np.array([0.2, 0.2, 0.2, 1.0], 'f'))
        glLightModeliv(GL_LIGHT_MODEL_TWO_SIDE, np.array([1], 'i'))
        glDisable(GL_LIGHTING)
        self.check_error('lights')

    def test_materials(self):
        glMaterialf(GL_FRONT, GL_SHININESS, 32.0)
        glMateriali(GL_FRONT, GL_SHININESS, 32)
        glMaterialfv(GL_FRONT, GL_DIFFUSE, np.array([1, 1, 1, 1], 'f'))
        glMaterialiv(GL_FRONT, GL_AMBIENT, np.array([0, 0, 0, 1], 'i'))
        glGetMaterialfv(GL_FRONT, GL_SHININESS, np.zeros(1, 'f'))
        glGetMaterialiv(GL_FRONT, GL_DIFFUSE, np.zeros(4, 'i'))
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        self.check_error('materials')

    def test_fog(self):
        glFogf(GL_FOG_DENSITY, 0.5)
        glFogi(GL_FOG_MODE, GL_EXP)
        glFogfv(GL_FOG_COLOR, np.array([0.5, 0.5, 0.5, 1.0], 'f'))
        glFogiv(GL_FOG_MODE, np.array([GL_LINEAR], 'i'))
        self.check_error('fog')


if __name__ == '__main__':
    unittest.main()
