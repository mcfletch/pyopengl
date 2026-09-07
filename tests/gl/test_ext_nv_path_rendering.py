#! /usr/bin/env python3
"""GL_NV_path_rendering on desktop OpenGL.

The cases are :mod:`nv_path_rendering_cases`; this says which context to run
them in and which module the entry points come from.
"""

import unittest

from gltestcase import GLTestCase
from nv_path_rendering_cases import NVPathRenderingMixin
from OpenGL import GL as _api
from OpenGL.GL.NV import path_rendering as _nv


class TestNVPathRendering(NVPathRenderingMixin, GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    gl = _api
    nv = _nv


if __name__ == '__main__':
    unittest.main()
