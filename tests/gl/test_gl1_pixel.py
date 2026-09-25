#! /usr/bin/env python3
"""GL 1.0 (compatibility): pixel store/transfer/maps, draw/copy/bitmap."""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *


class TestGL1Pixel(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_pixel_store_transfer(self):
        glPixelStoref(GL_PACK_ALIGNMENT, 1.0)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glPixelTransferf(GL_RED_SCALE, 1.0)
        glPixelTransferi(GL_MAP_COLOR, GL_FALSE)
        glPixelZoom(1.0, 1.0)
        self.check_error('pixel store/transfer')

    def test_pixel_maps(self):
        glPixelMapfv(GL_PIXEL_MAP_R_TO_R, 2, np.array([0.0, 1.0], 'f'))
        glPixelMapuiv(GL_PIXEL_MAP_I_TO_I, 2, np.array([0, 1], 'I'))
        glPixelMapusv(GL_PIXEL_MAP_S_TO_S, 2, np.array([0, 1], 'H'))
        glGetPixelMapfv(GL_PIXEL_MAP_R_TO_R, np.zeros(2, 'f'))
        glGetPixelMapuiv(GL_PIXEL_MAP_I_TO_I, np.zeros(2, 'I'))
        glGetPixelMapusv(GL_PIXEL_MAP_S_TO_S, np.zeros(2, 'H'))
        self.check_error('pixel maps')

    def test_draw_copy_bitmap(self):
        glRasterPos2i(0, 0)
        glDrawPixels(2, 2, GL_RGBA, GL_UNSIGNED_BYTE, np.zeros((2, 2, 4), 'B'))
        glCopyPixels(0, 0, 2, 2, GL_COLOR)
        glRasterPos2i(0, 0)
        glBitmap(8, 8, 0, 0, 8, 0, np.zeros(8, 'B'))
        self.check_error('draw/copy/bitmap')


if __name__ == '__main__':
    unittest.main()
