#! /usr/bin/env python3
"""ARB assembly programs: GL_ARB_vertex_program + GL_ARB_fragment_program.
Loads real ASCII program strings and exercises the env/local parameter and
program-object query entry points in a compatibility context."""

import unittest
import ctypes
from arraycompat import np, object_names, one

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.ARB.vertex_program import *  # noqa: F401,F403
from OpenGL.GL.ARB.fragment_program import *  # noqa: F401,F403

VP = b'''!!ARBvp1.0
MOV result.position, vertex.position;
END'''
FP = b'''!!ARBfp1.0
MOV result.color, {1.0, 1.0, 1.0, 1.0};
END'''


class TestARBPrograms(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def _load(self, target, source):
        pid = one(glGenProgramsARB(1))
        pid = int(pid[0]) if hasattr(pid, '__len__') else int(pid)
        glBindProgramARB(target, pid)
        glProgramStringARB(target, GL_PROGRAM_FORMAT_ASCII_ARB, len(source), source)
        self.assertEqual(
            self.getInteger(GL_PROGRAM_ERROR_POSITION_ARB),
            -1,
            glGetString(GL_PROGRAM_ERROR_STRING_ARB),
        )
        self.assertTrue(glIsProgramARB(pid))
        return pid

    def test_vertex_program(self):
        self.require_extension('GL_ARB_vertex_program')
        vp = self._load(GL_VERTEX_PROGRAM_ARB, VP)
        glEnable(GL_VERTEX_PROGRAM_ARB)
        glProgramEnvParameter4dARB(GL_VERTEX_PROGRAM_ARB, 0, 1, 2, 3, 4)
        glProgramEnvParameter4dvARB(
            GL_VERTEX_PROGRAM_ARB, 1, np.array([1, 2, 3, 4], 'd')
        )
        glProgramEnvParameter4fARB(GL_VERTEX_PROGRAM_ARB, 2, 1, 2, 3, 4)
        glProgramEnvParameter4fvARB(
            GL_VERTEX_PROGRAM_ARB, 3, np.array([1, 2, 3, 4], 'f')
        )
        glProgramLocalParameter4dARB(GL_VERTEX_PROGRAM_ARB, 0, 1, 2, 3, 4)
        glProgramLocalParameter4dvARB(
            GL_VERTEX_PROGRAM_ARB, 1, np.array([1, 2, 3, 4], 'd')
        )
        glProgramLocalParameter4fARB(GL_VERTEX_PROGRAM_ARB, 2, 1, 2, 3, 4)
        glProgramLocalParameter4fvARB(
            GL_VERTEX_PROGRAM_ARB, 3, np.array([1, 2, 3, 4], 'f')
        )
        glGetProgramEnvParameterdvARB(GL_VERTEX_PROGRAM_ARB, 0, np.zeros(4, 'd'))
        glGetProgramEnvParameterfvARB(GL_VERTEX_PROGRAM_ARB, 0, np.zeros(4, 'f'))
        glGetProgramLocalParameterdvARB(GL_VERTEX_PROGRAM_ARB, 0, np.zeros(4, 'd'))
        glGetProgramLocalParameterfvARB(GL_VERTEX_PROGRAM_ARB, 0, np.zeros(4, 'f'))
        glGetProgramivARB(
            GL_VERTEX_PROGRAM_ARB, GL_PROGRAM_LENGTH_ARB, np.zeros(1, 'i')
        )
        out = (ctypes.c_char * len(VP))()
        glGetProgramStringARB(GL_VERTEX_PROGRAM_ARB, GL_PROGRAM_STRING_ARB, out)
        glDisable(GL_VERTEX_PROGRAM_ARB)
        glDeleteProgramsARB(1, object_names(vp))
        self.check_error('ARB vertex program')

    def test_fragment_program(self):
        self.require_extension('GL_ARB_fragment_program')
        fp = self._load(GL_FRAGMENT_PROGRAM_ARB, FP)
        glEnable(GL_FRAGMENT_PROGRAM_ARB)
        glProgramEnvParameter4fARB(GL_FRAGMENT_PROGRAM_ARB, 0, 1, 1, 1, 1)
        glProgramLocalParameter4fARB(GL_FRAGMENT_PROGRAM_ARB, 0, 1, 1, 1, 1)
        glGetProgramEnvParameterfvARB(GL_FRAGMENT_PROGRAM_ARB, 0, np.zeros(4, 'f'))
        glGetProgramLocalParameterfvARB(GL_FRAGMENT_PROGRAM_ARB, 0, np.zeros(4, 'f'))
        glGetProgramivARB(
            GL_FRAGMENT_PROGRAM_ARB, GL_PROGRAM_FORMAT_ARB, np.zeros(1, 'i')
        )
        glDisable(GL_FRAGMENT_PROGRAM_ARB)
        glDeleteProgramsARB(1, object_names(fp))
        self.check_error('ARB fragment program')


if __name__ == '__main__':
    unittest.main()
