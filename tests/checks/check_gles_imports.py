#! /usr/bin/env python
"""Attempt to import GLES libraries"""
import os

if 'PYOPENGL_PLATFORM' not in os.environ:
    os.environ['PYOPENGL_PLATFORM'] = 'egl'
from OpenGL.GLES1 import *
from OpenGL.GLES2 import *
from OpenGL.GLES3 import *

print('OK')
