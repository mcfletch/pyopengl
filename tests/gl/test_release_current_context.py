#! /usr/bin/env python3
"""Letting go of the context a thread holds, whichever API made it.

**A thread may have one current GL context, and EGL and GLX do not know about
each other.**  Asking EGL to make a context current while GLX holds the thread
is ``EGL_BAD_ACCESS``; the reverse is an X ``BadAccess`` on
``X_GLXMakeCurrent`` -- which Xlib's default error handler turns into a process
*exit*, so it is not even an exception to catch.

That is not a contrived case.  A program with two GL views in it -- an engine's
test suite running on one windowing backend while a helper opens a window
through another, an application embedding a second renderer -- has both APIs in
one process, and whichever takes the thread has to be able to say that the
other should let go first.

``platform.PLATFORM.releaseCurrentContext()`` is that: it answers whether
anything was released, and is safe to call when nothing is.
"""

from gltestcase import GLTestCase

from OpenGL import platform


class TestReleasingTheCurrentContext(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_the_base_platform_declares_it(self):
        """A caller should not have to ask which platform it is on."""
        from OpenGL.platform import baseplatform

        assert callable(baseplatform.BasePlatform.releaseCurrentContext)

    def test_it_releases_what_was_current(self):
        assert platform.PLATFORM.releaseCurrentContext() is True
        try:
            assert not platform.PLATFORM.GetCurrentContext()
        finally:
            self._create_context()      # the fixture's teardown wants one

    def test_releasing_twice_is_releasing_once(self):
        assert platform.PLATFORM.releaseCurrentContext() is True
        try:
            assert platform.PLATFORM.releaseCurrentContext() is False
        finally:
            self._create_context()

    def test_the_thread_can_be_taken_again_afterwards(self):
        """Which is the whole point: the next API in gets a free thread."""
        platform.PLATFORM.releaseCurrentContext()
        self._create_context()
        assert platform.PLATFORM.GetCurrentContext()
