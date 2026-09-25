#! /usr/bin/env python3
"""Live glGet size coverage across every desktop-GL version and extension the
driver advertises.

Data-driven from ``gl/glget_groups.json`` (generated from the Khronos registry):
for each supported core version and extension, every ``state`` pname it defines is
read with the correct getter and its returned size is checked against
``glgetsizes.csv``.  A pname that the driver does not actually serve as a global
query is skipped; a pname that *does* return data with the wrong size fails -- that
is a CSV bug to correct (then ``src/regen_glgets.py``).

Object-scoped pnames (``program`` / ``uniform_block`` / ``atomic_counter_buffer`` /
``program_interface``) need a set-up GL object and are covered by curated
per-feature tests (e.g. test_glget_compute.py); this module reports their count so
the gap is visible rather than silent.

Runs on both backends: ``TEST_WINDOWING=glfw`` (llvmpipe) and ``=egl`` (the GPU).
"""

import unittest

from gltestcase import GLTestCase
from glget_check import GLGetCheckMixin

from OpenGL.GL import *


class TestExtensionGLGets(GLGetCheckMixin, GLTestCase):
    # compatibility at a widely-available version exposes the largest pname set
    # (both drivers provide >= 4.5 compatibility).
    profile = 'compatibility'
    gl_version = (4, 5)
    glget_suite = 'gl'

    def test_supported_extension_state_pnames(self):
        checked, exts, object_scoped = self.sweep_present('extensions')
        self.assertTrue(exts, 'no advertised extensions matched the registry map')
        print('\n[glget] extensions: %d supported, %d state pnames checked, '
              '%d object-scoped pnames deferred to curated tests'
              % (exts, checked, len(object_scoped)))

    def test_core_version_state_pnames(self):
        checked, feats, object_scoped = self.sweep_present('features')
        self.assertTrue(feats, 'no core versions matched the registry map')
        print('\n[glget] core versions: %d supported, %d state pnames checked, '
              '%d object-scoped pnames deferred' % (feats, checked, len(object_scoped)))


if __name__ == '__main__':
    unittest.main()
