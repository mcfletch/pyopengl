#! /usr/bin/env python3
"""GLU image helpers: gluScaleImage and the gluBuild{1,2,3}DMipmaps /
gluBuild{1,2,3}DMipmapLevels texture-pyramid builders."""

import unittest
from arraycompat import np, object_names, one

from glutestcase import GLUTestCase, requireEntryPoint
from OpenGL.GL import (
    glGenTextures,
    glBindTexture,
    glDeleteTextures,
    GL_TEXTURE_1D,
    GL_TEXTURE_2D,
    GL_TEXTURE_3D,
    GL_RGBA,
    GL_RGB,
    GL_UNSIGNED_BYTE,
)
from OpenGL.GLU import (
    gluScaleImage,
    gluBuild1DMipmaps,
    gluBuild2DMipmaps,
    gluBuild3DMipmaps,
    gluBuild1DMipmapLevels,
    gluBuild2DMipmapLevels,
    gluBuild3DMipmapLevels,
)


def _checker(shape):
    """A small image of the given (..., channels) shape with the red channel
    saturated (built without numpy fancy-indexing so it works on the ctypes
    fallback too)."""
    *outer, channels = shape

    def pixel():
        px = [0] * channels
        px[0] = 255
        return px

    def build(dims):
        if not dims:
            return pixel()
        return [build(dims[1:]) for _ in range(dims[0])]

    return np.array(build(outer), 'B')


class TestGLUImages(GLUTestCase):
    def _texture(self, target):
        tex = one(glGenTextures(1))
        glBindTexture(target, int(tex))
        self._cleanup.append(lambda: glDeleteTextures(object_names(tex)))
        return tex

    def test_scale_image(self):
        src = _checker((8, 8, 3))
        dst = np.zeros((4, 4, 3), 'B')
        gluScaleImage(GL_RGB, 8, 8, GL_UNSIGNED_BYTE, src, 4, 4, GL_UNSIGNED_BYTE, dst)
        self.check_error('gluScaleImage')
        # Down-scaling a solid-red checkerboard keeps the red channel saturated.
        reds = [dst[i][j][0] for i in range(4) for j in range(4)]
        self.assertGreater(int(max(reds)), 0)

    def test_scale_image_upscale(self):
        src = _checker((2, 2, 3))
        dst = np.zeros((4, 4, 3), 'B')
        gluScaleImage(GL_RGB, 2, 2, GL_UNSIGNED_BYTE, src, 4, 4, GL_UNSIGNED_BYTE, dst)
        self.check_error('gluScaleImage upscale')

    def test_build_1d_mipmaps(self):
        self._texture(GL_TEXTURE_1D)
        gluBuild1DMipmaps(GL_TEXTURE_1D, GL_RGB, 8, GL_RGB, GL_UNSIGNED_BYTE, _checker((8, 3)))
        self.check_error('gluBuild1DMipmaps')

    def test_build_2d_mipmaps(self):
        self._texture(GL_TEXTURE_2D)
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, 8, 8, GL_RGBA, GL_UNSIGNED_BYTE,
                          np.zeros((8, 8, 4), 'B'))
        self.check_error('gluBuild2DMipmaps')

    def test_build_3d_mipmaps(self):
        requireEntryPoint(gluBuild3DMipmaps, 'gluBuild3DMipmaps')
        self._texture(GL_TEXTURE_3D)
        gluBuild3DMipmaps(GL_TEXTURE_3D, GL_RGB, 8, 8, 8, GL_RGB, GL_UNSIGNED_BYTE,
                          _checker((8, 8, 8, 3)))
        self.check_error('gluBuild3DMipmaps')

    def test_build_1d_mipmap_levels(self):
        requireEntryPoint(gluBuild1DMipmapLevels, 'gluBuild1DMipmapLevels')
        self._texture(GL_TEXTURE_1D)
        gluBuild1DMipmapLevels(GL_TEXTURE_1D, GL_RGB, 8, GL_RGB, GL_UNSIGNED_BYTE,
                               0, 0, 3, _checker((8, 3)))
        self.check_error('gluBuild1DMipmapLevels')

    def test_build_2d_mipmap_levels(self):
        requireEntryPoint(gluBuild2DMipmapLevels, 'gluBuild2DMipmapLevels')
        self._texture(GL_TEXTURE_2D)
        gluBuild2DMipmapLevels(GL_TEXTURE_2D, GL_RGB, 8, 8, GL_RGB, GL_UNSIGNED_BYTE,
                               0, 0, 3, _checker((8, 8, 3)))
        self.check_error('gluBuild2DMipmapLevels')

    def test_build_3d_mipmap_levels(self):
        requireEntryPoint(gluBuild3DMipmapLevels, 'gluBuild3DMipmapLevels')
        self._texture(GL_TEXTURE_3D)
        gluBuild3DMipmapLevels(GL_TEXTURE_3D, GL_RGB, 8, 8, 8, GL_RGB, GL_UNSIGNED_BYTE,
                               0, 0, 3, _checker((8, 8, 8, 3)))
        self.check_error('gluBuild3DMipmapLevels')


if __name__ == '__main__':
    unittest.main()
