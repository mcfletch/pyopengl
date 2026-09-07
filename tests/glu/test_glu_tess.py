#! /usr/bin/env python3
"""GLU polygon tessellation: gluNewTess / gluDeleteTess, the gluTess* polygon /
contour / vertex API, gluTessCallback (including combine and *_DATA callbacks
with original-object return), gluTessProperty / gluGetTessProperty / gluTessNormal,
and the legacy gluBeginPolygon / gluNextContour / gluEndPolygon path."""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from glutestcase import GLUTestCase
from OpenGL.GL import (
    GL_TRIANGLES,
    glBegin,
    glEnd,
    glNormal3f,
    glVertex3dv,
)
from OpenGL.GLU import (
    gluNewTess,
    gluDeleteTess,
    gluTessCallback,
    gluTessProperty,
    gluGetTessProperty,
    gluTessNormal,
    gluTessBeginPolygon,
    gluTessEndPolygon,
    gluTessBeginContour,
    gluTessEndContour,
    gluTessVertex,
    gluBeginPolygon,
    gluEndPolygon,
    gluNextContour,
    GLU_TESS_BEGIN,
    GLU_TESS_VERTEX,
    GLU_TESS_END,
    GLU_TESS_COMBINE,
    GLU_TESS_ERROR,
    GLU_TESS_EDGE_FLAG,
    GLU_TESS_BEGIN_DATA,
    GLU_TESS_VERTEX_DATA,
    GLU_TESS_END_DATA,
    GLU_TESS_WINDING_RULE,
    GLU_TESS_WINDING_ODD,
    GLU_TESS_WINDING_NONZERO,
    GLU_TESS_WINDING_ABS_GEQ_TWO,
    gluErrorString,
    GLU_TESS_BOUNDARY_ONLY,
    GLU_TESS_TOLERANCE,
    GLU_UNKNOWN,
)

# A unit square, counter-clockwise, as (x, y, z) doubles.
SQUARE = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)]


class TestGLUTess(GLUTestCase):
    def _record_tess(self, tess):
        """Wire up begin/vertex/end recording callbacks; return the event list."""
        events = []
        gluTessCallback(tess, GLU_TESS_BEGIN, lambda which: events.append(('begin', which)))
        gluTessCallback(tess, GLU_TESS_VERTEX, lambda v: events.append(('vertex', tuple(v))))
        gluTessCallback(tess, GLU_TESS_END, lambda: events.append(('end',)))
        gluTessCallback(tess, GLU_TESS_ERROR, lambda code: events.append(('error', code)))
        return events

    def test_new_delete(self):
        tess = gluNewTess()
        self.assertIsNotNone(tess)
        gluDeleteTess(tess)
        self.check_error('new/delete tess')

    def test_properties(self):
        tess = self.tessellator()
        gluTessProperty(tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_NONZERO)
        rule = gluGetTessProperty(tess, GLU_TESS_WINDING_RULE)
        self.assertEqual(int(rule), GLU_TESS_WINDING_NONZERO)
        gluTessProperty(tess, GLU_TESS_BOUNDARY_ONLY, 1)
        self.assertEqual(int(gluGetTessProperty(tess, GLU_TESS_BOUNDARY_ONLY)), 1)
        gluTessProperty(tess, GLU_TESS_TOLERANCE, 0.25)
        self.assertAlmostEqual(gluGetTessProperty(tess, GLU_TESS_TOLERANCE), 0.25, places=5)
        self.check_error('tess properties')

    def test_tess_normal(self):
        tess = self.tessellator()
        gluTessNormal(tess, 0.0, 0.0, 1.0)
        self.check_error('gluTessNormal')

    def test_tessellate_square(self):
        # A convex square should tessellate into triangle(s) and fire begin /
        # vertex / end; the vertices reported must be our original points.
        tess = self.tessellator()
        events = self._record_tess(tess)
        gluTessProperty(tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_ODD)
        gluTessNormal(tess, 0.0, 0.0, 1.0)
        gluTessBeginPolygon(tess, None)
        gluTessBeginContour(tess)
        for point in SQUARE:
            gluTessVertex(tess, np.array(point, 'd'), point)
        gluTessEndContour(tess)
        gluTessEndPolygon(tess)
        self.check_error('tessellate square')

        kinds = [e[0] for e in events]
        self.assertIn('begin', kinds)
        self.assertIn('end', kinds)
        # The primitive type (fan / strip / triangles) is the driver's choice,
        # so only require enough vertices to cover the quad and that each is one
        # of our originals (a convex quad needs no combine vertices).
        vertices = [e[1] for e in events if e[0] == 'vertex']
        self.assertGreaterEqual(len(vertices), 4)
        square = [tuple(round(c, 3) for c in p) for p in SQUARE]
        for v in vertices:
            self.assertIn(tuple(round(c, 3) for c in v), square)

    def test_combine_callback(self):
        # Two crossing contours force the tessellator to synthesize an
        # intersection vertex via the combine callback, which returns data that
        # must come back to the vertex callback by original-object return.
        tess = self.tessellator()
        events = []
        combined = []

        def vertex(v):
            events.append(v)

        def combine(coords, vertex_data, weight):
            marker = ('combined', tuple(round(c, 3) for c in coords[:3]))
            combined.append(marker)
            return marker

        gluTessCallback(tess, GLU_TESS_BEGIN, lambda which: None)
        gluTessCallback(tess, GLU_TESS_END, lambda: None)
        gluTessCallback(tess, GLU_TESS_VERTEX, vertex)
        gluTessCallback(tess, GLU_TESS_COMBINE, combine)
        gluTessProperty(tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_ODD)
        gluTessNormal(tess, 0.0, 0.0, 1.0)

        # A self-intersecting "bowtie" quad.
        bowtie = [(0, 0, 0), (1, 1, 0), (1, 0, 0), (0, 1, 0)]
        gluTessBeginPolygon(tess, None)
        gluTessBeginContour(tess)
        for point in bowtie:
            gluTessVertex(tess, np.array(point, 'd'), point)
        gluTessEndContour(tess)
        gluTessEndPolygon(tess)
        self.check_error('combine tessellation')

        self.assertTrue(combined, 'combine callback was never invoked')
        # The synthesized marker objects must reach the vertex callback intact.
        self.assertTrue(any(e in combined for e in events))

    def test_data_callbacks(self):
        # The *_DATA callback variants deliver the polygon_data object passed to
        # gluTessBeginPolygon back to Python (original-object return).
        tess = self.tessellator()
        polygon_data = {'name': 'square'}
        seen = []

        gluTessCallback(tess, GLU_TESS_BEGIN_DATA, lambda which, data: seen.append(('begin', data)))
        gluTessCallback(tess, GLU_TESS_VERTEX_DATA, lambda v, data: seen.append(('vertex', data)))
        gluTessCallback(tess, GLU_TESS_END_DATA, lambda data: seen.append(('end', data)))
        gluTessProperty(tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_ODD)
        gluTessNormal(tess, 0.0, 0.0, 1.0)

        gluTessBeginPolygon(tess, polygon_data)
        gluTessBeginContour(tess)
        for point in SQUARE:
            gluTessVertex(tess, np.array(point, 'd'), point)
        gluTessEndContour(tess)
        gluTessEndPolygon(tess)
        self.check_error('data callbacks')

        self.assertTrue(seen)
        for _, data in seen:
            self.assertIs(data, polygon_data)

    def test_edge_flag_callback(self):
        # Registering an edge-flag callback disables triangle strips/fans, so the
        # tessellator emits only independent triangles; just prove it runs.
        tess = self.tessellator()
        flags = []
        gluTessCallback(tess, GLU_TESS_BEGIN, lambda which: None)
        gluTessCallback(tess, GLU_TESS_END, lambda: None)
        gluTessCallback(tess, GLU_TESS_VERTEX, lambda v: None)
        gluTessCallback(tess, GLU_TESS_EDGE_FLAG, lambda flag: flags.append(flag))
        gluTessNormal(tess, 0.0, 0.0, 1.0)
        gluTessBeginPolygon(tess, None)
        gluTessBeginContour(tess)
        for point in SQUARE:
            gluTessVertex(tess, np.array(point, 'd'), point)
        gluTessEndContour(tess)
        gluTessEndPolygon(tess)
        self.check_error('edge flag callback')
        self.assertTrue(flags, 'edge-flag callback was never invoked')

    def test_legacy_contour_api(self):
        # The pre-1.2 gluBeginPolygon / gluNextContour / gluEndPolygon names
        # still drive the same tessellator.
        tess = self.tessellator()
        events = self._record_tess(tess)
        gluTessProperty(tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_ODD)
        gluTessNormal(tess, 0.0, 0.0, 1.0)
        # Outer square plus an inner square contour (a hole) started with
        # gluNextContour, so the polygon has fillable area and emits geometry.
        inner = [(0.25, 0.25, 0.0), (0.75, 0.25, 0.0),
                 (0.75, 0.75, 0.0), (0.25, 0.75, 0.0)]
        gluBeginPolygon(tess)
        for point in SQUARE:
            gluTessVertex(tess, np.array(point, 'd'), point)
        gluNextContour(tess, GLU_UNKNOWN)
        for point in inner:
            gluTessVertex(tess, np.array(point, 'd'), point)
        gluEndPolygon(tess)
        self.check_error('legacy contour api')
        self.assertTrue(events)


    def test_a_callback_may_be_a_gl_entry_point(self):
        """The classic arrangement: tessellate straight into immediate mode.

        ``gluTessCallback(tess, GLU_TESS_BEGIN, glBegin)`` hands GLU the
        wrapper itself, so GLU calls into PyOpenGL from a C callback with the
        primitive enum it chose.  A Python function in between would convert
        the argument on the way; this way the wrapper is what receives it.
        """
        tess = self.tessellator()
        gluTessProperty(tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_ODD)
        gluTessNormal(tess, 0.0, 0.0, 1.0)
        gluTessCallback(tess, GLU_TESS_BEGIN, glBegin)
        gluTessCallback(tess, GLU_TESS_VERTEX, glVertex3dv)
        gluTessCallback(tess, GLU_TESS_END, glEnd)
        gluTessCallback(tess, GLU_TESS_COMBINE, lambda coords, data, weight: coords)

        glNormal3f(0.0, 0.0, 1.0)
        gluTessBeginPolygon(tess, None)
        gluTessBeginContour(tess)
        for point in SQUARE:
            gluTessVertex(tess, np.array(point, 'd'), np.array(point, 'd'))
        gluTessEndContour(tess)
        gluTessEndPolygon(tess)
        self.check_error('tessellating into immediate mode')

    def test_two_overlapping_contours_combine_at_both_crossings(self):
        """SF#2354596: what the combine callback returns has to reach the
        vertex callback, and be distinguishable there from an original vertex.

        Two squares overlapping in one corner, tessellated in the
        intersection-only winding rule, cross at exactly two points -- so the
        combine callback is called twice, and the objects it returns arrive at
        the vertex callback alongside the originals.  The count is the
        assertion the report was about: collecting the results once and losing
        them on the second crossing is the shape of the defect.
        """
        tess = self.tessellator()
        arrived = []
        crossings = []

        def vertex(vertex_data, polygon_data=None):
            arrived.append(vertex_data)
            return polygon_data

        def combine(coords, vertex_data, weights, _=None):
            crossings.append(coords)
            return ('combined', coords)

        def error(code):
            raise AssertionError(gluErrorString(code))

        gluTessProperty(tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_ABS_GEQ_TWO)
        gluTessCallback(tess, GLU_TESS_BEGIN, lambda which: None)
        gluTessCallback(tess, GLU_TESS_END, lambda: None)
        # An edge-flag callback switches strips and fans off, so every vertex
        # arrives once as part of an independent triangle.
        gluTessCallback(tess, GLU_TESS_EDGE_FLAG, lambda flag: None)
        gluTessCallback(tess, GLU_TESS_VERTEX, vertex)
        gluTessCallback(tess, GLU_TESS_ERROR, error)
        gluTessCallback(tess, GLU_TESS_COMBINE, combine)

        gluTessBeginPolygon(tess, arrived)
        for contour in (
            [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)],
            [(0.5, 0, -0.5), (1.5, 0, -0.5), (1.5, 0, 0.5), (0.5, 0, 0.5)],
        ):
            gluTessBeginContour(tess)
            for point in contour:
                data = np.array(point, 'd')
                gluTessVertex(tess, data, ('original', data))
            gluTessEndContour(tess)
        gluTessEndPolygon(tess)
        self.check_error('intersecting two contours')

        self.assertTrue(arrived, 'no vertex reached the callback')
        combined = [v for v in arrived if v[0] == 'combined']
        original = [v for v in arrived if v[0] == 'original']
        self.assertTrue(combined, ('no combined vertex arrived', arrived))
        self.assertTrue(original, ('no original vertex arrived', arrived))
        self.assertEqual(
            len(crossings), 2,
            'two squares overlapping in one corner cross at two points; the '
            'combine callback saw %d' % (len(crossings),),
        )


if __name__ == '__main__':
    unittest.main()
