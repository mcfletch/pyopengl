#! /usr/bin/env python3
"""GL 1.0 (compatibility): matrix stack, transforms, clip planes."""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from arraycompat import copy_safe
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


class TestGL1Transform(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_matrix_stack(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glPushMatrix()
        glLoadMatrixf(np.identity(4, 'f'))
        glLoadMatrixd(np.identity(4, 'd'))
        glMultMatrixf(np.identity(4, 'f'))
        glMultMatrixd(np.identity(4, 'd'))
        glTranslatef(1.0, 0.0, 0.0)
        glTranslated(1.0, 0.0, 0.0)
        glRotatef(45.0, 0.0, 0.0, 1.0)
        glRotated(45.0, 0.0, 0.0, 1.0)
        glScalef(2.0, 2.0, 2.0)
        glScaled(2.0, 2.0, 2.0)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glFrustum(-1, 1, -1, 1, 1, 10)
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)
        glMatrixMode(GL_TEXTURE)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        self.check_error('matrix stack')

    def test_viewport_depthrange(self):
        glViewport(0, 0, self.width, self.height)
        glDepthRange(0.0, 1.0)
        self.check_error('viewport/depthrange')

    def test_clip_planes(self):
        glEnable(GL_CLIP_PLANE0)
        glClipPlane(GL_CLIP_PLANE0, copy_safe([0.0, 1.0, 0.0, 0.0], 'd'))
        plane = glGetClipPlane(GL_CLIP_PLANE0)
        self.assertEqual(len(plane), 4)
        glDisable(GL_CLIP_PLANE0)
        self.check_error('clip planes')


if __name__ == '__main__':
    unittest.main()
