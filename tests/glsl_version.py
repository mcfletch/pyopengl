#! /usr/bin/env python
from __future__ import print_function
import pygamegltest
from OpenGL.GL import glGetString, GL_SHADING_LANGUAGE_VERSION
from OpenGL._bytes import as_8_bit

@pygamegltest.pygametest(name='Get GL_SHADING_LANGUAGE_VERSION')
def show_glsl_version():
    version = glGetString( GL_SHADING_LANGUAGE_VERSION )
    version = version.split(as_8_bit(' '))[0]
    version = [int(x) for x in version.split(as_8_bit('.'))[:2]]
    return version 

if __name__ == "__main__":
    print( show_glsl_version() )

