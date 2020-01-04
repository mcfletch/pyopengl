from __future__ import print_function
import pytest, os, sys, unittest
import logging
log = logging.getLogger(__name__)
HERE = os.path.dirname( __file__ )
if sys.platform != 'win32':
    raise pytest.skip('Non-windows (WGL) platform', allow_module_level=True)
try:
    from numpy import *
except ImportError as err:
    array = None
import pygame, pygame.display
pygame.display.init()
from OpenGL.GL import *
from OpenGL.WGL import *

class TestWGL(unittest.TestCase):
    width,height = 300,300
    def setUp(self):
        self.screen = pygame.display.set_mode(
            (self.width,self.height),
            pygame.OPENGL | pygame.DOUBLEBUF,
        )
        
        pygame.display.set_caption('Testing system')
        pygame.key.set_repeat(500,30)
    def tearDown(self):
        pygame.display.flip()

    def test_wgl_imported(self):
        assert bool(wglCreateContext)
    def test_create_context(self):
        window = pygame.display.get_wm_info()['window']
        wglCreateContext(window)

    def test_get_extensions_low_level(self):    
        from OpenGL.WGL.ARB.extensions_string import wglGetExtensionsStringARB
        window = pygame.display.get_wm_info()['window']
        extensions = wglGetExtensionsStringARB(wglGetCurrentDC())
        assert extensions 
        assert b'WGL_ARB_extensions_string' in extensions, extensions

    def test_swap_control_interval(self):
        from OpenGL.WGL.EXT import swap_control
        if not swap_control.wglGetSwapIntervalEXT:
            raise pytest.skip(reason='No wglGetSwapIntervalEXT available')
        interval = swap_control.wglGetSwapIntervalEXT()

        swap_control.wglSwapIntervalEXT(1)
