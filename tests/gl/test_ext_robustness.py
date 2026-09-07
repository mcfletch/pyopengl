#! /usr/bin/env python3
"""Robust-access query extensions: GL_ARB_robustness (+ legacy imaging getn*)
and GL_KHR_robustness.  Compatibility context so the imaging getters resolve."""

import unittest
from arraycompat import nbytes, np, one  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403
from OpenGL.GL.ARB.robustness import *  # noqa: F401,F403
from OpenGL.GL.KHR.robustness import *  # noqa: F401,F403

FS = 'uniform float uf; uniform int ui; void main(){ gl_FragColor = vec4(uf+float(ui)); }'
VS = 'void main(){ gl_Position = gl_Vertex; }'


class TestARBRobustness(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_arb_robustness(self):
        self.require_extension('GL_ARB_robustness')
        with self.allow_missing():
            glGetGraphicsResetStatusARB()
            buf = np.zeros((1, 1, 4), 'B')
            glReadnPixelsARB(0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, nbytes(buf), buf)
            prog = self.compile_program(VS, FS)
            glUseProgram(prog)
            uf = glGetUniformLocation(prog, 'uf')
            ui = glGetUniformLocation(prog, 'ui')
            glGetnUniformfvARB(prog, uf, 4, np.zeros(1, 'f'))
            glGetnUniformivARB(prog, ui, 4, np.zeros(1, 'i'))
            glGetnUniformuivARB(prog, ui, 4, np.zeros(1, 'I'))
            glGetnUniformdvARB(prog, uf, 8, np.zeros(1, 'd'))
            tex = one(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RGBA8,
                2,
                2,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                np.zeros((2, 2, 4), 'B'),
            )
            glGetnTexImageARB(
                GL_TEXTURE_2D,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                16,
                np.zeros((2, 2, 4), 'B'),
            )
            glGetnPixelMapfvARB(GL_PIXEL_MAP_R_TO_R, 4, np.zeros(4, 'f'))
            glGetnPixelMapuivARB(GL_PIXEL_MAP_R_TO_R, 4, np.zeros(4, 'I'))
            glGetnPixelMapusvARB(GL_PIXEL_MAP_R_TO_R, 4, np.zeros(4, 'H'))
            glGetnPolygonStippleARB(128, np.zeros(128, 'B'))
        self.check_error('arb robustness')
        # the ARB_imaging getters need histogram/minmax/table state set up first;
        # the calls drive the wrappers and exercise() tolerates the state GLError
        with self.exercise():
            glGetnColorTableARB(
                GL_COLOR_TABLE, GL_RGBA, GL_UNSIGNED_BYTE, 16, np.zeros(16, 'B')
            )
            glGetnConvolutionFilterARB(
                GL_CONVOLUTION_2D, GL_RGBA, GL_UNSIGNED_BYTE, 16, np.zeros(16, 'B')
            )
            glGetnSeparableFilterARB(
                GL_SEPARABLE_2D,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                16,
                np.zeros(16, 'B'),
                16,
                np.zeros(16, 'B'),
                None,
            )
            glGetnHistogramARB(
                GL_HISTOGRAM, GL_TRUE, GL_RGBA, GL_UNSIGNED_BYTE, 16, np.zeros(16, 'B')
            )
            glGetnMinmaxARB(
                GL_MINMAX, GL_TRUE, GL_RGBA, GL_UNSIGNED_BYTE, 16, np.zeros(16, 'B')
            )
            glMap1f(GL_MAP1_VERTEX_3, 0, 1, np.array([[0, 0, 0], [1, 1, 0]], 'f'))
            glGetnMapdvARB(GL_MAP1_VERTEX_3, GL_COEFF, 6, np.zeros(6, 'd'))
            glGetnMapfvARB(GL_MAP1_VERTEX_3, GL_COEFF, 6, np.zeros(6, 'f'))
            glGetnMapivARB(GL_MAP1_VERTEX_3, GL_ORDER, 1, np.zeros(1, 'i'))
            ctex = one(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D, ctex)
            glGetnCompressedTexImageARB(GL_TEXTURE_2D, 0, 16, np.zeros(16, 'B'))


class TestKHRRobustness(GLTestCase):
    profile = 'core'
    gl_version = (4, 5)

    def test_khr_robustness(self):
        self.require_extension('GL_KHR_robustness')
        with self.allow_missing():
            glGetGraphicsResetStatus()
            glGetGraphicsResetStatusKHR()
            buf = np.zeros((1, 1, 4), 'B')
            glReadnPixels(0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, nbytes(buf), buf)
            glReadnPixelsKHR(0, 0, 1, 1, GL_RGBA, GL_UNSIGNED_BYTE, nbytes(buf), buf)
            prog = self.compile_program(
                '#version 150\nin vec4 p; void main(){ gl_Position = p; }',
                '#version 150\nuniform float uf; out vec4 c; void main(){ c = vec4(uf); }',
            )
            glUseProgram(prog)
            loc = glGetUniformLocation(prog, 'uf')
            glGetnUniformfv(prog, loc, 4, np.zeros(1, 'f'))
            glGetnUniformfvKHR(prog, loc, 4, np.zeros(1, 'f'))
            glGetnUniformiv(prog, loc, 4, np.zeros(1, 'i'))
            glGetnUniformivKHR(prog, loc, 4, np.zeros(1, 'i'))
            glGetnUniformuiv(prog, loc, 4, np.zeros(1, 'I'))
            glGetnUniformuivKHR(prog, loc, 4, np.zeros(1, 'I'))
        self.check_error('khr robustness')


if __name__ == '__main__':
    unittest.main()
