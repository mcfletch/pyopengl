#! /usr/bin/env python3
"""GL 1.4 (compatibility): blend, fog coord, multi-draw, point params,
secondary color, window pos."""

import unittest
import ctypes
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from arraycompat import copy_safe
from gltestcase import GLTestCase
from OpenGL import arrays
from OpenGL.GL import *  # noqa: F401,F403


class TestGL14(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_blend_and_point(self):
        glBlendColor(0.1, 0.2, 0.3, 0.4)
        glBlendEquation(GL_FUNC_ADD)
        glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ZERO)
        glPointParameterf(GL_POINT_SIZE_MIN, 1.0)
        glPointParameteri(GL_POINT_SPRITE_COORD_ORIGIN, GL_LOWER_LEFT)
        glPointParameterfv(GL_POINT_DISTANCE_ATTENUATION, np.array([1, 0, 0], 'f'))
        glPointParameteriv(GL_POINT_FADE_THRESHOLD_SIZE, np.array([1], 'i'))
        self.check_error('blend/point')

    def test_fog_coord(self):
        glFogCoordf(1.0)
        glFogCoordd(1.0)
        glFogCoordfv(np.array([1.0], 'f'))
        glFogCoorddv(np.array([1.0], 'd'))
        glEnableClientState(GL_FOG_COORD_ARRAY)
        glFogCoordPointer(GL_FLOAT, 0, np.array([1.0, 1.0, 1.0], 'f'))
        glDisableClientState(GL_FOG_COORD_ARRAY)
        self.check_error('fog coord')

    def test_secondary_color(self):
        glBegin(GL_POINTS)
        glSecondaryColor3b(0, 0, 0)
        glSecondaryColor3s(0, 0, 0)
        glSecondaryColor3i(0, 0, 0)
        glSecondaryColor3f(0.0, 0.0, 0.0)
        glSecondaryColor3d(0.0, 0.0, 0.0)
        glSecondaryColor3ub(0, 0, 0)
        glSecondaryColor3us(0, 0, 0)
        glSecondaryColor3ui(0, 0, 0)
        glSecondaryColor3bv(np.zeros(3, 'b'))
        glSecondaryColor3sv(np.zeros(3, 'h'))
        glSecondaryColor3iv(np.zeros(3, 'i'))
        glSecondaryColor3fv(np.zeros(3, 'f'))
        glSecondaryColor3dv(np.zeros(3, 'd'))
        glSecondaryColor3ubv(np.zeros(3, 'B'))
        glSecondaryColor3usv(np.zeros(3, 'H'))
        glSecondaryColor3uiv(np.zeros(3, 'I'))
        glEnd()
        glEnableClientState(GL_SECONDARY_COLOR_ARRAY)
        glSecondaryColorPointer(3, GL_FLOAT, 0, np.zeros((3, 3), 'f'))
        glDisableClientState(GL_SECONDARY_COLOR_ARRAY)
        self.check_error('secondary color')

    def test_window_pos(self):
        glWindowPos2s(0, 0)
        glWindowPos2i(0, 0)
        glWindowPos2f(0.0, 0.0)
        glWindowPos2d(0.0, 0.0)
        glWindowPos3s(0, 0, 0)
        glWindowPos3i(0, 0, 0)
        glWindowPos3f(0.0, 0.0, 0.0)
        glWindowPos3d(0.0, 0.0, 0.0)
        glWindowPos2sv(np.zeros(2, 'h'))
        glWindowPos2iv(np.zeros(2, 'i'))
        glWindowPos2fv(np.zeros(2, 'f'))
        glWindowPos2dv(np.zeros(2, 'd'))
        glWindowPos3sv(np.zeros(3, 'h'))
        glWindowPos3iv(np.zeros(3, 'i'))
        glWindowPos3fv(np.zeros(3, 'f'))
        glWindowPos3dv(np.zeros(3, 'd'))
        self.check_error('window pos')

    def test_multi_draw(self):
        verts = np.array([(-1, -1), (1, -1), (0, 1)], 'f')
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, verts)
        glMultiDrawArrays(GL_TRIANGLES, np.array([0], 'i'), np.array([3], 'i'), 1)
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, np.array([0, 1, 2], 'I'), GL_STATIC_DRAW)
        # const void*const* indices -> array of byte offsets into the bound EBO
        offsets = (ctypes.c_void_p * 1)(0)
        glMultiDrawElements(
            GL_TRIANGLES, np.array([3], 'i'), GL_UNSIGNED_INT, offsets, 1
        )
        glDisableClientState(GL_VERTEX_ARRAY)
        self.check_error('multi draw')


class TestDrawingSeveralRangesAtOnce(GLTestCase):
    """``glMultiDrawElements`` takes an array *of pointers* to index arrays.

    Which is the reason it is worth a case of its own: every other draw call
    takes one array, and this one takes a GLvoid** the caller has to fill with
    data pointers PyOpenGL handed it.  The element counts come alongside as a
    second array, and the two have to stay the same length.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_two_index_ranges_are_drawn_from_one_call(self):
        self.require_feature('multi-draw', (1, 4), 'GL_EXT_multi_draw_arrays')
        points = np.array(
            [(i, 0, 0) for i in range(8)] + [(i, 1, 0) for i in range(8)], 'd'
        )
        indices = np.array(
            [[0, 8, 9, 1, 2, 10, 11, 3], [4, 12, 13, 5, 6, 14, 15, 7]], 'B'
        )
        pointers = arrays.GLvoidpArray.zeros((2,))
        pointers[0] = arrays.GLbyteArray.dataPointer(indices)
        pointers[1] = arrays.GLbyteArray.dataPointer(indices[1])
        # GLsizei, so signed.
        counts = copy_safe([len(row) for row in indices], 'i')

        glDisable(GL_LIGHTING)
        glEnableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        try:
            glVertexPointerd(points)
            glMultiDrawElements(
                GL_QUAD_STRIP, counts, GL_UNSIGNED_BYTE, pointers, 2
            )
        finally:
            glDisableClientState(GL_VERTEX_ARRAY)
            glEnable(GL_LIGHTING)
        self.check_error('glMultiDrawElements')


if __name__ == '__main__':
    unittest.main()
