#! /usr/bin/env python3
"""No pname in the shipped table may be smaller than what the driver writes.

``glGetFloatv(pname)`` allocates the output array from
``OpenGL.raw.GL._glgets._glget_size_mapping``.  A pname recorded smaller than
the number of values the driver returns is a heap overflow in every program
that makes the call -- silent, because the bytes past the end usually belong to
another live allocation and the damage surfaces somewhere else entirely.

The audit in ``tests/glget_audit.py`` walks the pnames named in
``glget_groups.json``, which is the state the registry groups; this walks the
shipped table itself, so a pname no group lists is still covered.

Only under-allocation fails here.  Recording more than the driver writes wastes
a few bytes and is the audit's business, not a memory-safety question.
"""

import ctypes

from gltestcase import GLTestCase

from OpenGL import error
from OpenGL.raw.GL import _glgets
from OpenGL.raw.GL.VERSION.GL_1_0 import glGetFloatv as rawGetFloatv

#: Long enough that anything the driver writes fits, so the probe itself never
#: overflows however wrong the recorded size is.
PROBE_LEN = 4096

#: Two values, so a slot the driver happens to set to the sentinel is not read
#: as untouched.  Rounded through float32 so an untouched slot compares equal.
SENTINELS = (20345.223938, -98765.4321)


def _declared_count(dimensions):
    """Element count for a recorded shape, or None if it is looked up live."""
    if not isinstance(dimensions, tuple):
        dimensions = (dimensions,)
    count = 1
    for dimension in dimensions:
        try:
            count *= int(dimension)
        except (TypeError, ValueError):
            return None  # a size read from another query, not a fixed claim
    return count


class TestGLGetSizes(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def _drain(self):
        for _ in range(16):
            if self.gl.glGetError() == 0:
                return

    def _written(self, pname):
        """Values the driver writes for this pname, or None if it rejects it."""
        counts = []
        for sentinel in SENTINELS:
            filler = ctypes.c_float(sentinel).value
            buffer = (ctypes.c_float * PROBE_LEN)(*([filler] * PROBE_LEN))
            try:
                rawGetFloatv(pname, buffer)
            except error.GLError:
                self._drain()
                return None
            self._drain()
            untouched = bytes(ctypes.c_float(filler))
            raw = bytes(buffer)
            written = 0
            for index in range(PROBE_LEN):
                if raw[index * 4 : index * 4 + 4] != untouched:
                    written = index + 1
            counts.append(written)
        if counts[0] != counts[1]:
            return None  # a live-changing value; not a size measurement
        return counts[0]

    def test_no_pname_is_recorded_short(self):
        short = []
        for pname, dimensions in sorted(_glgets._glget_size_mapping.items()):
            declared = _declared_count(dimensions)
            if declared is None:
                continue
            written = self._written(pname)
            if written is None or written == 0:
                continue
            if written > declared:
                short.append((pname, declared, written))
        assert not short, 'recorded size smaller than the driver writes: ' + ', '.join(
            '0x%04X recorded %d, driver writes %d' % entry for entry in short
        )
