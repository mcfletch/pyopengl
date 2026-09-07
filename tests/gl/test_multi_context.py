#! /usr/bin/env python3
"""N contexts in one process, each holding its own entry points.

Under the ctypes implementation an entry point is resolved once and the
address is kept for the process, so whichever context resolved it first
determines the binding for every other.  Where two contexts differ -- a core
context beside a compatibility one, a discrete GPU beside a software renderer,
GLES beside desktop GL -- that is wrong.  These cases assert that the C
implementation keeps them apart.
"""

import unittest

import pytest

import OpenGL._dispatch as dispatch
from OpenGL import platform

# Importing the API is what installs the dispatch implementation, since it is
# the first thing to build an entry point.  These cases ask which one is in
# use, so the import has to have happened first.
import OpenGL.GL  # noqa: F401
from glcontext import Context

pytestmark = pytest.mark.skipif(
    not dispatch.AVAILABLE, reason='the C dispatch extension is not built'
)


class TestMultipleContexts(unittest.TestCase):
    def setUp(self):
        if not dispatch.ACTIVE:
            self.skipTest('PYOPENGL_DISPATCH=c selects the implementation under test')
        self.contexts = []

    def tearDown(self):
        # Context.release() forgets each table as its context goes, which is
        # what these cases are counting.
        for context in self.contexts:
            context.release()

    def _context(self, major, minor, core=False):
        made = Context(
            gl_version=(major, minor),
            profile='core' if core else 'compatibility',
        )
        self.contexts.append(made)
        return made

    def _become(self, context):
        context.make_current()
        handle = platform.PLATFORM.GetCurrentContext()
        dispatch.make_current(handle)
        return handle

    def test_two_contexts_hold_two_tables(self):
        first = self._context(3, 3, core=True)
        second = self._context(2, 1)
        from OpenGL._dispatch import _c as extension
        from OpenGL.GL import GL_VERSION, glGetString

        a = self._become(first)
        glGetString(GL_VERSION)
        b = self._become(second)
        glGetString(GL_VERSION)

        assert a != b
        assert extension.context_count() >= 2

    def test_an_entry_point_resolved_in_one_context_is_unresolved_in_the_other(self):
        """The table is per context, so resolution does not carry across."""
        from OpenGL._dispatch import _c as extension
        from OpenGL.GL import glBindTexture

        first = self._context(3, 3, core=True)
        second = self._context(3, 3, core=True)

        self._become(first)
        glBindTexture(0x0DE1, 0)
        resolved = extension.slot_address(glBindTexture)
        assert resolved != 0

        self._become(second)
        assert extension.slot_address(glBindTexture) == 0

        glBindTexture(0x0DE1, 0)
        assert extension.slot_address(glBindTexture) != 0

    def test_a_binding_hoisted_into_a_local_follows_the_context(self):
        """The common tight-loop idiom must survive a context switch.

        The entry point object holds a slot index rather than an address, so
        a reference captured before the switch dispatches through the new
        context's table after it.
        """
        from OpenGL.GL import GL_VERSION, glGetString

        first = self._context(3, 3, core=True)
        second = self._context(2, 1)

        self._become(first)
        hoisted = glGetString
        core_version = hoisted(GL_VERSION)

        self._become(second)
        compat_version = hoisted(GL_VERSION)

        assert core_version and compat_version

    def test_forgetting_a_context_frees_its_table(self):
        from OpenGL._dispatch import _c as extension
        from OpenGL.GL import GL_VERSION, glGetString

        window = self._context(3, 3, core=True)
        handle = self._become(window)
        glGetString(GL_VERSION)
        before = extension.context_count()

        dispatch.forget_context(handle)
        assert extension.context_count() == before - 1


if __name__ == '__main__':
    unittest.main()
