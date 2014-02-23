import os
if not os.environ.get( 'PYOPENGL_PLATFORM' ):
    os.environ['PYOPENGL_PLATFORM'] = 'egl'
from OpenGL import GLES1
from OpenGL.arrays.vbo import VBO
