#! /usr/bin/env python3
"""GL 1.0 (compatibility): texture images, parameters, env, texgen, queries."""

import unittest
from arraycompat import np  # numpy, or a ctypes fallback when numpy is absent

from gltestcase import GLTestCase
from OpenGL.GL import *  # noqa: F401,F403


class TestGL1Texture(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_image_and_parameters(self):
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            4,
            4,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            np.zeros((4, 4, 4), 'B'),
        )
        glTexImage1D(
            GL_TEXTURE_1D,
            0,
            GL_RGBA,
            4,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            np.zeros((4, 4), 'B'),
        )
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, float(GL_NEAREST))
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, np.zeros(4, 'f'))
        glTexParameteriv(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, np.array([GL_REPEAT], 'i'))
        glGetTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, np.zeros(1, 'f'))
        glGetTexParameteriv(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, np.zeros(1, 'i'))
        glGetTexLevelParameterfv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH, np.zeros(1, 'f'))
        glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH, np.zeros(1, 'i'))
        data = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        self.assertTrue(len(data) > 0)
        self.check_error('texture image/params')

    def test_texenv_texgen(self):
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, float(GL_MODULATE))
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
        glTexEnvfv(GL_TEXTURE_ENV, GL_TEXTURE_ENV_COLOR, np.zeros(4, 'f'))
        glTexEnviv(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, np.array([GL_DECAL], 'i'))
        glGetTexEnvfv(GL_TEXTURE_ENV, GL_TEXTURE_ENV_COLOR, np.zeros(4, 'f'))
        glGetTexEnviv(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, np.zeros(1, 'i'))
        glTexGend(GL_S, GL_TEXTURE_GEN_MODE, GL_OBJECT_LINEAR)
        glTexGenf(GL_T, GL_TEXTURE_GEN_MODE, float(GL_OBJECT_LINEAR))
        glTexGeni(GL_R, GL_TEXTURE_GEN_MODE, GL_OBJECT_LINEAR)
        glTexGendv(GL_S, GL_OBJECT_PLANE, np.array([1, 0, 0, 0], 'd'))
        glTexGenfv(GL_T, GL_OBJECT_PLANE, np.array([0, 1, 0, 0], 'f'))
        glTexGeniv(GL_S, GL_TEXTURE_GEN_MODE, np.array([GL_EYE_LINEAR], 'i'))
        glGetTexGendv(GL_S, GL_OBJECT_PLANE, np.zeros(4, 'd'))
        glGetTexGenfv(GL_T, GL_OBJECT_PLANE, np.zeros(4, 'f'))
        glGetTexGeniv(GL_S, GL_TEXTURE_GEN_MODE, np.zeros(1, 'i'))
        self.check_error('texenv/texgen')


class TestTextureNamesAndResidence(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_generating_one_name_gives_a_usable_integer(self):
        texture = glGenTextures(1)
        self.assertTrue(texture)
        self.assertTrue(int(texture))
        glDeleteTextures(1, [int(texture)])

    def test_a_generated_name_may_be_passed_straight_back_in(self):
        """``glGenTextures(2)`` hands back array elements, not Python ints.

        With numpy installed those elements are ``numpy.uint32``, and passing
        one to the next call is the obvious thing to write.  It works, and
        without help: ctypes converts any numpy *integer* scalar itself, so the
        ``ALLOW_NUMPY_SCALARS`` flag that ``OpenGL/__init__.py`` documents for
        this is not what makes it work and defaults off.  What the flag adds is
        a retry through ``long()``, which reaches a numpy *float* where an
        integer is wanted -- see ``OpenGL/raw/GL/_types.py``.
        """
        textures = glGenTextures(2)
        for texture in textures:
            glBindTexture(GL_TEXTURE_2D, texture)
        self.check_error('binding a texture by the name glGenTextures returned')
        glBindTexture(GL_TEXTURE_2D, 0)
        glDeleteTextures(2, [int(t) for t in textures])

    def test_residence_is_reported_for_every_texture_asked_about(self):
        """``glAreTexturesResident`` answers one flag per name.

        The output array is sized from the input, so a binding that sized it
        from something else overruns; what each flag *says* is the driver's
        business and varies with what else is on the card.
        """
        textures = glGenTextures(2)
        data = np.array([(0, 255, 0)], 'i')
        for texture in textures:
            glBindTexture(GL_TEXTURE_2D, int(texture))
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 1, 1, 0, GL_RGB, GL_INT, data)
        glGetError()  # drain: an unsupported format above is not what is asked
        residence = glAreTexturesResident(textures)
        self.assertEqual(len(residence), 2, residence)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDeleteTextures(2, [int(t) for t in textures])


class TestQueryingTextureState(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_an_enable_bit_reads_back_as_a_boolean(self):
        """``glGetBoolean(GL_TEXTURE_2D)`` is a one-element query."""
        glEnable(GL_TEXTURE_2D)
        self.assertTrue(glGetBoolean(GL_TEXTURE_2D))
        glDisable(GL_TEXTURE_2D)
        self.assertFalse(glGetBoolean(GL_TEXTURE_2D))
        self.check_error('glGetBoolean(GL_TEXTURE_2D)')

    def test_the_image_unit_count_is_positive(self):
        """SF#2895081: this pname read back as nothing at all."""
        units = glGetIntegerv(GL_MAX_TEXTURE_IMAGE_UNITS)
        self.assertTrue(units, units)
        self.assertGreaterEqual(int(units), 2)

    def test_the_histogram_of_the_imaging_subset_switches_on_and_off(self):
        """``GL_ARB_imaging`` is an optional block of the compatibility profile."""
        if not glInitImagingARB():
            self.skipTest('the ARB_imaging subset is not available here')
        glHistogram(GL_HISTOGRAM, 256, GL_LUMINANCE, GL_FALSE)
        glEnable(GL_HISTOGRAM)
        glDisable(GL_HISTOGRAM)
        self.check_error('glHistogram')


if __name__ == '__main__':
    unittest.main()
