#! /usr/bin/env python3
"""An error about a large argument does not print the argument.

Every GL error PyOpenGL raises carries the arguments of the call that caused
it, which is most of what makes them useful. The arguments to a GL call are
routinely enormous: a vertex buffer, a texture, a mesh. Formatting one of
those into the message produces megabytes of digits, and what the caller sees
is not a diagnosis but a terminal that stops responding -- IDLE hangs
outright, and a terminal fills its scrollback with the contents of a buffer
while the actual message scrolls past.

So the size of an error message has to be bounded by something other than the
size of the data, and it has to be bounded on the way in rather than by
whatever is printing it: the cost is paid when the message is built, and
`str(error)` is called by logging, by `repr`, and by the traceback machinery
before anything decides whether to show it.

https://github.com/mcfletch/pyopengl/issues/114
"""

import time

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403

#: Big enough that formatting it would be unmistakable -- 32 MB is about 100
#: million characters as decimal digits -- and small enough to allocate
#: without making the machine swap.
BIG = 32 * 1024 * 1024

#: What a message may reasonably run to. Generous: a GL error names the
#: operation, its arguments and a description.
LONGEST_REASONABLE = 8192

#: Formatting 32 MB of digits takes tens of seconds; a bounded message is
#: instant. Loose, because this is distinguishing "instant" from "minutes".
SLOWEST_REASONABLE = 5.0


class TestAWrongCallWithALargeArgument(GLTestCase):
    profile = 'core'
    gl_version = (3, 3)

    def setUp(self):
        super().setUp()
        self.buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer)

    def raise_it(self, call):
        """Make the wrong call, and answer the message and what it cost."""
        started = time.time()
        try:
            call()
        except Exception as error:
            text = str(error)
        else:
            pytest.fail('the wrong call was accepted')
        return text, time.time() - started

    def test_a_wrong_arity_call_reports_briefly(self):
        """The ticket's own shape: `glBufferStorage` with the flags left off."""
        payload = bytes(BIG)
        text, took = self.raise_it(
            lambda: glBufferStorage(GL_ARRAY_BUFFER, payload))
        assert len(text) < LONGEST_REASONABLE, (
            '%d characters of error message for a %d-byte argument'
            % (len(text), BIG))
        assert took < SLOWEST_REASONABLE, (
            'took %.1fs to build the message' % (took,))

    @pytest.mark.skipif(not hasattr(np, 'ndarray'),
                        reason='needs numpy itself, not the ctypes shim')
    def test_a_gl_error_about_a_large_array_reports_briefly(self):
        """A GLError rather than a TypeError: the other way one is built."""
        data = np.zeros(BIG // 4, dtype='f')
        text, took = self.raise_it(
            # An invalid usage constant, so the driver refuses a call whose
            # data argument is the whole array.
            lambda: glBufferData(GL_ARRAY_BUFFER, data, 0xDEAD))
        assert len(text) < LONGEST_REASONABLE, (
            '%d characters of error message for a %d-byte array'
            % (len(text), data.nbytes))
        assert took < SLOWEST_REASONABLE, (
            'took %.1fs to build the message' % (took,))

    def test_the_message_still_says_what_went_wrong(self):
        """Bounded is not the same as empty."""
        payload = bytes(BIG)
        text, _ = self.raise_it(
            lambda: glBufferStorage(GL_ARRAY_BUFFER, payload))
        assert text.strip(), 'the message was empty'
        assert 'glBufferStorage' in text or 'argument' in text.lower(), text
