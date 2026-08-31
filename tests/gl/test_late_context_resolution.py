#! /usr/bin/env python3
"""An entry point probed before there is a context still works after there is.

Test modules import their entry points at collection time, when no context
exists yet, and anything that probes one then gets an answer that is not
trustworthy.  What must not happen is for that answer to be remembered: the
first real call, under a real context, has to resolve properly.
"""

import unittest

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.ARB.shader_objects import *  # noqa: F401,F403
from OpenGL.GL.ARB.vertex_shader import *  # noqa: F401,F403


class TestLateContextResolution(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_an_extension_probed_without_a_context_resolves_later(self):
        shader = glCreateShaderObjectARB(GL_VERTEX_SHADER_ARB)
        glShaderSourceARB(shader, ['void main(){ gl_Position = vec4(1); }'])
        glCompileShaderARB(shader)
        self.assertTrue(
            glGetObjectParameterivARB(shader, GL_OBJECT_COMPILE_STATUS_ARB)
        )
        glDeleteObjectARB(shader)

    def test_a_core_entry_point_resolves_after_a_late_context(self):
        self.assertTrue(glGetString(GL_VERSION))


if __name__ == '__main__':
    unittest.main()
