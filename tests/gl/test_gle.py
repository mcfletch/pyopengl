#! /usr/bin/env python3
"""GLE: the tubing and extrusion library, which draws through a GL context.

GLE is a separate library from GL and GLU -- an image carrying Mesa often has
no libgle at all -- so every case here skips where it is absent rather than
failing.  What is asserted is that the entry points reach the library with the
arrays PyOpenGL converted for them and that geometry comes back out: the
polyline and contour arguments are the interesting part, since each is a count
PyOpenGL derives from the array it was given rather than one the caller passes.

Measured through the GL feedback buffer, which records the primitives a draw
would have produced without rasterising them.  That is a fact about what the
call did rather than about whether it raised, and it needs no framebuffer to
read back.
"""

import ctypes
import unittest

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL import GLE
from OpenGL.GL import *  # noqa: F401,F403

#: A four-segment path.  GLE reads the first and last points as direction hints
#: and draws the segments between the rest, so a path needs at least four.
POLYLINE = [
    (-6.0, 6.0, 0.0),
    (6.0, 6.0, 0.0),
    (6.0, -6.0, 0.0),
    (-6.0, -6.0, 0.0),
    (-6.0, 6.0, 0.0),
    (6.0, 6.0, 0.0),
]

COLOURS = [
    (0.0, 0.0, 0.0),
    (0.0, 0.8, 0.3),
    (0.8, 0.3, 0.0),
    (0.2, 0.3, 0.9),
    (0.2, 0.8, 0.5),
    (0.0, 0.0, 0.0),
]

RADII = [1.0, 1.0, 3.0, 0.5, 2.0, 1.0]

#: Half-width of the orthographic view the feedback helper sets up: the
#: geometry below reaches +/-6 and the tubing swept around it a little
#: further, so the clip volume has to be wider than either.
EXTENT = 20.0

#: A closed square contour to sweep along a path.
CONTOUR = [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0)]


class GLETestCase(GLTestCase):
    """A compatibility context, skipped where the GLE library is absent."""

    profile = 'compatibility'
    gl_version = (2, 1)

    def setUp(self):
        super().setUp()
        if not GLE.gleSetJoinStyle:
            self.skipTest('the GLE extrusion library is not installed here')

    def feedback(self, draw, size=1 << 16):
        """The number of floats ``draw`` fed back, having drawn nothing.

        ``GL_FEEDBACK`` makes the pipeline write what it would have rasterised
        into a buffer instead.  An empty buffer means the call reached the
        library and the library emitted nothing, which is the failure a call
        that merely does not raise cannot tell apart from success.

        Feedback records what survives transformation and clipping, so the
        projection has to contain the geometry: with the identity matrix the
        clip volume is the unit cube and everything here falls outside it,
        which reads as "GLE drew nothing" and is really "the view was too
        small".
        """
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-EXTENT, EXTENT, -EXTENT, EXTENT, -EXTENT, EXTENT)
        glMatrixMode(GL_MODELVIEW)
        buffer = (ctypes.c_float * size)()
        glFeedbackBuffer(size, GL_3D, buffer)
        glRenderMode(GL_FEEDBACK)
        try:
            draw()
        finally:
            # The wrapper hands back the written prefix of the buffer rather
            # than the count the C call returns.
            written = glRenderMode(GL_RENDER)
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
        return len(written)


class TestSweepingAlongAPath(GLETestCase):
    def test_a_poly_cone_emits_geometry(self):
        def draw():
            GLE.gleSetJoinStyle(
                GLE.TUBE_NORM_EDGE | GLE.TUBE_JN_ANGLE | GLE.TUBE_JN_CAP
            )
            GLE.glePolyCone(POLYLINE, COLOURS, RADII)

        written = self.feedback(draw)
        self.assertGreater(written, 0, 'glePolyCone fed back no geometry')
        self.check_error('glePolyCone')

    def test_a_poly_cylinder_emits_geometry(self):
        def draw():
            GLE.glePolyCylinder(POLYLINE, COLOURS, 1.0)

        self.assertGreater(self.feedback(draw), 0)
        self.check_error('glePolyCylinder')

    def test_an_extrusion_sweeps_a_contour(self):
        """``gleExtrusion`` takes a contour and its normals as well as a path.

        Four arrays, each of whose lengths PyOpenGL derives rather than being
        told, which is what makes this the case worth having.
        """
        contour = np.array(CONTOUR, 'd')
        normals = np.array(
            [(-1.0, 0.0), (0.0, -1.0), (1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)], 'd'
        )
        up = np.array([0.0, 1.0, 0.0], 'd')

        def draw():
            GLE.gleExtrusion(
                contour, normals, up,
                np.array(POLYLINE, 'd'), np.array(COLOURS, 'd'),
            )

        self.assertGreater(self.feedback(draw), 0)
        self.check_error('gleExtrusion')


class TestTheJoinStyleIsReadBack(GLETestCase):
    def test_what_was_set_is_what_is_reported(self):
        wanted = GLE.TUBE_NORM_EDGE | GLE.TUBE_JN_ANGLE | GLE.TUBE_JN_CAP
        GLE.gleSetJoinStyle(wanted)
        self.assertEqual(GLE.gleGetJoinStyle(), wanted)
        self.check_error('gleGetJoinStyle')

    def test_the_side_count_is_read_back(self):
        GLE.gleSetNumSides(12)
        self.assertEqual(GLE.gleGetNumSides(), 12)
        self.check_error('gleGetNumSides')


if __name__ == '__main__':
    unittest.main()
