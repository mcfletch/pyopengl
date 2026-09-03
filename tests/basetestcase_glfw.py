from __future__ import print_function
import unittest, glfw, time, os
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

if not glfw.init():
    raise RuntimeError( 'Failed to initialise GLFW' )
import OpenGL
if os.environ.get( 'TEST_NO_ACCELERATE' ):
    OpenGL.USE_ACCELERATE = False
#OpenGL.FULL_LOGGING = True
OpenGL.CONTEXT_CHECKING = True
OpenGL.FORWARD_COMPATIBLE_ONLY = False
OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = True

#from OpenGL._bytes import bytes, _NULL_8_BYTE, unicode, as_8_bit
from OpenGL.GL import *
# What an entry point does with no current context is decided by
# OpenGL.CONTEXT_CHECKING, which only takes effect if it is set before anything
# builds the entry points -- so it cannot be asked here, where OpenGL.GL is
# usually already imported by whatever was collected first.
# tests/gl/test_no_context_calls.py settles it in a subprocess instead.
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
    #: show the window by default (set TEST_VISIBLE=0 for headless/CI runs).
    #: Off by default: a suite that maps windows takes over the screen of
    #: whoever runs it, and steals focus while they are doing something
    #: else.  ``TEST_VISIBLE=1`` to watch a run.  A hidden window still
    #: has a real context on the real driver, so nothing is given up.
    visible = os.environ.get('TEST_VISIBLE', '0').lower() in ('1', 'true', 'yes')
    def setUp( self ):
        """Set up the operation"""

        glfw.default_window_hints()
        glfw.window_hint( glfw.VISIBLE, glfw.TRUE if self.visible else glfw.FALSE )
        self.screen = glfw.create_window(
            self.width, self.height, 'Testing system', None, None,
        )
        if not self.screen:
            raise RuntimeError( 'Failed to create GLFW window' )
        glfw.make_context_current( self.screen )

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

    def flip( self ):
        """Swap the front and back buffers"""
        glFlush()
        glfw.swap_buffers( self.screen )

    def tearDown( self ):
        self.flip()
        # this is just so that you can see the effect
        # before we run the next test (skip the dwell when hidden)...
        if self.visible:
            time.sleep( .05 )
        glfw.destroy_window( self.screen )
        self.screen = None
