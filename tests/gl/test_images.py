#! /usr/bin/env python3
"""Pixel data crossing the boundary: what comes back, and in what shape.

``glReadPixels`` and its friends have to decide the size and the element type
of the array they hand back from the format, the type and the rectangle -- and
get it right, because the alternative is an array shorter than the driver wrote
into.  ``OpenGL.toplevel_images.createTargetArray`` is the same arithmetic offered to a
caller that wants to allocate the array itself.  Both are where a
format/type combination nobody tried lands wrongly.

The counterpart for the *generated* side of this is ``cdispatch/test_images.py``,
which asks what the annotations say; this asks what the calls do.
"""

import ctypes
import unittest

import pytest

from arraycompat import np, object_names, one
from gltestcase import GLTestCase
from OpenGL.arrays import arraydatatype
from OpenGL.GL import *  # noqa: F401,F403
# After the star import, which binds `images` to OpenGL.GL.images.
from OpenGL import images as toplevel_images
from OpenGL.GL.ARB import texture_rg


class TestReadingPixelsBack(GLTestCase):
    """Issues #1979002 and #1959860, and SF#1311265: the shape of the result."""

    profile = 'compatibility'
    gl_version = (2, 1)
    width = height = 32

    def test_the_unsigned_byte_form_is_bytes(self):
        """``UNSIGNED_BYTE_IMAGES_AS_STRING`` is on by default, and says so.

        A caller doing ``len(image)`` on the result is relying on it, so the
        two element types have to answer differently and predictably.
        """
        import OpenGL

        image = glReadPixels(0, 0, self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE)
        if OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING:
            self.assertIsInstance(image, bytes, type(image))
            self.assertEqual(len(image), self.width * self.height * 3)
        else:
            self.assertNotIsInstance(image, bytes, type(image))

    def test_a_signed_byte_form_is_an_array(self):
        """Only the *unsigned* byte form is a str; GL_BYTE is an array."""
        image = glReadPixels(0, 0, self.width, self.height, GL_RGB, GL_BYTE)
        self.assertNotIsInstance(image, bytes, type(image))

    def test_the_element_type_decides_the_size(self):
        """#1979002 was a crash from mis-calculating the resulting array size."""
        as_bytes = glReadPixelsub(0, 0, self.width, self.height, GL_RGB)
        as_floats = glReadPixelsf(0, 0, self.width, self.height, GL_RGB)
        self.assertIsNotNone(as_bytes)
        self.assertIsNotNone(as_floats)
        self.assertEqual(
            arraydatatype.ArrayDatatype.arrayByteCount(as_floats),
            4 * arraydatatype.ArrayDatatype.arrayByteCount(as_bytes),
            'a float image of the same rectangle is four bytes an element '
            'against one',
        )
        self.check_error('glReadPixels')

    def test_an_array_may_be_passed_in_to_fill(self):
        """SF#1311265: the caller allocates, the call fills it in place."""
        pytest.importorskip('numpy', reason='needs an array with a buffer to fill')
        target = np.zeros((self.height, self.width, 3), 'B')
        filled = glReadPixelsub(
            0, 0, self.width, self.height, GL_RGB, array=target
        )
        self.assertIsNotNone(filled)
        self.check_error('glReadPixels into a caller array')


class TestReadingATextureBack(GLTestCase):
    """``glGetTexImage`` sizes its result from the texture, not from a count.

    The rectangle is not an argument: the wrapper asks the texture how big it
    is and allocates from that, which is one more place the format/type
    arithmetic has to be right.  The typed spelling and the general one have to
    agree about the element type they hand back.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    SIDE = 4

    def uploaded(self):
        texture = one(glGenTextures(1))
        self.defer_cleanup(lambda: glDeleteTextures(1, object_names(texture)))
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        pixels = np.zeros((self.SIDE, self.SIDE, 4), 'B')
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA8, self.SIDE, self.SIDE, 0,
            GL_RGBA, GL_UNSIGNED_BYTE, pixels,
        )
        self.check_error('glTexImage2D')
        return texture

    def test_the_unsigned_byte_form_is_bytes_of_the_right_length(self):
        import OpenGL

        self.uploaded()
        image = glGetTexImageub(GL_TEXTURE_2D, 0, GL_RGBA)
        if OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING:
            self.assertIsInstance(image, bytes, type(image))
            self.assertEqual(len(image), self.SIDE * self.SIDE * 4)
        self.check_error('glGetTexImageub')

    def test_the_general_form_agrees_with_the_typed_one(self):
        self.uploaded()
        typed = glGetTexImageub(GL_TEXTURE_2D, 0, GL_RGBA)
        general = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
        self.assertEqual(type(typed), type(general))
        self.assertEqual(bytes(typed), bytes(general))
        self.check_error('glGetTexImage')


class TestSizingATargetArray(GLTestCase):
    """``toplevel_images.createTargetArray`` sizes an array for a format/type pair."""

    profile = 'compatibility'
    gl_version = (2, 1)

    SIZE = (640, 480)

    def byte_count(self, array):
        if hasattr(array, 'nbytes'):
            return array.nbytes
        return ctypes.sizeof(array)

    def test_a_packed_type_and_its_unpacked_equivalent_are_the_same_size(self):
        """32 bits a pixel is 32 bits a pixel however the components are cut."""
        packed_bgra = toplevel_images.createTargetArray(
            GL_BGRA, self.SIZE, GL_UNSIGNED_INT_8_8_8_8_REV
        )
        loose_rgba = toplevel_images.createTargetArray(GL_RGBA, self.SIZE, GL_UNSIGNED_BYTE)
        packed_rgba = toplevel_images.createTargetArray(
            GL_RGBA, self.SIZE, GL_UNSIGNED_INT_8_8_8_8_REV
        )
        self.assertEqual(self.byte_count(packed_bgra), self.byte_count(packed_rgba))
        self.assertEqual(self.byte_count(packed_bgra), self.byte_count(loose_rgba))

    def test_the_size_is_the_rectangle_times_the_pixel(self):
        array = toplevel_images.createTargetArray(GL_RGBA, self.SIZE, GL_UNSIGNED_BYTE)
        self.assertEqual(
            self.byte_count(array), self.SIZE[0] * self.SIZE[1] * 4
        )

    def test_a_type_too_narrow_for_the_format_is_refused(self):
        """``GL_UNSIGNED_BYTE_3_3_2`` has three components and RGBA has four.

        Sizing it anyway would hand the driver an array a quarter of the size
        it writes into.
        """
        with self.assertRaises(ValueError):
            toplevel_images.createTargetArray(GL_RGBA, self.SIZE, GL_UNSIGNED_BYTE_3_3_2)


class TestDrawingPixels(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def test_a_bitmap_is_one_bit_a_pixel(self):
        """SF#2152623: GL_BITMAP data is bits, so the array is small."""
        # An 8x8 bitmap is eight bytes, not sixty-four: a size derived from the
        # rectangle alone would read 56 bytes past the end.
        glDrawPixels(8, 8, GL_COLOR_INDEX, GL_BITMAP, np.zeros(8, 'B'))
        self.check_error('glDrawPixels with GL_BITMAP')

    def test_a_null_texture_image_allocates_without_data(self):
        texture = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 512, 512, 0, GL_RGB, GL_INT, None)
        self.check_error('glTexImage2D with no data')
        glDeleteTextures(1, object_names(texture))


class TestTwoComponentTextures(GLTestCase):
    """``GL_ARB_texture_rg``: a format with two components rather than three."""

    profile = 'compatibility'
    gl_version = (2, 1)

    def test_a_two_channel_float_texture_uploads(self):
        self.require_extension('GL_ARB_texture_rg')
        texture = one(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(
            GL_TEXTURE_2D, 0, texture_rg.GL_RG, 1, 1, 0, GL_RG, GL_FLOAT,
            np.array([0.3, 0.5], 'f'),
        )
        self.check_error('GL_RG texture upload')
        glDeleteTextures(1, object_names(texture))


class TestAnImageTheCallerKeeps(GLTestCase):
    """Uploading an image must not take a reference and hold it.

    PyOpenGL converts an array the driver cannot read directly -- one that is
    not contiguous, or not of the element type the call names -- by copying it
    into a buffer of its own. The copy is the right thing; keeping the
    original alive afterwards is not. A renderer uploading a frame each time
    round its loop then accumulates one array per frame, which is a leak
    measured in the size of the images rather than in bytes.

    ``data[::-1]`` is how it arrives in practice: an image flipped so it is
    the right way up, which is what both tickets were doing.

    https://github.com/mcfletch/pyopengl/issues/47
    https://github.com/mcfletch/pyopengl/issues/96
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    #: Enough repetitions that a leak of one reference per call is unmistakable
    #: beside the ordinary noise of a refcount read.
    UPLOADS = 8

    def setUp(self):
        super().setUp()
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def tearDown(self):
        glDeleteTextures(1, object_names(self.texture))
        super().tearDown()

    def upload(self, image):
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 16, 16, 0, GL_RGBA,
                     GL_UNSIGNED_BYTE, image)

    def assert_no_references_kept(self, image, what):
        import sys

        self.upload(image)                 # the first one may cache legitimately
        before = sys.getrefcount(image)
        for _ in range(self.UPLOADS):
            self.upload(image)
        after = sys.getrefcount(image)
        self.check_error(what)
        self.assertEqual(
            after, before,
            '%s: %d uploads took %d reference(s) and did not give them back'
            % (what, self.UPLOADS, after - before))

    @pytest.mark.skipif(not hasattr(np, 'ndarray'),
                        reason='needs numpy itself, not the ctypes shim')
    def test_a_contiguous_image_is_not_retained(self):
        self.assert_no_references_kept(
            np.zeros((16, 16, 4), dtype='u1'), 'a contiguous image')

    @pytest.mark.skipif(not hasattr(np, 'ndarray'),
                        reason='needs numpy itself, not the ctypes shim')
    def test_a_flipped_image_is_not_retained(self):
        """The case both tickets hit: PyOpenGL has to copy this one."""
        image = np.zeros((16, 16, 4), dtype='u1')[::-1]
        self.assertFalse(image.flags['C_CONTIGUOUS'])
        self.assert_no_references_kept(image, 'a flipped image')

    @pytest.mark.skipif(not hasattr(np, 'ndarray'),
                        reason='needs numpy itself, not the ctypes shim')
    def test_the_reported_sequence_completes(self):
        """#96 in full: upload a flipped image, then build its mipmaps.

        The report is a segfault in ``glGenerateMipmap``, which is where a
        short or freed upload buffer would be noticed rather than where it was
        made -- the upload writes into the texture and the mipmap build reads
        the whole of it back.
        """
        if not glGenerateMipmap:
            self.skipTest('no glGenerateMipmap on this context')
        image = np.zeros((64, 64, 3), dtype='u1')
        image[:, :, 1] = 200
        flipped = np.flip(image, 0)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, 64, 64, 0, GL_RGB,
                     GL_UNSIGNED_BYTE,
                     np.frombuffer(flipped.tobytes(), np.uint8))
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, 3)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR)
        glFinish()
        self.check_error('upload a flipped image and build its mipmaps')


class TestHalfFloatImages(GLTestCase):
    """``GL_HALF_FLOAT`` is an element type images can be given in.

    Sixteen-bit floats are how a renderer uploads high-dynamic-range data at
    half the bandwidth, so the type is ordinary rather than exotic. It reaches
    PyOpenGL through the same table as every other: a type absent from
    ``TYPE_TO_ARRAYTYPE`` is a ``KeyError`` naming the constant and the
    converter object, several frames inside the wrapper, which is what the
    ticket reports.

    https://github.com/mcfletch/pyopengl/issues/51
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    def setUp(self):
        super().setUp()
        self.require_extension('GL_ARB_half_float_pixel')
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)

    def tearDown(self):
        glDeleteTextures(1, object_names(self.texture))
        super().tearDown()

    def test_the_type_is_known_to_the_image_machinery(self):
        """Asked of the table directly, so a failure names the missing type
        rather than arriving as a KeyError out of a converter."""
        from OpenGL.arrays import GL_CONSTANT_TO_ARRAY_TYPE

        array_type = toplevel_images.TYPE_TO_ARRAYTYPE.get(
            GL_HALF_FLOAT, GL_HALF_FLOAT)
        self.assertIn(
            array_type, GL_CONSTANT_TO_ARRAY_TYPE,
            'GL_HALF_FLOAT maps to %r, which is not an array type'
            % (array_type,))

    @pytest.mark.skipif(not hasattr(np, 'ndarray'),
                        reason='needs numpy itself, not the ctypes shim')
    def test_a_half_float_image_uploads(self):
        image = np.zeros((16, 16, 4), dtype='float16')
        image[:, :, 0] = 0.5
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, 16, 16, 0, GL_RGBA,
                     GL_HALF_FLOAT, image)
        glFinish()
        self.check_error('glTexImage2D with GL_HALF_FLOAT')

    @pytest.mark.skipif(not hasattr(np, 'ndarray'),
                        reason='needs numpy itself, not the ctypes shim')
    def test_a_half_float_image_reads_back(self):
        image = np.zeros((16, 16, 4), dtype='float16')
        image[:, :, 0] = 0.5
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, 16, 16, 0, GL_RGBA,
                     GL_HALF_FLOAT, image)
        glFinish()
        read = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_HALF_FLOAT)
        self.check_error('glGetTexImage with GL_HALF_FLOAT')
        self.assertEqual(np.asarray(read).dtype, np.dtype('float16'))


if __name__ == '__main__':
    unittest.main()
