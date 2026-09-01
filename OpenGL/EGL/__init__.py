"""OpenGL.EGL the portable interface to GL environments"""
from OpenGL._declarations import define as _define
_define(globals(), 'OpenGL.raw.EGL._types')
from OpenGL.raw.EGL._errors import EGLError
from OpenGL.EGL.VERSION.EGL_1_0 import *
from OpenGL.EGL.VERSION.EGL_1_1 import *
from OpenGL.EGL.VERSION.EGL_1_2 import *
from OpenGL.EGL.VERSION.EGL_1_3 import *
from OpenGL.EGL.VERSION.EGL_1_4 import *
from OpenGL.EGL.VERSION.EGL_1_5 import *
