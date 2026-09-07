#! /usr/bin/env python3
"""GL 1.0 (compatibility): display lists, selection, feedback, accumulation."""

import unittest
from arraycompat import np, object_names, one

from arraycompat import copy_safe
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


class TestGL1Lists(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)
    accum_size = 16

    def test_display_lists(self):
        base = glGenLists(2)
        self.assertTrue(base)
        glNewList(base, GL_COMPILE)
        glColor3f(1.0, 0.0, 0.0)
        glEndList()
        self.assertTrue(glIsList(base))
        glCallList(base)
        glListBase(base)
        glCallLists(1, GL_UNSIGNED_BYTE, np.array([0], 'B'))
        glDeleteLists(base, 2)
        self.check_error('display lists')

    def test_selection_feedback(self):
        glSelectBuffer(64, np.zeros(64, 'I'))
        glRenderMode(GL_SELECT)
        glInitNames()
        glPushName(1)
        glLoadName(2)
        glPopName()
        glRenderMode(GL_RENDER)
        feedback = np.zeros(64, 'f')
        glFeedbackBuffer(64, GL_2D, feedback)
        glRenderMode(GL_FEEDBACK)
        glPassThrough(1.0)
        glRenderMode(GL_RENDER)
        self.check_error('selection/feedback')

    def test_accumulation(self):
        if self.getInteger(GL_ACCUM_RED_BITS) < 1:
            self.skipTest('no accumulation buffer available')
        glClear(GL_ACCUM_BUFFER_BIT)
        glAccum(GL_ACCUM, 1.0)
        glAccum(GL_RETURN, 1.0)
        self.check_error('accumulation')


class TestCallingAListOfLists(GLTestCase):
    """SF#2829309: ``glCallLists`` executed its argument twice.

    The list is given as a sequence of names, and a wrapper that both passed
    the count *and* iterated would run each one again.  What that looks like
    from outside is a name stack one deeper than it should be, and a selection
    buffer with a record that should not be there -- so the count is what is
    asserted, in GL_SELECT where the name stack is observable.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_a_one_element_list_runs_its_list_once(self):
        glRenderMode(GL_RENDER)
        # The point the list draws has to fall inside the viewing volume or
        # GL_SELECT produces no record at all and the count below is trivially
        # met.  Orthographic and set by hand, so the case needs no GLU.
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, 1, 10)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, 0, -3)

        first = glGenLists(2)
        second = first + 1
        self.defer_cleanup(lambda: glDeleteLists(first, 2))

        # `first` initialises the name stack and then calls `second` through
        # glCallLists; `second` pushes exactly one name.
        glNewList(first, GL_COMPILE_AND_EXECUTE)
        glInitNames()
        glCallLists(copy_safe([second], 'I'))
        glEndList()

        glNewList(second, GL_COMPILE)
        glPushName(1)
        glBegin(GL_POINTS)
        glVertex3f(0, 0, 0)
        glEnd()
        glEndList()

        glCallList(second)
        glPopName()
        self.assertEqual(
            one(glGetIntegerv(GL_NAME_STACK_DEPTH)), 0,
            'the name stack is not empty before the selection pass',
        )

        glSelectBuffer(100)
        glRenderMode(GL_SELECT)
        glCallList(first)
        depth = one(glGetIntegerv(GL_NAME_STACK_DEPTH))
        glPopName()
        records = glRenderMode(GL_RENDER)

        self.assertEqual(depth, 1, 'the single name was pushed %d times' % (depth,))
        self.assertEqual(len(records), 1, records)


if __name__ == '__main__':
    unittest.main()
