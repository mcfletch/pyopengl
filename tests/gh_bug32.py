#! /usr/bin/env python
"""Tests bug report #32 from github"""
import os
if not os.environ.get( 'PYOPENGL_PLATFORM' ):
    os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
from math import pi, sin, cos
import OpenGL
OpenGL.USE_ACCELERATE = False
from OpenGL.GL import *
from OpenGL.GL.ARB.fragment_program import glGenProgramsARB
from OpenGL.GLU import *
from OpenGL.osmesa import *
width = height = 300

shared_win = None
# Current OSMesa does not seem to support RGB, only RGBA,
# note also the use of the OSMESA_* constants here, they
# seem to match the GL constants, but can't be too careful.
# Also see ./osdemo.py for a working sample of offscreen
# rendering using OSMesa.
ctx = OSMesaCreateContext(OSMESA_RGBA, shared_win)
buf = arrays.GLubyteArray.zeros((height, width, 4))
mesap = arrays.ArrayDatatype.dataPointer(buf)
assert(OSMesaMakeCurrent(ctx, GLuint(mesap), GL_UNSIGNED_BYTE, width, height))