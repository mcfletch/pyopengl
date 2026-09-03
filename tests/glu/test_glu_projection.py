#! /usr/bin/env python3
"""GLU projection / matrix helpers: gluPerspective, gluOrtho2D, gluLookAt,
gluPickMatrix, gluProject, gluUnProject, gluUnProject4."""

import unittest

from glutestcase import GLUTestCase, requireEntryPoint
from OpenGL.GL import (
    glMatrixMode,
    glLoadIdentity,
    glGetDoublev,
    glGetIntegerv,
    GL_PROJECTION,
    GL_MODELVIEW,
    GL_MODELVIEW_MATRIX,
    GL_PROJECTION_MATRIX,
    GL_VIEWPORT,
)
from OpenGL.GLU import (
    gluPerspective,
    gluOrtho2D,
    gluLookAt,
    gluPickMatrix,
    gluProject,
    gluUnProject,
    gluUnProject4,
)


class TestGLUProjection(GLUTestCase):
    def test_perspective(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, float(self.width) / self.height, 0.5, 50.0)
        glMatrixMode(GL_MODELVIEW)
        self.check_error('gluPerspective')

    def test_ortho2d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0.0, 1.0, 0.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        self.check_error('gluOrtho2D')

    def test_look_at(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        self.check_error('gluLookAt')

    def test_pick_matrix(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        viewport = glGetIntegerv(GL_VIEWPORT)
        gluPickMatrix(64.0, 64.0, 5.0, 5.0, viewport)
        gluPerspective(45.0, 1.0, 0.5, 50.0)
        glMatrixMode(GL_MODELVIEW)
        self.check_error('gluPickMatrix')

    def test_project_roundtrip(self):
        # Project an object-space point to window space, then back, and confirm
        # we recover the original coordinate (proves both wrappers, including
        # the auto-filled model/proj/view matrices).
        self.set_projection()
        gluLookAt(0, 0, 4, 0, 0, 0, 0, 1, 0)
        obj = (0.3, -0.2, 0.0)
        win = gluProject(*obj)
        self.assertEqual(len(win), 3)
        back = gluUnProject(*win)
        for got, want in zip(back, obj):
            self.assertAlmostEqual(got, want, places=3)
        self.check_error('gluProject/gluUnProject')

    def test_project_explicit_matrices(self):
        # Pass model/proj/view explicitly rather than relying on the GL state.
        self.set_projection()
        gluLookAt(0, 0, 4, 0, 0, 0, 0, 1, 0)  # move the origin off the eye plane
        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        proj = glGetDoublev(GL_PROJECTION_MATRIX)
        view = glGetIntegerv(GL_VIEWPORT)
        win = gluProject(0.0, 0.0, 0.0, model, proj, view)
        self.assertEqual(len(win), 3)
        self.check_error('gluProject explicit')

    def test_unproject4(self):
        # gluUnProject4 carries the homogeneous clip-w plus the near/far depth
        # range; the wrapper must forward all of them.
        requireEntryPoint(gluUnProject4, 'gluUnProject4')
        self.set_projection()
        result = gluUnProject4(64.0, 64.0, 0.5, 1.0, near=0.0, far=1.0)
        self.assertEqual(len(result), 4)
        self.check_error('gluUnProject4')


if __name__ == '__main__':
    unittest.main()
