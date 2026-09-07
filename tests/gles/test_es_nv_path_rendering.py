#! /usr/bin/env python3
"""GL_NV_path_rendering on OpenGL-ES.

The cases are :mod:`nv_path_rendering_cases`; this says which context to run
them in and which module the entry points come from.
"""

import unittest

from egltestcase import ESTestCase
from nv_path_rendering_cases import NVPathRenderingMixin
# GLES3: the immutable-storage and framebuffer calls the cases use are
# ES 3.0's, and the ES base case's own `gl` is GLES2.
from OpenGL import GLES3 as _api
from OpenGL.GLES2.NV import path_rendering as _nv


class TestESNVPathRendering(NVPathRenderingMixin, ESTestCase):
    api = 'gles'
    gl_version = (3, 2)

    gl = _api
    nv = _nv


if __name__ == '__main__':
    unittest.main()
