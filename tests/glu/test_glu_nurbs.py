#! /usr/bin/env python3
"""GLU NURBS rendering: gluNewNurbsRenderer / gluDeleteNurbsRenderer, the
gluNurbsProperty / gluGetNurbsProperty state, gluNurbsCallback /
gluNurbsCallbackData(EXT), gluNurbsCurve / gluNurbsSurface (auto-computed order
and stride), the gluBegin*/gluEnd* scoping, and gluPwlCurve trimming."""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from glutestcase import GLUTestCase, requireEntryPoint
from OpenGL.GL import GL_MAP1_VERTEX_3, GL_MAP2_VERTEX_3
from OpenGL.GLU import (
    gluNewNurbsRenderer,
    gluDeleteNurbsRenderer,
    gluNurbsProperty,
    gluGetNurbsProperty,
    gluNurbsCallback,
    gluNurbsCallbackData,
    gluNurbsCallbackDataEXT,
    gluNurbsCurve,
    gluNurbsSurface,
    gluPwlCurve,
    gluBeginCurve,
    gluEndCurve,
    gluBeginSurface,
    gluEndSurface,
    gluBeginTrim,
    gluEndTrim,
    gluLoadSamplingMatrices,
    GLU_SAMPLING_TOLERANCE,
    GLU_DISPLAY_MODE,
    GLU_FILL,
    GLU_OUTLINE_POLYGON,
    GLU_NURBS_ERROR,
    GLU_MAP1_TRIM_2,
)

# A cubic Bezier needs order-4 knots (0,0,0,0,1,1,1,1) over 4 control points.
KNOTS = np.array([0, 0, 0, 0, 1, 1, 1, 1], 'f')


def _curve_control():
    return np.array([[-1, -1, 0], [-0.5, 1, 0], [0.5, -1, 0], [1, 1, 0]], 'f')


def _surface_control():
    # built as nested lists so it works on the ctypes fallback (no numpy
    # multi-index assignment) as well as numpy
    return np.array(
        [[[i / 3.0 - 0.5, j / 3.0 - 0.5, 0.0] for j in range(4)] for i in range(4)],
        'f',
    )


class TestGLUNurbs(GLUTestCase):
    def setUp(self):
        super(TestGLUNurbs, self).setUp()
        self.set_projection()

    def test_new_delete(self):
        nurb = gluNewNurbsRenderer()
        self.assertIsNotNone(nurb)
        gluDeleteNurbsRenderer(nurb)
        self.check_error('new/delete nurbs')

    def test_properties(self):
        nurb = self.nurbs()
        gluNurbsProperty(nurb, GLU_SAMPLING_TOLERANCE, 33.0)
        self.assertAlmostEqual(
            gluGetNurbsProperty(nurb, GLU_SAMPLING_TOLERANCE), 33.0, places=3
        )
        gluNurbsProperty(nurb, GLU_DISPLAY_MODE, GLU_FILL)
        self.assertEqual(
            int(gluGetNurbsProperty(nurb, GLU_DISPLAY_MODE)), GLU_FILL
        )
        self.check_error('nurbs properties')

    def test_error_callback(self):
        nurb = self.nurbs()
        errors = []
        gluNurbsCallback(nurb, GLU_NURBS_ERROR, lambda code: errors.append(code))
        self.assertIn(GLU_NURBS_ERROR, nurb.callbacks)
        self.check_error('gluNurbsCallback')

    def test_callback_data(self):
        # gluNurbsCallbackData notes a Python object for later original-object
        # return; the call must accept an arbitrary Python object.
        requireEntryPoint(gluNurbsCallbackData, 'gluNurbsCallbackData')
        nurb = self.nurbs()
        gluNurbsCallbackData(nurb, {'tag': 'curve'})
        gluNurbsCallbackDataEXT(nurb, ['list', 'data'])
        self.check_error('gluNurbsCallbackData')

    def test_curve(self):
        # gluNurbsCurve computes knotCount / order / stride from the arrays.
        nurb = self.nurbs()
        gluBeginCurve(nurb)
        gluNurbsCurve(nurb, KNOTS, _curve_control(), GL_MAP1_VERTEX_3)
        gluEndCurve(nurb)
        self.check_error('gluNurbsCurve')

    def test_surface(self):
        nurb = self.nurbs()
        gluBeginSurface(nurb)
        gluNurbsSurface(nurb, KNOTS, KNOTS, _surface_control(), GL_MAP2_VERTEX_3)
        gluEndSurface(nurb)
        self.check_error('gluNurbsSurface')

    def test_trimmed_surface(self):
        # A trim loop is a piecewise-linear curve in parametric (u, v) space.
        nurb = self.nurbs()
        gluNurbsProperty(nurb, GLU_DISPLAY_MODE, GLU_OUTLINE_POLYGON)
        gluBeginSurface(nurb)
        gluNurbsSurface(nurb, KNOTS, KNOTS, _surface_control(), GL_MAP2_VERTEX_3)
        gluBeginTrim(nurb)
        loop = np.array([[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]], 'f')
        gluPwlCurve(nurb, loop, GLU_MAP1_TRIM_2)
        gluEndTrim(nurb)
        gluEndSurface(nurb)
        self.check_error('trimmed surface')

    def test_load_sampling_matrices(self):
        from OpenGL.GL import (
            glGetDoublev,
            glGetIntegerv,
            GL_MODELVIEW_MATRIX,
            GL_PROJECTION_MATRIX,
            GL_VIEWPORT,
        )
        from OpenGL.GLU import GLU_NURBS_MODE, GLU_NURBS_TESSELLATOR

        nurb = self.nurbs()
        gluNurbsProperty(nurb, GLU_NURBS_MODE, GLU_NURBS_TESSELLATOR)
        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj = glGetDoublev(GL_PROJECTION_MATRIX)
        view = glGetIntegerv(GL_VIEWPORT)
        gluLoadSamplingMatrices(nurb, model, proj, view)
        self.check_error('gluLoadSamplingMatrices')


if __name__ == '__main__':
    unittest.main()
