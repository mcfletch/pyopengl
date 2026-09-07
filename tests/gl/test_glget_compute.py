#! /usr/bin/env python3
"""glGet coverage for ``GL_ARB_compute_shader`` (core in GL 4.3).

Vertical slice proving the glGet size/semantics approach end to end across all
four getter families the extension touches:

* ``state``  -- the ``GL_MAX_COMPUTE_*`` limits + ``GL_DISPATCH_INDIRECT_BUFFER_BINDING``,
  read live and size-checked (including the indexed ``glGetIntegeri_v`` pnames
  ``GL_MAX_COMPUTE_WORK_GROUP_COUNT``/``_SIZE``).
* ``program`` -- ``GL_COMPUTE_WORK_GROUP_SIZE`` via ``glGetProgramiv`` on a compute
  program with a known ``local_size`` layout (the spec-defined way to make it
  return a real value).
* ``uniform_block`` -- ``GL_UNIFORM_BLOCK_REFERENCED_BY_COMPUTE_SHADER`` via
  ``glGetActiveUniformBlockiv`` on a program whose compute stage uses the block.
* ``atomic_counter_buffer`` -- ``GL_ATOMIC_COUNTER_BUFFER_REFERENCED_BY_COMPUTE_SHADER``
  via ``glGetActiveAtomicCounterBufferiv``.

The descriptor list is the generated ``gl/glget_groups.json`` for the extension, so
this stays in lock-step with the registry.  A size mismatch is a bug in
``src/glgetsizes.csv`` (run ``src/regen_glgets.py`` after fixing it).
"""

import ctypes
import unittest

from arraycompat import object_names
from gltestcase import GLTestCase
from glget_check import GLGetCheckMixin, feature_glgets

from OpenGL.arrays.arraydatatype import ArrayDatatype
from OpenGL.GL import *  # noqa: F401,F403

EXT = 'GL_ARB_compute_shader'


class TestComputeGLGet(GLGetCheckMixin, GLTestCase):
    profile = 'core'
    gl_version = (4, 3)
    glget_suite = 'gl'

    def setUp(self):
        super().setUp()
        # core in 4.3; some core-profile drivers don't list it as an extension
        # string, so accept either the extension or the core version.
        if EXT not in self.extensions() and self.version() < (4, 3):
            self.skipTest('compute shader (GL 4.3 / %s) unavailable' % EXT)

    # --- shader helpers --------------------------------------------------
    def _link_compute(self, body, decls=''):
        src = (
            '#version 430\n'
            'layout(local_size_x=8, local_size_y=4, local_size_z=2) in;\n'
            + decls + 'void main(){\n' + body + '}\n'
        )
        sh = glCreateShader(GL_COMPUTE_SHADER)
        glShaderSource(sh, src)
        glCompileShader(sh)
        if not glGetShaderiv(sh, GL_COMPILE_STATUS):
            self.fail('compute compile failed: %s' % glGetShaderInfoLog(sh))
        prog = glCreateProgram()
        glAttachShader(prog, sh)
        glLinkProgram(prog)
        if not glGetProgramiv(prog, GL_LINK_STATUS):
            self.fail('compute link failed: %s' % glGetProgramInfoLog(prog))
        self.addCleanup(glDeleteProgram, prog)
        self.addCleanup(glDeleteShader, sh)
        return prog

    # --- Layer 1: state pnames sweep -------------------------------------
    def test_state_pnames(self):
        """Read every state pname the extension defines; sizes must match."""
        seen = self.sweep_state('extensions', EXT)
        # the sweep must actually have reached the indexed work-group queries
        self.assertIn('GL_MAX_COMPUTE_WORK_GROUP_COUNT', seen)
        self.assertIn('GL_MAX_COMPUTE_WORK_GROUP_SIZE', seen)

    def test_dispatch_indirect_buffer_binding_roundtrip(self):
        """state pname with a setter: bind a buffer, read the binding back."""
        buf = int(glGenBuffers(1))
        self.addCleanup(glDeleteBuffers, 1, object_names(buf))
        glBindBuffer(GL_DISPATCH_INDIRECT_BUFFER, buf)
        got = int(glGetIntegerv(GL_DISPATCH_INDIRECT_BUFFER_BINDING))
        self.assertEqual(got, buf)

    # --- Layer 2: object-scoped, spec-driven round-trips -----------------
    def test_compute_work_group_size(self):
        """``glGetProgramiv(GL_COMPUTE_WORK_GROUP_SIZE)`` returns the 3 local sizes.

        Catches the glgetsizes.csv (1,) bug: a 1-int buffer truncates the driver's
        3 ints to a scalar (and under-allocates the output array).
        """
        prog = self._link_compute('')
        size = glGetProgramiv(prog, GL_COMPUTE_WORK_GROUP_SIZE)
        self.assertEqual(
            tuple(int(x) for x in size), (8, 4, 2),
            'GL_COMPUTE_WORK_GROUP_SIZE truncated to %r -- glgetsizes.csv size '
            'must be (3,)' % (size,),
        )
        self.assertEqual(ArrayDatatype.dimensions(size), (3,))

    def test_uniform_block_referenced_by_compute(self):
        prog = self._link_compute(
            'v = blk.value;\n',
            'layout(std140) uniform Blk { float value; } blk;\n'
            'layout(std430) buffer Out { float v; };\n',
        )
        idx = int(glGetUniformBlockIndex(prog, 'Blk'))
        self.assertNotEqual(idx, GL_INVALID_INDEX)
        # NB: glGetActiveUniformBlockiv has no PyOpenGL output wrapper, so it does
        # not consume the _glget_size_mapping entry -- the caller must pass the
        # output buffer.  (Wiring that wrapper would let the CSV size drive it.)
        out = (ctypes.c_int * 1)()
        glGetActiveUniformBlockiv(
            prog, idx, GL_UNIFORM_BLOCK_REFERENCED_BY_COMPUTE_SHADER, out
        )
        self.assertEqual(out[0], GL_TRUE)

    def test_atomic_counter_buffer_referenced_by_compute(self):
        if int(glGetIntegerv(GL_MAX_COMPUTE_ATOMIC_COUNTERS)) < 1:
            self.skipTest('no compute atomic counters')
        prog = self._link_compute(
            'atomicCounterIncrement(counter);\n',
            'layout(binding=0, offset=0) uniform atomic_uint counter;\n',
        )
        nbuf = int(glGetProgramiv(prog, GL_ACTIVE_ATOMIC_COUNTER_BUFFERS))
        self.assertGreaterEqual(nbuf, 1)
        ref = glGetActiveAtomicCounterBufferiv(
            prog, 0, GL_ATOMIC_COUNTER_BUFFER_REFERENCED_BY_COMPUTE_SHADER
        )
        self.assertEqual(int(ref), GL_TRUE)
        self.assert_dims(
            'GL_ATOMIC_COUNTER_BUFFER_REFERENCED_BY_COMPUTE_SHADER', ref, (1,)
        )

    # --- completeness: no descriptor family left unexercised -------------
    def test_all_families_covered(self):
        families = {d['family'] for d in feature_glgets('gl', 'extensions', EXT)}
        covered = {'state', 'state?', 'program', 'uniform_block',
                   'atomic_counter_buffer'}
        self.assertTrue(
            families <= covered,
            'unhandled glGet families for %s: %s' % (EXT, families - covered),
        )


if __name__ == '__main__':
    unittest.main()
