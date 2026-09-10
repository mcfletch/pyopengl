#! /usr/bin/env python3
"""Repeating a call must not grow the process.

Two calls a program makes in a loop, measured against the number of times they
are made.  What a leak does is grow with the call count, which a fixed budget
over a large count detects and ordinary allocator noise does not reach:
resident memory moves in page- and arena-sized steps, so a tight threshold over
a few iterations reports a one-time allocation as a leak and a generous
threshold over many iterations does not.

Marked ``resources``: this is a measurement of the machine as much as of the
library, so it is deselectable with ``-m "not resources"`` on one that is busy.
"""

import gc
import os
import unittest
from platform import python_implementation

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL import arrays
from OpenGL.arrays import vbo
from OpenGL.arrays.arraydatatype import ArrayDatatype
from OpenGL.GL import *  # noqa: F401,F403

psutil = pytest.importorskip('psutil', reason='psutil measures the resident set')

pytestmark = pytest.mark.resources


def resident_bytes():
    return psutil.Process(os.getpid()).memory_info().rss


class TestGettingAMatrixBack(GLTestCase):
    """``glGetFloatv(GL_MODELVIEW_MATRIX)`` builds a 4x4 array per call."""

    profile = 'compatibility'
    gl_version = (2, 1)

    #: Calls made before the baseline, so that first-call allocation -- the
    #: entry point resolving, the array type registering, the arena growing to
    #: the size one call needs -- is not counted as growth.
    WARMUP = 2000

    #: Calls in a round.  Each one returns a 4x4 array, so leaking even the
    #: array costs ~64 bytes a call and a round would show megabytes.
    MEASURED = 20000

    #: Rounds of that many calls.  What is asserted is the *smallest* round's
    #: growth, because a leak grows every round by the same amount while an
    #: allocator growing an arena does it now and then: one round's worth of a
    #: per-call leak is above the budget by itself, so a leak leaves no round
    #: under it.  CPython frees each array as the call returns and every round
    #: is flat; PyPy has no refcount and reaches steady state over the first
    #: few, which is the same reason the VBO case below warms up longer there.
    ROUNDS = 6

    #: Resident memory moves in page-sized steps and the process is doing other
    #: things; this is far below what any per-call leak would reach over
    #: MEASURED calls.
    BUDGET = 1024 * 1024

    def test_the_returned_array_is_not_kept(self):
        for _ in range(self.WARMUP):
            assert glGetFloatv(GL_MODELVIEW_MATRIX) is not None
        rounds = []
        for _ in range(self.ROUNDS):
            gc.collect()
            before = resident_bytes()
            for _ in range(self.MEASURED):
                glGetFloatv(GL_MODELVIEW_MATRIX)
            gc.collect()
            rounds.append(resident_bytes() - before)
        growth = min(rounds)
        self.assertLess(
            growth, self.BUDGET,
            'resident memory grew in every round of %d calls, the smallest by '
            '%d bytes (%.1f bytes a call)\nrounds: %s'
            % (self.MEASURED, growth, growth / float(self.MEASURED), rounds),
        )


class TestTransferringAVBO(GLTestCase):
    """SF#2980896: binding a VBO used to re-transfer and lose the whole buffer.

    The original leak lost the data buffer on *every* bind, so a regression
    grows the resident set on every iteration.  That sustained per-iteration
    growth is what is counted, rather than each iteration against one baseline:
    a single multi-KB step is what a driver buffer pool, a malloc arena or a
    module imported elsewhere in the run looks like, and a tight byte threshold
    reports one of those as a leak.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_a_bound_and_deleted_vbo_gives_its_memory_back(self):
        pytest.importorskip('numpy', reason='VBO transfer is measured on a numpy array')
        data = arrays.GLfloatArray.zeros((1000,))
        chunk = ArrayDatatype.arrayByteCount(data)  # bytes transferred per bind

        # PyPy reaches steady state later (the JIT compiles this loop over the
        # first several iterations) and its incremental GC releases arenas
        # lazily, so its resident set steps up more often without any leak.
        # A real leak still grows on nearly every iteration, far above either
        # tolerance.
        # `platform` itself is not usable here: `from OpenGL.GL import *`
        # binds the name to OpenGL.platform.
        is_pypy = python_implementation() == 'PyPy'
        warmup, iterations = (10, 30) if is_pypy else (5, 25)
        tolerance = 8 if is_pypy else 3

        samples = []
        for _ in range(iterations):
            buffer = vbo.VBO(data)
            with buffer:
                pass  # the transfer is what binding does
            buffer.delete()
            del buffer
            gc.collect()
            glFinish()
            samples.append(resident_bytes())

        tail = samples[warmup:]
        grew = sum(1 for a, b in zip(tail, tail[1:]) if b - a >= chunk)
        self.assertLessEqual(
            grew, tolerance,
            'the transfer appears to leak: %d of %d post-warm-up iterations '
            'grew by >=%d bytes\nresident samples: %s'
            % (grew, len(tail) - 1, chunk, samples),
        )


if __name__ == '__main__':
    unittest.main()
