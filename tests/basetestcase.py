"""``BaseTest``: the legacy root-level suites' GL fixture.

One mechanism puts a context under a test -- :class:`glcontext.ContextTestCase`
with a backend mixin from :func:`glcontext.pick_backend` -- and this is that,
with the settings the root-level ``tests/test_*.py`` were written against: a
300x300 compatibility-profile context, and a perspective already set up on the
matrix stack.

The backend comes from :func:`glcontext.pick_backend` rather than from a
windowing library named here, so these suites run wherever any other test does:
on a headless runner, that is the EGL device platform or CGL rather than a
window.

``from basetestcase import *`` brings the GL namespace with it, which is how the
legacy modules are written.
"""

import logging
import os
import pickle

logging.basicConfig(level=logging.INFO)
HERE = os.path.dirname(__file__)

cPickle = pickle

try:
    from numpy import *
except ImportError:
    array = None

import OpenGL

if os.environ.get('TEST_NO_ACCELERATE'):
    OpenGL.USE_ACCELERATE = False
OpenGL.FORWARD_COMPATIBLE_ONLY = False
OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = True

# OpenGL.CONTEXT_CHECKING is deliberately not set here.  What an entry point
# does with no current context is decided before anything builds the entry
# points, so a module this late cannot ask the question -- and setting it
# anyway reaches calls that legitimately have no context: EGL enumerates its
# devices before there is one, and a refused enumeration reads as a machine
# with no devices on it.  tests/gl/test_no_context_calls.py settles the
# question in a subprocess instead.

from glcontext import pick_backend
from glcontext_desktop import DesktopGLTestCaseBase

from OpenGL.extensions import alternate
from OpenGL.GL import *
from OpenGL.GL.ARB.imaging import *
from OpenGL.GL.EXT.multi_draw_arrays import *
from OpenGL.GL.framebufferobjects import *
from OpenGL.GLU import *

glMultiDrawElements = alternate(
    glMultiDrawElementsEXT, glMultiDrawElements,
)


class BaseTest(pick_backend(), DesktopGLTestCaseBase):
    """A 300x300 compatibility context with a perspective already set up.

    The projection and the eye point are part of the fixture because the
    reference values in these suites were measured through them.
    """

    width = height = 300

    #: setUp puts a perspective on the matrix stack with gluPerspective and
    #: gluLookAt, so these cases need the library like any other GLU one.
    needs_glu = True

    def setUp(self):
        super().setUp()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, float(self.width) / self.height, 1.0, 20.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            -2, 0, 3,    # eyepoint
            0, 0, 0,     # center-of-view
            0, 1, 0,     # up-vector
        )
        glClearColor(0, 0, .25, 0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def flip(self):
        """Present what was drawn, for a run somebody is watching."""
        glFlush()
        self._swap()
