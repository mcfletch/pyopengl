#! /usr/bin/env python3
"""An extension entry point first called inside a ``glBegin`` block.

Immediate-mode extension commands -- ``glColor3hNV``, ``glPrimitiveRestartNV``,
``glMultiTexCoord2fARB`` -- may only be called between ``glBegin`` and
``glEnd``, so the first call to one, the call that resolves it, is necessarily
made inside a block.  Resolution normally reads the context's extension string
first, and no GL query is legal in a block: the query answers "no extensions",
the command the driver does have is reported undefined, and the failed query
leaves GL_INVALID_OPERATION recorded for ``glEnd`` to raise.

The gate therefore stands aside inside a block and the entry-point address
decides -- see ``OpenGL._dispatch.support._extension_gate_passes``.
"""

import unittest

from gltestcase import GLTestCase
from OpenGL import error, platform
from OpenGL._dispatch import support
from OpenGL.GL import *  # noqa: F401,F403

#: An extension no driver has, for asking what the gate does with one.
ABSENT = 'GL_NOT_AN_EXTENSION_ANY_DRIVER_HAS'

#: An immediate-mode extension command: legal only inside a Begin/End block,
#: and declared by an extension rather than a core version, so resolving it is
#: what puts the extension gate in the way.
EXTENSION = 'GL_NV_half_float'


class TestTheGate(GLTestCase):
    """What the gate decides, asked directly."""

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_it_refuses_an_absent_extension_outside_a_block(self):
        assert not error.inside_begin_block()
        assert not support._extension_gate_passes(platform.PLATFORM, ABSENT, '')

    def test_it_stands_aside_inside_a_block(self):
        with self.begin(GL_POINTS):
            assert error.inside_begin_block()
            assert support._extension_gate_passes(platform.PLATFORM, ABSENT, '')

    def test_standing_aside_lasts_only_as_long_as_the_block(self):
        with self.begin(GL_POINTS):
            pass
        assert not error.inside_begin_block()
        assert not support._extension_gate_passes(platform.PLATFORM, ABSENT, '')


class TestResolvingInsideABlock(GLTestCase):
    """The behaviour that decision buys, against a real entry point."""

    profile = 'compatibility'
    gl_version = (2, 1)

    def setUp(self):
        super().setUp()
        self.require_extension(EXTENSION)
        from OpenGL.GL.NV import half_float

        self.entry_point = half_float.glColor3hNV

    def assert_unresolved(self):
        """Report what this run actually exercised.

        Every case gets a fresh context and the compiled layer's table is per
        context, so the entry point starts unresolved there.  The ctypes
        implementation holds one binding for the process, so a case running
        after the first has nothing left to resolve -- which is worth saying
        rather than passing quietly as though it had.
        """
        from OpenGL import _dispatch

        if _dispatch.ACTIVE and _dispatch._c.slot_address(self.entry_point):
            self.skipTest('already resolved in this process')

    def test_it_resolves_rather_than_reporting_itself_undefined(self):
        self.assert_unresolved()
        with self.begin(GL_POINTS):
            self.entry_point(0, 0, 0)

    def test_the_block_is_left_without_a_recorded_error(self):
        """The failed extension query used to surface as an error at glEnd."""
        self.assert_unresolved()
        with self.begin(GL_POINTS):
            self.entry_point(0, 0, 0)
        self.check_error('resolving inside a glBegin block')


if __name__ == '__main__':
    unittest.main()
