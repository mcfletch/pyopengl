# requires: numpy
"""Test for github issue #47"""

import sys
import checkutils

# This check is a reference-count leak detector: it asserts that the refcount of
# the array argument is unchanged across many GL calls.  PyPy does not use
# reference counting and exposes no ``sys.getrefcount``, so the check is both
# impossible to run and semantically meaningless there -- skip it.
if not hasattr(sys, 'getrefcount'):
    checkutils.skip('reference-count leak check requires CPython (no sys.getrefcount)')

import OpenGL

OpenGL.SIZE_1_ARRAY_UNPACK = False  # just for convenience
OpenGL.ERROR_ON_COPY = False  # we are checking a leak in the copying
import testdecorator
import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
from sys import getrefcount


@testdecorator.gltest(name="Texture image 2d leak check")
def main():
    data = np.zeros([256, 256, 3], dtype='b')
    glEnable(GL_TEXTURE_2D)
    textures = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, textures[0])
    reversed_data = data[::-1]
    assert not reversed_data.flags['C_CONTIGUOUS']
    rc1 = getrefcount(reversed_data)
    for i in range(100):
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            256,
            256,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            reversed_data,
        )
    rc2 = getrefcount(reversed_data)
    assert rc1 == rc2, (rc1, rc2)
    sys.stdout.write('OK\n')
    sys.stdout.flush()


if __name__ == "__main__":
    checkutils.run_check(main)
