#! /usr/bin/env python
"""Attempt to import GLES libraries"""
import os
if not 'PYOPENGL_PLATFORM' in os.environ:
    os.environ['PYOPENGL_PLATFORM'] = 'egl'
from OpenGL.GLES1 import *
from OpenGL.GLES2 import *
from OpenGL.GLES3 import *
