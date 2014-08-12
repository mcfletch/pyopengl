#! /usr/bin/env python
import pygamegltest
from OpenGL.GL import glGetString, GL_SHADING_LANGUAGE_VERSION

@pygamegltest.pygametest(name='Get GL_SHADING_LANGUAGE_VERSION')
def show_glsl_version():
    version = glGetString( GL_SHADING_LANGUAGE_VERSION )
    version = [int(x) for x in version.split('.')[:2]]
    return version 

if __name__ == "__main__":
    print( show_glsl_version() )

