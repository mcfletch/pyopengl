"""Test for github issue #47"""
from __future__ import print_function
import OpenGL
OpenGL.SIZE_1_ARRAY_UNPACK = False # just for convenience
OpenGL.ERROR_ON_COPY = False # we are checking a leak in the copying
import pygamegltest
import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
from sys import getrefcount

@pygamegltest.pygametest(name="Texture image 2d leak check")
def main():
    data = np.zeros([256,256,3],dtype='b')
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
            256, 256, 0, GL_RGB,GL_UNSIGNED_BYTE, reversed_data)
    rc2 = getrefcount(reversed_data)
    assert rc1 == rc2, (rc1, rc2)


if __name__ == "__main__":
    main()
