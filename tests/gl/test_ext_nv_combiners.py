#! /usr/bin/env python3
"""Legacy NVIDIA register-combiner extensions (the pre-shader programmable
texture-combiner pipeline): GL_NV_register_combiners and _combiners2.

Functional tests -- configure a real general + final combiner stage and read the
state back, with a clean error state.
"""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase

from OpenGL.GL import *
from OpenGL.GL.NV.register_combiners import *


class TestNVCombiners(GLTestCase):
    profile = 'compatibility'
    gl_version = (4, 5)

    def test_nv_register_combiners(self):
        self.require_extension('GL_NV_register_combiners')
        glEnable(GL_REGISTER_COMBINERS_NV)
        glCombinerParameteriNV(GL_NUM_GENERAL_COMBINERS_NV, 1)
        glCombinerParameterfNV(GL_NUM_GENERAL_COMBINERS_NV, 1.0)
        glCombinerParameterfvNV(GL_CONSTANT_COLOR0_NV, np.array([0.5, 0.5, 0.5, 1.0], 'f'))
        glCombinerParameterivNV(GL_COLOR_SUM_CLAMP_NV, np.array([GL_TRUE], 'i'))

        glCombinerInputNV(GL_COMBINER0_NV, GL_RGB, GL_VARIABLE_A_NV,
                          GL_PRIMARY_COLOR_NV, GL_UNSIGNED_IDENTITY_NV, GL_RGB)
        glCombinerOutputNV(GL_COMBINER0_NV, GL_RGB, GL_SPARE0_NV, GL_DISCARD_NV,
                           GL_DISCARD_NV, GL_NONE, GL_NONE, GL_FALSE, GL_FALSE, GL_FALSE)
        glFinalCombinerInputNV(GL_VARIABLE_A_NV, GL_SPARE0_NV,
                               GL_UNSIGNED_IDENTITY_NV, GL_RGB)

        glGetCombinerInputParameterfvNV(GL_COMBINER0_NV, GL_RGB, GL_VARIABLE_A_NV,
                                        GL_COMBINER_INPUT_NV, np.zeros(4, 'f'))
        glGetCombinerInputParameterivNV(GL_COMBINER0_NV, GL_RGB, GL_VARIABLE_A_NV,
                                        GL_COMBINER_INPUT_NV, np.zeros(4, 'i'))
        glGetCombinerOutputParameterfvNV(GL_COMBINER0_NV, GL_RGB,
                                         GL_COMBINER_AB_OUTPUT_NV, np.zeros(4, 'f'))
        glGetCombinerOutputParameterivNV(GL_COMBINER0_NV, GL_RGB,
                                         GL_COMBINER_AB_OUTPUT_NV, np.zeros(4, 'i'))
        glGetFinalCombinerInputParameterfvNV(GL_VARIABLE_A_NV, GL_COMBINER_INPUT_NV,
                                             np.zeros(4, 'f'))
        glGetFinalCombinerInputParameterivNV(GL_VARIABLE_A_NV, GL_COMBINER_INPUT_NV,
                                             np.zeros(4, 'i'))
        glDisable(GL_REGISTER_COMBINERS_NV)
        self.check_error('nv register combiners')

    def test_nv_register_combiners2(self):
        self.require_extension('GL_NV_register_combiners2')
        from OpenGL.GL.NV.register_combiners2 import (
            glCombinerStageParameterfvNV, glGetCombinerStageParameterfvNV,
            GL_PER_STAGE_CONSTANTS_NV,
        )

        glEnable(GL_REGISTER_COMBINERS_NV)
        glCombinerParameteriNV(GL_NUM_GENERAL_COMBINERS_NV, 1)
        glCombinerStageParameterfvNV(GL_COMBINER0_NV, GL_CONSTANT_COLOR0_NV,
                                     np.array([0.5, 0.5, 0.5, 1.0], 'f'))
        glGetCombinerStageParameterfvNV(GL_COMBINER0_NV, GL_CONSTANT_COLOR0_NV,
                                        np.zeros(4, 'f'))
        glDisable(GL_REGISTER_COMBINERS_NV)
        self.check_error('nv register combiners2')


if __name__ == '__main__':
    unittest.main()
