from __future__ import print_function
import unittest, pygame, pygame.display, time, os
import logging 
logging.basicConfig(level=logging.INFO)
HERE = os.path.dirname( __file__ )
import pickle
try:
    import cPickle
except ImportError as err:
    cPickle = pickle

try:
    from numpy import *
except ImportError as err:
    array = None

pygame.display.init()
import OpenGL 
if os.environ.get( 'TEST_NO_ACCELERATE' ):
    OpenGL.USE_ACCELERATE = False
#OpenGL.FULL_LOGGING = True
OpenGL.CONTEXT_CHECKING = True
OpenGL.FORWARD_COMPATIBLE_ONLY = False
OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = True

#from OpenGL._bytes import bytes, _NULL_8_BYTE, unicode, as_8_bit
from OpenGL.GL import *
try:
    glGetError()
except error.NoContext as err:
    # good, should have got this error 
    pass
else:
    print( 'WARNING: Failed to catch invalid context' )
    #raise RuntimeError( """Did not catch invalid context!""" )
#from OpenGL import error
from OpenGL.GLU import *
#from OpenGL.arrays import arraydatatype
import OpenGL
from OpenGL.extensions import alternate
#import ctypes
from OpenGL.GL.framebufferobjects import *
from OpenGL.GL.EXT.multi_draw_arrays import *
from OpenGL.GL.ARB.imaging import *

glMultiDrawElements = alternate( 
    glMultiDrawElementsEXT, glMultiDrawElements, 
)

class BaseTest( unittest.TestCase ):
    width = height = 300
    def setUp( self ):
        """Set up the operation"""
        
        self.screen = pygame.display.set_mode(
            (self.width,self.height),
            pygame.OPENGL | pygame.DOUBLEBUF,
        )
        
        pygame.display.set_caption('Testing system')
        pygame.key.set_repeat(500,30)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, 300/300., 1.0, 20.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            -2,0,3, # eyepoint
            0,0,0, # center-of-view
            0,1,0, # up-vector
        )
        glClearColor( 0,0,.25, 0 )
        glClear( GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT )
    
    def tearDown( self ):
        glFlush()
        pygame.display.flip()
        # this is just so that you can see the effect
        # before we run the next test...
        time.sleep( .05 )
