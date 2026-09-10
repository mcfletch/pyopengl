#! /usr/bin/env python3
"""Legacy immediate-mode extension aliases: multitexture, window-pos,
secondary-colour, fog-coord, NV half-float.  These predate (or mirror) core
entry points; exercised in a compatibility context, skipped where unexported."""

import unittest
from arraycompat import np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.ARB.multitexture import *  # noqa: F401,F403
from OpenGL.GL.ARB.window_pos import *  # noqa: F401,F403
from OpenGL.GL.MESA.window_pos import *  # noqa: F401,F403
from OpenGL.GL.EXT.secondary_color import *  # noqa: F401,F403
from OpenGL.GL.NV.half_float import *  # noqa: F401,F403


class TestMultitextureARB(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_multitexture(self):
        self.require_extension('GL_ARB_multitexture')
        with self.allow_missing():
            glActiveTextureARB(GL_TEXTURE0)
            glClientActiveTextureARB(GL_TEXTURE0)
            glMultiTexCoord1dARB(GL_TEXTURE0, 1.0)
            glMultiTexCoord1dvARB(GL_TEXTURE0, np.zeros(1, 'd'))
            glMultiTexCoord1fARB(GL_TEXTURE0, 1.0)
            glMultiTexCoord1fvARB(GL_TEXTURE0, np.zeros(1, 'f'))
            glMultiTexCoord1iARB(GL_TEXTURE0, 1)
            glMultiTexCoord1ivARB(GL_TEXTURE0, np.zeros(1, 'i'))
            glMultiTexCoord1sARB(GL_TEXTURE0, 1)
            glMultiTexCoord1svARB(GL_TEXTURE0, np.zeros(1, 'h'))
            glMultiTexCoord2dARB(GL_TEXTURE0, 1, 2)
            glMultiTexCoord2dvARB(GL_TEXTURE0, np.zeros(2, 'd'))
            glMultiTexCoord2fARB(GL_TEXTURE0, 1, 2)
            glMultiTexCoord2fvARB(GL_TEXTURE0, np.zeros(2, 'f'))
            glMultiTexCoord2iARB(GL_TEXTURE0, 1, 2)
            glMultiTexCoord2ivARB(GL_TEXTURE0, np.zeros(2, 'i'))
            glMultiTexCoord2sARB(GL_TEXTURE0, 1, 2)
            glMultiTexCoord2svARB(GL_TEXTURE0, np.zeros(2, 'h'))
            glMultiTexCoord3dARB(GL_TEXTURE0, 1, 2, 3)
            glMultiTexCoord3dvARB(GL_TEXTURE0, np.zeros(3, 'd'))
            glMultiTexCoord3fARB(GL_TEXTURE0, 1, 2, 3)
            glMultiTexCoord3fvARB(GL_TEXTURE0, np.zeros(3, 'f'))
            glMultiTexCoord3iARB(GL_TEXTURE0, 1, 2, 3)
            glMultiTexCoord3ivARB(GL_TEXTURE0, np.zeros(3, 'i'))
            glMultiTexCoord3sARB(GL_TEXTURE0, 1, 2, 3)
            glMultiTexCoord3svARB(GL_TEXTURE0, np.zeros(3, 'h'))
            glMultiTexCoord4dARB(GL_TEXTURE0, 1, 2, 3, 4)
            glMultiTexCoord4dvARB(GL_TEXTURE0, np.zeros(4, 'd'))
            glMultiTexCoord4fARB(GL_TEXTURE0, 1, 2, 3, 4)
            glMultiTexCoord4fvARB(GL_TEXTURE0, np.zeros(4, 'f'))
            glMultiTexCoord4iARB(GL_TEXTURE0, 1, 2, 3, 4)
            glMultiTexCoord4ivARB(GL_TEXTURE0, np.zeros(4, 'i'))
            glMultiTexCoord4sARB(GL_TEXTURE0, 1, 2, 3, 4)
            glMultiTexCoord4svARB(GL_TEXTURE0, np.zeros(4, 'h'))
        self.check_error('multitexture ARB')


class TestWindowPos(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_window_pos_arb(self):
        self.require_extension('GL_ARB_window_pos')
        with self.allow_missing():
            glWindowPos2dARB(1, 1)
            glWindowPos2dvARB(np.zeros(2, 'd'))
            glWindowPos2fARB(1, 1)
            glWindowPos2fvARB(np.zeros(2, 'f'))
            glWindowPos2iARB(1, 1)
            glWindowPos2ivARB(np.zeros(2, 'i'))
            glWindowPos2sARB(1, 1)
            glWindowPos2svARB(np.zeros(2, 'h'))
            glWindowPos3dARB(1, 1, 0)
            glWindowPos3dvARB(np.zeros(3, 'd'))
            glWindowPos3fARB(1, 1, 0)
            glWindowPos3fvARB(np.zeros(3, 'f'))
            glWindowPos3iARB(1, 1, 0)
            glWindowPos3ivARB(np.zeros(3, 'i'))
            glWindowPos3sARB(1, 1, 0)
            glWindowPos3svARB(np.zeros(3, 'h'))
        self.check_error('window pos ARB')

    def test_window_pos_mesa(self):
        self.require_extension('GL_MESA_window_pos')
        with self.allow_missing():
            glWindowPos2dMESA(1, 1)
            glWindowPos2dvMESA(np.zeros(2, 'd'))
            glWindowPos2fMESA(1, 1)
            glWindowPos2fvMESA(np.zeros(2, 'f'))
            glWindowPos2iMESA(1, 1)
            glWindowPos2ivMESA(np.zeros(2, 'i'))
            glWindowPos2sMESA(1, 1)
            glWindowPos2svMESA(np.zeros(2, 'h'))
            glWindowPos3dMESA(1, 1, 0)
            glWindowPos3dvMESA(np.zeros(3, 'd'))
            glWindowPos3fMESA(1, 1, 0)
            glWindowPos3fvMESA(np.zeros(3, 'f'))
            glWindowPos3iMESA(1, 1, 0)
            glWindowPos3ivMESA(np.zeros(3, 'i'))
            glWindowPos3sMESA(1, 1, 0)
            glWindowPos3svMESA(np.zeros(3, 'h'))
            glWindowPos4dMESA(1, 1, 0, 1)
            glWindowPos4dvMESA(np.zeros(4, 'd'))
            glWindowPos4fMESA(1, 1, 0, 1)
            glWindowPos4fvMESA(np.zeros(4, 'f'))
            glWindowPos4iMESA(1, 1, 0, 1)
            glWindowPos4ivMESA(np.zeros(4, 'i'))
            glWindowPos4sMESA(1, 1, 0, 1)
            glWindowPos4svMESA(np.zeros(4, 'h'))
        self.check_error('window pos MESA')


class TestSecondaryColorEXT(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_secondary_color(self):
        self.require_extension('GL_EXT_secondary_color')
        with self.allow_missing():
            glSecondaryColor3bEXT(1, 2, 3)
            glSecondaryColor3bvEXT(np.zeros(3, 'b'))
            glSecondaryColor3dEXT(1, 1, 1)
            glSecondaryColor3dvEXT(np.zeros(3, 'd'))
            glSecondaryColor3fEXT(1, 1, 1)
            glSecondaryColor3fvEXT(np.zeros(3, 'f'))
            glSecondaryColor3iEXT(1, 1, 1)
            glSecondaryColor3ivEXT(np.zeros(3, 'i'))
            glSecondaryColor3sEXT(1, 1, 1)
            glSecondaryColor3svEXT(np.zeros(3, 'h'))
            glSecondaryColor3ubEXT(1, 1, 1)
            glSecondaryColor3ubvEXT(np.zeros(3, 'B'))
            glSecondaryColor3uiEXT(1, 1, 1)
            glSecondaryColor3uivEXT(np.zeros(3, 'I'))
            glSecondaryColor3usEXT(1, 1, 1)
            glSecondaryColor3usvEXT(np.zeros(3, 'H'))
            buf = one(glGenBuffers(1))
            glBindBuffer(GL_ARRAY_BUFFER, buf)
            glBufferData(GL_ARRAY_BUFFER, np.zeros(12, 'f'), GL_STATIC_DRAW)
            glSecondaryColorPointerEXT(3, GL_FLOAT, 0, None)
        self.check_error('secondary color EXT')


class TestHalfFloatNV(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_half_float(self):
        self.require_extension('GL_NV_half_float')
        # One array per width rather than slices of one: slicing a ctypes
        # array answers a list, so a run without numpy would be passing
        # lists here -- which a caller that has refused implicit copies
        # is told about rather than charged for.
        h1 = np.zeros(1, 'H')  # GLhalfNV is an unsigned short
        h2 = np.zeros(2, 'H')
        h3 = np.zeros(3, 'H')
        h = np.zeros(4, 'H')
        with self.allow_missing(), self.begin(GL_POINTS):
            glColor3hNV(0, 0, 0)
            glColor3hvNV(h3)
            glColor4hNV(0, 0, 0, 0)
            glColor4hvNV(h)
            glFogCoordhNV(0)
            glFogCoordhvNV(h1)
            glMultiTexCoord1hNV(GL_TEXTURE0, 0)
            glMultiTexCoord1hvNV(GL_TEXTURE0, h1)
            glMultiTexCoord2hNV(GL_TEXTURE0, 0, 0)
            glMultiTexCoord2hvNV(GL_TEXTURE0, h2)
            glMultiTexCoord3hNV(GL_TEXTURE0, 0, 0, 0)
            glMultiTexCoord3hvNV(GL_TEXTURE0, h3)
            glMultiTexCoord4hNV(GL_TEXTURE0, 0, 0, 0, 0)
            glMultiTexCoord4hvNV(GL_TEXTURE0, h)
            glNormal3hNV(0, 0, 0)
            glNormal3hvNV(h3)
            glSecondaryColor3hNV(0, 0, 0)
            glSecondaryColor3hvNV(h3)
            glTexCoord1hNV(0)
            glTexCoord1hvNV(h1)
            glTexCoord2hNV(0, 0)
            glTexCoord2hvNV(h2)
            glTexCoord3hNV(0, 0, 0)
            glTexCoord3hvNV(h3)
            glTexCoord4hNV(0, 0, 0, 0)
            glTexCoord4hvNV(h)
            glVertexAttrib1hNV(1, 0)
            glVertexAttrib1hvNV(1, h1)
            glVertexAttrib2hNV(1, 0, 0)
            glVertexAttrib2hvNV(1, h2)
            glVertexAttrib3hNV(1, 0, 0, 0)
            glVertexAttrib3hvNV(1, h3)
            glVertexAttrib4hNV(1, 0, 0, 0, 0)
            glVertexAttrib4hvNV(1, h)
            glVertexAttribs1hvNV(1, 1, h1)
            glVertexAttribs2hvNV(1, 1, h2)
            glVertexAttribs3hvNV(1, 1, h3)
            glVertexAttribs4hvNV(1, 1, h)
            glVertexWeighthNV(0)
            glVertexWeighthvNV(h1)
            glVertex2hNV(0, 0)
            glVertex2hvNV(h2)
            glVertex3hNV(0, 0, 0)
            glVertex3hvNV(h3)
            glVertex4hNV(0, 0, 0, 0)
            glVertex4hvNV(h)
        self.check_error('NV half float')


if __name__ == '__main__':
    unittest.main()
