#! /usr/bin/env python3
"""``OpenGL.arrays.vbo.VBO``: an array that lives on the card.

The wrapper's job is to look like the array it was given while keeping the
buffer object behind it in step: bound where a pointer is wanted, re-uploaded
where a slice is assigned, and deleted once rather than twice.  Each of those
is a place a caller notices only much later -- a stale buffer draws the last
frame's data, and a double delete takes a name the driver has since reissued.

Also here: a memory-mapped file as the source of pixel data, which is the case
where the array PyOpenGL is handed is a window onto something it does not own.
"""

import os
import tempfile
import unittest

import pytest

from arraycompat import np
from gltestcase import GLTestCase
from OpenGL.arrays import vbo
from OpenGL.GL import *  # noqa: F401,F403

#: A closed outline, as doubles.
POINTS = [
    [0, 0, 0], [0, 1, 0], [1, 0.5, 0], [1, 0, 0], [1.5, 0.5, 0], [1.5, 0, 0],
]


class TestDrawingFromAVBO(GLTestCase):
    profile = 'compatibility'
    gl_version = (2, 1)

    def setUp(self):
        super().setUp()
        if not vbo.get_implementation():
            self.skipTest('no vertex-buffer-object implementation is available')

    def buffer(self):
        points = np.array(POINTS, 'd')
        buffer = vbo.VBO(points)
        self.defer_cleanup(buffer.delete)
        return buffer

    def test_a_bound_buffer_is_what_the_vertex_pointer_reads(self):
        buffer = self.buffer()
        indices = np.array(list(range(len(POINTS))), 'I')
        glDisable(GL_CULL_FACE)
        glEnableClientState(GL_VERTEX_ARRAY)
        try:
            with buffer:
                glVertexPointerd(buffer)
                glDrawElements(
                    GL_LINE_LOOP, len(indices), GL_UNSIGNED_INT, indices
                )
        finally:
            glDisableClientState(GL_VERTEX_ARRAY)
        self.check_error('drawing from a VBO')

    def test_assigning_a_slice_re_uploads_it(self):
        """The copy on the card has to follow the copy in memory."""
        buffer = self.buffer()
        glEnableClientState(GL_VERTEX_ARRAY)
        try:
            with buffer:
                glVertexPointerd(buffer)
            buffer[-2:-1] = np.array([[1.5, 0.25, 0]], 'd')
            with buffer:
                glVertexPointerd(buffer)
        finally:
            glDisableClientState(GL_VERTEX_ARRAY)
        self.check_error('re-uploading a slice')

    def test_deleting_it_explicitly_is_not_an_error(self):
        """Reported by Dan Helfman: delete() then the deleter at collection."""
        buffer = vbo.VBO(np.array(POINTS, 'd'))
        with buffer:
            pass
        buffer.delete()
        buffer.delete()  # the second one has nothing to do, and must not raise
        self.check_error('deleting a VBO twice')


class TestPixelsFromAMappedFile(GLTestCase):
    """``numpy.memmap`` as the source array: PyOpenGL does not own the pages.

    What it has to get right is the length, since a mapping is sized by the
    file rather than by anything in the call.
    """

    profile = 'compatibility'
    gl_version = (2, 1)

    SIDE = 32

    def test_drawing_pixels_from_a_mapping(self):
        numpy = pytest.importorskip('numpy', reason='memmap is numpy\'s')
        # In a directory of its own: the version of this that wrote
        # `mmap-test-data.dat` left it wherever the run was started from, which
        # is why that name is in .gitignore.
        directory = tempfile.TemporaryDirectory()
        self.defer_cleanup(directory.cleanup)
        path = os.path.join(directory.name, 'pixels.dat')
        with open(path, 'wb') as handle:
            handle.write(b'\x00' * (self.SIDE * self.SIDE * 3))

        data = numpy.memmap(path, dtype='uint8', mode='r+')
        try:
            glDrawPixels(
                self.SIDE, self.SIDE, GL_RGB, GL_UNSIGNED_BYTE, data
            )
            self.check_error('glDrawPixels from a memmap')
            data[::2] = 128
            glDrawPixels(
                self.SIDE, self.SIDE, GL_RGB, GL_UNSIGNED_BYTE, data
            )
            self.check_error('glDrawPixels from a modified memmap')
        finally:
            del data


if __name__ == '__main__':
    unittest.main()
