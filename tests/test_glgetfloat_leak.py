#!/usr/bin/python
from __future__ import print_function
import os, math, unittest
import checkutils
from basetestcase import BaseTest
from OpenGL.GL import *

try:
    import psutil
except ImportError:
    psutil = None


class TestGLGetFloatLeak(BaseTest):
    #: Calls made before the baseline, so that first-call allocation -- the
    #: entry point resolving, the array type registering, the arena growing to
    #: the size one call needs -- is not counted as growth.
    WARMUP = 2000

    #: Calls measured.  Each one returns a 4x4 array, so leaking even the array
    #: costs ~64 bytes a call and this many calls would show megabytes.
    MEASURED = 20000

    #: RSS moves in page-sized steps and the process is doing other things;
    #: this is far below what any per-call leak would reach over MEASURED calls.
    BUDGET = 1024 * 1024

    @unittest.skipUnless(psutil, "psutil not installed")
    def test_glGetFloatv_no_leak(self):
        """Repeated glGetFloatv(GL_MODELVIEW_MATRIX) must not grow the process

        Measured as resident bytes against the number of calls: what a leak
        does is grow with the call count, which a fixed budget over a large
        count detects and ordinary allocator noise does not reach.
        """
        proc = psutil.Process(os.getpid())
        for _ in range(self.WARMUP):
            assert glGetFloatv(GL_MODELVIEW_MATRIX) is not None
        before = proc.memory_info().rss
        for _ in range(self.MEASURED):
            glGetFloatv(GL_MODELVIEW_MATRIX)
        growth = proc.memory_info().rss - before
        assert growth < self.BUDGET, (
            'resident memory grew %d bytes over %d calls (%.1f bytes a call)'
            % (growth, self.MEASURED, growth / float(self.MEASURED))
        )


if __name__ == '__main__':
    checkutils.require('OpenGL_accelerate')
    checkutils.run()
