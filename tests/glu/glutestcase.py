#! /usr/bin/env python3
"""Reusable base TestCase for GLU (OpenGL Utility library) tests.

GLU rides on a desktop compatibility-profile GL context: gluProject and friends
read the fixed-function ``GL_MODELVIEW_MATRIX`` / ``GL_PROJECTION_MATRIX``, and
quadrics / tessellation / NURBS emit immediate-mode geometry.  A test therefore
gets a current, cleared compatibility context plus GLU-specific conveniences
(quadric/tess/nurbs factories with cleanup, a default projection helper).

The implementation now lives in the shared :mod:`glcontext` framework:
:class:`glcontext_desktop.GLUTestCaseBase` supplies the GL+GLU API and helpers,
while the windowing backend (glfw or pygame) is chosen by
:func:`glcontext.pick_backend` from the ``TEST_WINDOWING`` environment variable.

    from glutestcase import GLUTestCase

    class TestThing(GLUTestCase):
        def test_it(self):
            q = self.quadric()
            ...
"""

from __future__ import print_function

import unittest

from glcontext import pick_backend
from glcontext_desktop import GLUTestCaseBase


def requireEntryPoint(entry_point, name=None):
    """Skip unless this system's GLU supplies ``entry_point``.

    GLU is whatever the operating system ships, and the versions differ.  The
    glu32.dll on Windows reports GLU 1.2 and has none of the 1.3 additions --
    the mipmap-level builders, gluBuild3DMipmaps, gluUnProject4,
    gluNurbsCallbackData, gluCheckExtension -- so those arrive as null
    functions there and the test has nothing to exercise.
    """
    if not entry_point:
        raise unittest.SkipTest(
            '%s is not in this system\'s GLU (GLU 1.3 entry point)'
            % (name or getattr(entry_point, '__name__', entry_point),)
        )

#: backwards-compatible alias for the toolkit-agnostic API base.
BaseGLUTestCase = GLUTestCaseBase


class GLUTestCase(pick_backend(), GLUTestCaseBase):
    """GLU test case backed by the selected windowing toolkit."""
