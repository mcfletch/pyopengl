#! /usr/bin/env python3
"""Dispatch from a thread that has not dispatched before.

A context is current per thread, and the table a thread dispatches through is
thread-local, so a thread that has never made a GL call starts with no table
at all.  It has to find the right one on its first call rather than inheriting
whatever the thread that created it was using.

**The workers are daemons, and the joins below are bounded**, because taking a
context is a call that can fail to return: ``glfwMakeContextCurrent`` blocks
where the driver will not hand the context over, and a worker stuck in it never
finishes.  A bounded join then reports the failure -- which is what a test
should do -- but a *non-daemon* thread still holds the interpreter open at
exit, and ``threading._shutdown`` waits on it with no timeout at all.  The run
then hangs after the summary has been printed, which reads as a hung suite
rather than as three failing cases.
"""

import threading
import unittest

import OpenGL._dispatch as dispatch
import OpenGL.GL  # noqa: F401  -- installs the implementation under test
from OpenGL import platform
from glcontext import Context


class TestThreadedDispatch(unittest.TestCase):
    def setUp(self):
        self.context = Context()
        # A context is current on the thread that made it, and a thread cannot
        # take one another thread holds -- so this one lets go before handing
        # it to a worker, which is what an application with a render thread
        # does too.
        self._let_go()

    def tearDown(self):
        self.context.release()

    def _take(self):
        """Take the context on this thread, and say so."""
        self.context.make_current()
        if dispatch.ACTIVE:
            dispatch.make_current(platform.PLATFORM.GetCurrentContext())

    def _let_go(self):
        """Give the thread back, so the next one may take it."""
        platform.PLATFORM.releaseCurrentContext()

    def test_a_fresh_thread_dispatches_correctly(self):
        """The context is made current *on the worker*, as the GL requires."""
        from OpenGL.GL import GL_VERSION, glGetString

        answers = {}

        def worker():
            self._take()
            try:
                answers['version'] = glGetString(GL_VERSION)
            except Exception as raised:  # noqa: BLE001 - recorded, then asserted
                answers['error'] = raised
            self._let_go()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout=30)

        assert 'error' not in answers, answers.get('error')
        assert answers.get('version')

    def test_the_main_thread_still_works_afterwards(self):
        from OpenGL.GL import GL_VERSION, glGetString

        self.test_a_fresh_thread_dispatches_correctly()
        self._take()
        assert glGetString(GL_VERSION)

    def test_several_threads_in_turn_all_resolve(self):
        """Each takes the context in turn, as a real worker pool would."""
        from OpenGL.GL import GL_VERSION, glGetString

        results = []
        lock = threading.Lock()

        def worker(index):
            with lock:
                self._take()
                results.append((index, glGetString(GL_VERSION)))
                self._let_go()

        threads = [threading.Thread(target=worker, args=(i,), daemon=True)
                   for i in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        assert len(results) == 4
        assert all(version for _index, version in results)


if __name__ == '__main__':
    unittest.main()
