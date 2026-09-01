#! /usr/bin/env python3
"""Dispatch from a thread that has not dispatched before.

A context is current per thread, and the table a thread dispatches through is
thread-local, so a thread that has never made a GL call starts with no table
at all.  It has to find the right one on its first call rather than inheriting
whatever the thread that created it was using.
"""

import threading
import unittest

import pytest

import OpenGL._dispatch as dispatch
import OpenGL.GL  # noqa: F401  -- installs the implementation under test
from OpenGL import platform

glfw = pytest.importorskip('glfw')


class TestThreadedDispatch(unittest.TestCase):
    def setUp(self):
        if not glfw.init():
            self.skipTest('no glfw')
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        self.window = glfw.create_window(64, 64, 'threaded', None, None)
        if not self.window:
            self.skipTest('could not create a context')

    def tearDown(self):
        glfw.make_context_current(None)
        glfw.destroy_window(self.window)
        # Deliberately not glfw.terminate(): see test_multi_context.

    def test_a_fresh_thread_dispatches_correctly(self):
        """The context is made current *on the worker*, as the GL requires."""
        from OpenGL.GL import GL_VERSION, glGetString

        answers = {}

        def worker():
            glfw.make_context_current(self.window)
            if dispatch.ACTIVE:
                dispatch.make_current(platform.PLATFORM.GetCurrentContext())
            try:
                answers['version'] = glGetString(GL_VERSION)
            except Exception as raised:  # noqa: BLE001 - recorded, then asserted
                answers['error'] = raised
            glfw.make_context_current(None)

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(timeout=30)

        assert 'error' not in answers, answers.get('error')
        assert answers.get('version')

    def test_the_main_thread_still_works_afterwards(self):
        from OpenGL.GL import GL_VERSION, glGetString

        self.test_a_fresh_thread_dispatches_correctly()
        glfw.make_context_current(self.window)
        if dispatch.ACTIVE:
            dispatch.make_current(platform.PLATFORM.GetCurrentContext())
        assert glGetString(GL_VERSION)

    def test_several_threads_in_turn_all_resolve(self):
        """Each takes the context in turn, as a real worker pool would."""
        from OpenGL.GL import GL_VERSION, glGetString

        results = []
        lock = threading.Lock()

        def worker(index):
            with lock:
                glfw.make_context_current(self.window)
                if dispatch.ACTIVE:
                    dispatch.make_current(platform.PLATFORM.GetCurrentContext())
                results.append((index, glGetString(GL_VERSION)))
                glfw.make_context_current(None)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        assert len(results) == 4
        assert all(version for _index, version in results)


if __name__ == '__main__':
    unittest.main()
