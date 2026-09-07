#! /usr/bin/env python3
"""GL 1.2 / 1.3 (compatibility): 3D textures, multitexture, compressed, transpose."""

import unittest
from arraycompat import np, object_names

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


class TestGL12_13(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_gl12_3d_textures(self):
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_3D, tex)
        glTexImage3D(
            GL_TEXTURE_3D,
            0,
            GL_RGBA,
            2,
            2,
            2,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            np.zeros((2, 2, 2, 4), 'B'),
        )
        glTexSubImage3D(
            GL_TEXTURE_3D,
            0,
            0,
            0,
            0,
            2,
            2,
            2,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            np.zeros((2, 2, 2, 4), 'B'),
        )
        glCopyTexSubImage3D(GL_TEXTURE_3D, 0, 0, 0, 0, 0, 0, 2, 2)
        glDrawRangeElements(GL_POINTS, 0, 0, 1, GL_UNSIGNED_INT, np.array([0], 'I'))
        self.check_error('gl1.2 3d textures')

    def test_gl13_multitexture(self):
        t = GL_TEXTURE0
        glActiveTexture(GL_TEXTURE1)
        glClientActiveTexture(GL_TEXTURE1)
        glActiveTexture(t)
        glBegin(GL_POINTS)
        glMultiTexCoord1d(t, 0.0)
        glMultiTexCoord1f(t, 0.0)
        glMultiTexCoord1i(t, 0)
        glMultiTexCoord1s(t, 0)
        glMultiTexCoord2d(t, 0.0, 0.0)
        glMultiTexCoord2f(t, 0.0, 0.0)
        glMultiTexCoord2i(t, 0, 0)
        glMultiTexCoord2s(t, 0, 0)
        glMultiTexCoord3d(t, 0.0, 0.0, 0.0)
        glMultiTexCoord3f(t, 0.0, 0.0, 0.0)
        glMultiTexCoord3i(t, 0, 0, 0)
        glMultiTexCoord3s(t, 0, 0, 0)
        glMultiTexCoord4d(t, 0.0, 0.0, 0.0, 1.0)
        glMultiTexCoord4f(t, 0.0, 0.0, 0.0, 1.0)
        glMultiTexCoord4i(t, 0, 0, 0, 1)
        glMultiTexCoord4s(t, 0, 0, 0, 1)
        glMultiTexCoord1dv(t, np.zeros(1, 'd'))
        glMultiTexCoord1fv(t, np.zeros(1, 'f'))
        glMultiTexCoord1iv(t, np.zeros(1, 'i'))
        glMultiTexCoord1sv(t, np.zeros(1, 'h'))
        glMultiTexCoord2dv(t, np.zeros(2, 'd'))
        glMultiTexCoord2fv(t, np.zeros(2, 'f'))
        glMultiTexCoord2iv(t, np.zeros(2, 'i'))
        glMultiTexCoord2sv(t, np.zeros(2, 'h'))
        glMultiTexCoord3dv(t, np.zeros(3, 'd'))
        glMultiTexCoord3fv(t, np.zeros(3, 'f'))
        glMultiTexCoord3iv(t, np.zeros(3, 'i'))
        glMultiTexCoord3sv(t, np.zeros(3, 'h'))
        glMultiTexCoord4dv(t, np.zeros(4, 'd'))
        glMultiTexCoord4fv(t, np.zeros(4, 'f'))
        glMultiTexCoord4iv(t, np.zeros(4, 'i'))
        glMultiTexCoord4sv(t, np.zeros(4, 'h'))
        glEnd()
        self.check_error('gl1.3 multitexture')

    def test_gl13_transpose_and_sample(self):
        glLoadTransposeMatrixf(np.identity(4, 'f'))
        glLoadTransposeMatrixd(np.identity(4, 'd'))
        glMultTransposeMatrixf(np.identity(4, 'f'))
        glMultTransposeMatrixd(np.identity(4, 'd'))
        glSampleCoverage(1.0, GL_FALSE)
        self.check_error('gl1.3 transpose/sample')

    def test_gl13_compressed(self):
        # S3TC is the common desktop compressed format; skip if unavailable
        if 'GL_EXT_texture_compression_s3tc' not in self.extensions():
            self.skipTest('no S3TC')
        fmt = 0x83F1  # GL_COMPRESSED_RGBA_S3TC_DXT1_EXT
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        # PyOpenGL's friendly wrapper derives imageSize from the data array
        glCompressedTexImage2D(GL_TEXTURE_2D, 0, fmt, 4, 4, 0, np.zeros(8, 'B'))
        glCompressedTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 4, 4, fmt, np.zeros(8, 'B'))
        glGetCompressedTexImage(GL_TEXTURE_2D, 0)
        # S3TC is a 2D-only format, so the 1D/3D entry points raise GL errors;
        # the calls still drive the wrappers and exercise() tolerates the error
        with self.exercise():
            t1 = glGenTextures(1)
            glBindTexture(GL_TEXTURE_1D, t1)
            glCompressedTexImage1D(GL_TEXTURE_1D, 0, fmt, 4, 0, np.zeros(8, 'B'))
            glCompressedTexSubImage1D(GL_TEXTURE_1D, 0, 0, 4, fmt, np.zeros(8, 'B'))
            t3 = glGenTextures(1)
            glBindTexture(GL_TEXTURE_3D, t3)
            glCompressedTexImage3D(GL_TEXTURE_3D, 0, fmt, 4, 4, 1, 0, np.zeros(8, 'B'))
            glCompressedTexSubImage3D(
                GL_TEXTURE_3D, 0, 0, 0, 0, 4, 4, 1, fmt, np.zeros(8, 'B')
            )
        self.check_error('gl1.3 compressed')


class TestTheImagingAdditions(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_the_blend_colour_of_1_2_is_settable(self):
        """``glBlendColor`` is the 1.2 promotion of GL_EXT_blend_color."""
        self.require_version(1, 2)
        glBlendColor(0.3, 0.4, 1.0, 0.3)
        self.check_error('glBlendColor')

    def test_a_compressed_texture_uploads_from_a_sized_block(self):
        """S3TC DXT5 is one byte a texel, so 256x256 is 65536 bytes.

        The size is not derivable from the format alone, which is why
        glCompressedTexImage2D takes it -- and why a wrapper that guessed it
        would hand the driver the wrong length.
        """
        self.require_extension('GL_EXT_texture_compression_s3tc')
        from OpenGL.GL.EXT import texture_compression_s3tc as s3tc

        texture = int(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, texture)
        blocks = (GLubyte * (256 * 256))()
        glCompressedTexImage2D(
            GL_TEXTURE_2D, 0, s3tc.GL_COMPRESSED_RGBA_S3TC_DXT5_EXT,
            256, 256, 0, blocks,
        )
        self.check_error('glCompressedTexImage2D')
        glDeleteTextures(1, object_names(texture))


if __name__ == '__main__':
    unittest.main()
