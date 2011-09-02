"""OpenGL.GL, the core GL library and extensions to it"""
from OpenGL.raw.GL import *
from OpenGL.raw.GL.annotations import *

from OpenGL.GL.pointers import *
from OpenGL.GL.glget import *
from OpenGL.GL.images import *

from OpenGL.GL.exceptional import *
from OpenGL.error import *

from OpenGL.GL.VERSION.GL_1_2 import *
from OpenGL.GL.VERSION.GL_1_3 import *
from OpenGL.GL.VERSION.GL_1_4 import *
from OpenGL.GL.VERSION.GL_1_5 import *
from OpenGL.GL.VERSION.GL_2_0 import *
from OpenGL.GL.VERSION.GL_2_1 import *
from OpenGL.GL.VERSION.GL_3_0 import *
from OpenGL.GL.VERSION.GL_3_1 import *
from OpenGL.GL.VERSION.GL_3_2 import *
from OpenGL.GL.VERSION.GL_3_3 import *
from OpenGL.GL.VERSION.GL_4_0 import *
from OpenGL.GL.VERSION.GL_4_1 import *
from OpenGL.GL.VERSION.GL_4_2 import *

GLerror = GLError

# Now the aliases...
glRotate = glRotated
glTranslate = glTranslated
glLight = glLightfv
glTexCoord = glTexCoord2d
glScale = glScaled
#glColor = glColor3f
glNormal = glNormal3d
