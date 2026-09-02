#! /usr/bin/env python3
"""A ``glBegin`` block that is never closed must not silence the next context.

``glGetError`` between ``glBegin`` and ``glEnd`` is itself an invalid
operation, so error checking is suspended for the block and ``glEnd`` turns it
back on.  When an exception escapes the block -- a ``TypeError`` from a bad
vertex, an entry point the driver does not export -- ``glEnd`` never runs, and
the switch stays off.

A Begin/End block belongs to one context, so a context change ends it: the
notifications an application already makes when it switches or destroys a
context are what turn checking back on.  Within a single context ``glEnd`` is
still the only thing that closes a block, which is why the exception-safe form
is ``glBegin(...)`` followed by ``try: ... finally: glEnd()``.
"""

import unittest

import pytest

import OpenGL._dispatch as dispatch
from OpenGL import _configflags, error, platform

# Importing the API installs the dispatch implementation, and these cases ask
# which one is in use.
import OpenGL.GL  # noqa: F401
from OpenGL.GL import GL_NO_ERROR, GL_POINTS, glBegin, glEnable, glEnd, glGetError

glfw = pytest.importorskip('glfw')

pytestmark = pytest.mark.skipif(
    not _configflags.ERROR_CHECKING,
    reason='PYOPENGL_ERROR_CHECKING=0 leaves glBegin the raw entry point',
)

#: An enum no driver defines, so enabling it is always GL_INVALID_ENUM.
NOT_AN_ENUM = 0xDEAD


def suspension_flags():
    """The switch each implementation in play keeps, by name.

    ``glBegin`` throws both -- the error checker's and, where the compiled
    layer is dispatching, its thread-local one -- so a case asserting the
    block is suspended has to see both, and one asserting it is over has to
    see neither.  Read from the switches because the only way to observe
    suspension through GL is a call that is illegal inside a block.
    """
    from OpenGL.raw.GL import _errors

    flags = {}
    checker = _errors._error_checker
    if checker is not None:
        flags['checker'] = bool(checker.suspended)
    if dispatch.ACTIVE:
        flags['c'] = bool(dispatch._c.error_checking_suspended())
    return flags


class TestAnAbandonedBeginBlock(unittest.TestCase):
    def setUp(self):
        if not glfw.init():
            self.skipTest('no glfw')
        glfw.default_window_hints()
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        self.windows = []

    def tearDown(self):
        for window in self.windows:
            glfw.make_context_current(window)
            handle = platform.PLATFORM.GetCurrentContext()
            if handle:
                dispatch.forget_context(handle)
            glfw.destroy_window(window)
        glfw.make_context_current(None)
        # Deliberately not glfw.terminate(): the library is initialised once
        # for the whole run and shared with every other test.

    def _window(self):
        """A compatibility context, since Begin/End only exists in one."""
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_ANY_PROFILE)
        window = glfw.create_window(64, 64, 'begin-block', None, None)
        if not window:
            self.skipTest('could not create a 2.1 context')
        self.windows.append(window)
        return window

    def _become(self, window):
        glfw.make_context_current(window)
        handle = platform.PLATFORM.GetCurrentContext()
        dispatch.make_current(handle)
        return handle

    def _checking_is_live(self):
        """Whether an invalid call still raises, drained of error state."""
        while glGetError() != GL_NO_ERROR:
            pass
        try:
            glEnable(NOT_AN_ENUM)
        except error.GLError:
            return True
        while glGetError() != GL_NO_ERROR:
            pass
        return False

    def test_checking_is_suspended_inside_the_block(self):
        """The premise: what the recovery cases are recovering from.

        Also what stops "recovery" being implemented by never suspending at
        all, which would trade a silenced checker for a GL error on every
        vertex.
        """
        self._become(self._window())
        assert not any(suspension_flags().values())
        glBegin(GL_POINTS)
        try:
            assert all(suspension_flags().values()), suspension_flags()
        finally:
            glEnd()

    def test_glend_turns_checking_back_on(self):
        self._become(self._window())
        glBegin(GL_POINTS)
        glEnd()
        assert not any(suspension_flags().values())
        assert self._checking_is_live()

    def test_making_another_context_current_ends_an_abandoned_block(self):
        self._become(self._window())
        glBegin(GL_POINTS)  # abandoned: what an exception in the block leaves

        self._become(self._window())
        assert self._checking_is_live(), (
            'a context created after an abandoned glBegin block inherited its '
            'suspended error checking'
        )

    def test_forgetting_the_context_ends_an_abandoned_block(self):
        """The shape a test suite has: tear the context down, build the next.

        Nothing calls ``make_current`` here -- the teardown reports the context
        is gone and the toolkit makes the next one current by itself.
        """
        window = self._window()
        handle = self._become(window)
        glBegin(GL_POINTS)

        dispatch.forget_context(handle)
        glfw.destroy_window(window)
        self.windows.remove(window)

        glfw.make_context_current(self._window())
        assert self._checking_is_live(), (
            'error checking stayed suspended after the context holding the '
            'abandoned block was destroyed'
        )


if __name__ == '__main__':
    unittest.main()
