#! /usr/bin/env python3
"""GL 1.0 (compatibility): immediate-mode vertex specification variants.

Exercises every glVertex/glColor/glNormal/glTexCoord/glRasterPos/glIndex/
glEdgeFlag/glRect type variant inside a compatibility context.
"""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL import _configflags
from OpenGL.GL import *  # noqa: F401,F403  (legacy suite touches hundreds of names)


class TestGL1Immediate(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_vertex_color_normal_texcoord(self):
        glBegin(GL_POINTS)
        # glVertex {2,3,4} x {s,i,f,d} (+ vector forms)
        glVertex2s(0, 0)
        glVertex2i(0, 0)
        glVertex2f(0.0, 0.0)
        glVertex2d(0.0, 0.0)
        glVertex3s(0, 0, 0)
        glVertex3i(0, 0, 0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3d(0.0, 0.0, 0.0)
        glVertex4s(0, 0, 0, 1)
        glVertex4i(0, 0, 0, 1)
        glVertex4f(0.0, 0.0, 0.0, 1.0)
        glVertex4d(0.0, 0.0, 0.0, 1.0)
        glVertex2sv(np.array([0, 0], 'h'))
        glVertex2iv(np.array([0, 0], 'i'))
        glVertex2fv(np.array([0, 0], 'f'))
        glVertex2dv(np.array([0, 0], 'd'))
        glVertex3sv(np.array([0, 0, 0], 'h'))
        glVertex3iv(np.array([0, 0, 0], 'i'))
        glVertex3fv(np.array([0, 0, 0], 'f'))
        glVertex3dv(np.array([0, 0, 0], 'd'))
        glVertex4sv(np.array([0, 0, 0, 1], 'h'))
        glVertex4iv(np.array([0, 0, 0, 1], 'i'))
        glVertex4fv(np.array([0, 0, 0, 1], 'f'))
        glVertex4dv(np.array([0, 0, 0, 1], 'd'))
        # glColor {3,4} x many types (+ vector)
        glColor3b(0, 0, 0)
        glColor3s(0, 0, 0)
        glColor3i(0, 0, 0)
        glColor3f(0.0, 0.0, 0.0)
        glColor3d(0.0, 0.0, 0.0)
        glColor3ub(0, 0, 0)
        glColor3us(0, 0, 0)
        glColor3ui(0, 0, 0)
        glColor4b(0, 0, 0, 0)
        glColor4s(0, 0, 0, 0)
        glColor4i(0, 0, 0, 0)
        glColor4f(0.0, 0.0, 0.0, 1.0)
        glColor4d(0.0, 0.0, 0.0, 1.0)
        glColor4ub(0, 0, 0, 255)
        glColor4us(0, 0, 0, 0)
        glColor4ui(0, 0, 0, 0)
        glColor3bv(np.array([0, 0, 0], 'b'))
        glColor3sv(np.array([0, 0, 0], 'h'))
        glColor3iv(np.array([0, 0, 0], 'i'))
        glColor3fv(np.array([0, 0, 0], 'f'))
        glColor3dv(np.array([0, 0, 0], 'd'))
        glColor3ubv(np.array([0, 0, 0], 'B'))
        glColor3usv(np.array([0, 0, 0], 'H'))
        glColor3uiv(np.array([0, 0, 0], 'I'))
        glColor4bv(np.array([0, 0, 0, 0], 'b'))
        glColor4sv(np.array([0, 0, 0, 0], 'h'))
        glColor4iv(np.array([0, 0, 0, 0], 'i'))
        glColor4fv(np.array([0, 0, 0, 1], 'f'))
        glColor4dv(np.array([0, 0, 0, 1], 'd'))
        glColor4ubv(np.array([0, 0, 0, 255], 'B'))
        glColor4usv(np.array([0, 0, 0, 0], 'H'))
        glColor4uiv(np.array([0, 0, 0, 0], 'I'))
        # glNormal3 x {b,s,i,f,d} (+ vector)
        glNormal3b(0, 0, 1)
        glNormal3s(0, 0, 1)
        glNormal3i(0, 0, 1)
        glNormal3f(0.0, 0.0, 1.0)
        glNormal3d(0.0, 0.0, 1.0)
        glNormal3bv(np.array([0, 0, 1], 'b'))
        glNormal3sv(np.array([0, 0, 1], 'h'))
        glNormal3iv(np.array([0, 0, 1], 'i'))
        glNormal3fv(np.array([0, 0, 1], 'f'))
        glNormal3dv(np.array([0, 0, 1], 'd'))
        # glTexCoord {1,2,3,4} x {s,i,f,d} (+ vector)
        glTexCoord1s(0)
        glTexCoord1i(0)
        glTexCoord1f(0.0)
        glTexCoord1d(0.0)
        glTexCoord2s(0, 0)
        glTexCoord2i(0, 0)
        glTexCoord2f(0.0, 0.0)
        glTexCoord2d(0.0, 0.0)
        glTexCoord3s(0, 0, 0)
        glTexCoord3i(0, 0, 0)
        glTexCoord3f(0.0, 0.0, 0.0)
        glTexCoord3d(0.0, 0.0, 0.0)
        glTexCoord4s(0, 0, 0, 1)
        glTexCoord4i(0, 0, 0, 1)
        glTexCoord4f(0.0, 0.0, 0.0, 1.0)
        glTexCoord4d(0.0, 0.0, 0.0, 1.0)
        glTexCoord1sv(np.array([0], 'h'))
        glTexCoord1iv(np.array([0], 'i'))
        glTexCoord1fv(np.array([0], 'f'))
        glTexCoord1dv(np.array([0], 'd'))
        glTexCoord2sv(np.array([0, 0], 'h'))
        glTexCoord2iv(np.array([0, 0], 'i'))
        glTexCoord2fv(np.array([0, 0], 'f'))
        glTexCoord2dv(np.array([0, 0], 'd'))
        glTexCoord3sv(np.array([0, 0, 0], 'h'))
        glTexCoord3iv(np.array([0, 0, 0], 'i'))
        glTexCoord3fv(np.array([0, 0, 0], 'f'))
        glTexCoord3dv(np.array([0, 0, 0], 'd'))
        glTexCoord4sv(np.array([0, 0, 0, 1], 'h'))
        glTexCoord4iv(np.array([0, 0, 0, 1], 'i'))
        glTexCoord4fv(np.array([0, 0, 0, 1], 'f'))
        glTexCoord4dv(np.array([0, 0, 0, 1], 'd'))
        glEnd()
        self.check_error('vertex/color/normal/texcoord')

    def test_rasterpos_index_edgeflag(self):
        glRasterPos2s(0, 0)
        glRasterPos2i(0, 0)
        glRasterPos2f(0.0, 0.0)
        glRasterPos2d(0.0, 0.0)
        glRasterPos3s(0, 0, 0)
        glRasterPos3i(0, 0, 0)
        glRasterPos3f(0.0, 0.0, 0.0)
        glRasterPos3d(0.0, 0.0, 0.0)
        glRasterPos4s(0, 0, 0, 1)
        glRasterPos4i(0, 0, 0, 1)
        glRasterPos4f(0.0, 0.0, 0.0, 1.0)
        glRasterPos4d(0.0, 0.0, 0.0, 1.0)
        glRasterPos2sv(np.array([0, 0], 'h'))
        glRasterPos2iv(np.array([0, 0], 'i'))
        glRasterPos2fv(np.array([0, 0], 'f'))
        glRasterPos2dv(np.array([0, 0], 'd'))
        glRasterPos3sv(np.array([0, 0, 0], 'h'))
        glRasterPos3iv(np.array([0, 0, 0], 'i'))
        glRasterPos3fv(np.array([0, 0, 0], 'f'))
        glRasterPos3dv(np.array([0, 0, 0], 'd'))
        glRasterPos4sv(np.array([0, 0, 0, 1], 'h'))
        glRasterPos4iv(np.array([0, 0, 0, 1], 'i'))
        glRasterPos4fv(np.array([0, 0, 0, 1], 'f'))
        glRasterPos4dv(np.array([0, 0, 0, 1], 'd'))
        glBegin(GL_POINTS)
        glIndexs(0)
        glIndexi(0)
        glIndexf(0.0)
        glIndexd(0.0)
        glIndexsv(np.array([0], 'h'))
        glIndexiv(np.array([0], 'i'))
        glIndexfv(np.array([0], 'f'))
        glIndexdv(np.array([0], 'd'))
        glEdgeFlag(GL_TRUE)
        glEdgeFlagv(np.array([1], 'B'))
        glEnd()
        self.check_error('rasterpos/index/edgeflag')

    def test_rect_variants(self):
        glRects(-1, -1, 1, 1)
        glRecti(-1, -1, 1, 1)
        glRectf(-1.0, -1.0, 1.0, 1.0)
        glRectd(-1.0, -1.0, 1.0, 1.0)
        glRectsv(np.array([-1, -1], 'h'), np.array([1, 1], 'h'))
        glRectiv(np.array([-1, -1], 'i'), np.array([1, 1], 'i'))
        glRectfv(np.array([-1, -1], 'f'), np.array([1, 1], 'f'))
        glRectdv(np.array([-1, -1], 'd'), np.array([1, 1], 'd'))
        self.check_error('rect')


class TestWhatAVertexCallAccepts(GLTestCase):
    """The immediate-mode calls take several spellings of the same vertex."""

    profile = 'compatibility'
    gl_version = (2, 1)

    @unittest.skipIf(
        _configflags.ERROR_ON_COPY,
        'the list spellings here are among the ones under test, and a run that '
        'has refused implicit copies refuses them',
    )
    def test_the_typed_spellings_agree_inside_one_primitive(self):
        glDisable(GL_LIGHTING)
        glBegin(GL_TRIANGLES)
        try:
            glVertex3f(0.0, 1.0, 0.0)
            glVertex3fv([-1, 0, 0])
            glVertex3dv([1, 0, 0])
        finally:
            glEnd()
        self.check_error('immediate-mode vertex spellings')

    @unittest.skipIf(
        not _configflags.ARRAY_SIZE_CHECKING,
        'ARRAY_SIZE_CHECKING is off, so a four-element vertex is not refused',
    )
    @unittest.skipIf(
        _configflags.ERROR_ON_COPY,
        'ERROR_ON_COPY refuses the list before its size is looked at',
    )
    def test_a_wrongly_sized_vertex_is_refused(self):
        """``glVertex3dv`` takes three doubles, and four is a caller's error."""
        glBegin(GL_TRIANGLES)
        try:
            with self.assertRaises(ValueError):
                glVertex3dv([1, 0, 4, 5])
        finally:
            glEnd()

    def test_a_colour_component_that_is_not_a_number_is_refused(self):
        """``glColor4f`` takes floats; an object is not one.

        Zero is, though -- an int converts -- so the case asserts both, or it
        would pass on a wrapper that refused everything.
        """
        glColor4f(0, 1, 1, 0)
        for rejected in (object(), object):
            with self.assertRaises(Exception):
                glColor4f(0, 1, 1, rejected)


if __name__ == '__main__':
    unittest.main()
