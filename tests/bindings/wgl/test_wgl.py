from __future__ import print_function
import pytest, os, sys, unittest
import logging
log = logging.getLogger(__name__)
HERE = os.path.dirname( __file__ )
if sys.platform != 'win32':
    raise pytest.skip('Non-windows (WGL) platform', allow_module_level=True)
import pygame, pygame.display
from OpenGL.GL import *
from OpenGL.WGL import *

class TestWGL(unittest.TestCase):
    width,height = 300,300

    #: Whether the window may be seen.  ``TEST_VISIBLE=0`` is how the suite
    #: says it may not, and these cases need a window rather than a *shown*
    #: one: several hundred GL tests flashing windows over whatever the person
    #: running them is doing, and taking the focus while they type, is not
    #: something to inflict on anyone.  See tests/glcontext_pygame.py, which
    #: hides its window the same way.
    visible = os.environ.get('TEST_VISIBLE', '1').strip().lower() not in (
        '0', 'false', 'no', '',
    )

    def setUp(self):
        # Here rather than at module scope: pytest imports every module while
        # it collects, so an import-time init starts the display subsystem for
        # a run that may not go on to use it.
        pygame.display.init()
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if not self.visible:
            # pygame.HIDDEN arrived in pygame 2.0; fall back gracefully.
            flags |= getattr(pygame, 'HIDDEN', 0)
        self.screen = pygame.display.set_mode((self.width,self.height), flags)
        pygame.display.set_caption('Testing system')
        pygame.key.set_repeat(500,30)

    def tearDown(self):
        pygame.display.flip()
        # And give the window back.  ``set_mode`` alone leaves it on screen for
        # the rest of the process -- the run has hundreds of tests still to go
        # and a window sitting over them for all of it -- and the GL context it
        # carries stays current, which the next backend to ask for the thread
        # then has to take off it.
        pygame.display.quit()

    def test_wgl_imported(self):
        assert bool(wglCreateContext)

    def test_the_gdi_entry_points_resolve(self):
        """The calls a WGL program makes that GDI owns rather than OpenGL.

        opengl32 exports none of these and wglGetProcAddress answers for none
        of them -- it returns extension entry points, and these are not
        extensions -- so they resolve only where the search knows to look in
        gdi32 as well. Both ways of binding a function have to know that: the
        C dispatcher found none of these while the ctypes path found all five,
        which is a program that cannot set a pixel format or show a frame.
        """
        missing = [name for name in ('ChoosePixelFormat', 'DescribePixelFormat',
                                     'GetPixelFormat', 'SetPixelFormat',
                                     'SwapBuffers')
                   if not bool(globals().get(name))]
        assert not missing, 'unresolved GDI entry points: %s' % (missing,)
    def test_create_context(self):
        window = pygame.display.get_wm_info()['window']
        wglCreateContext(window)

    def test_get_extensions_low_level(self):    
        from OpenGL.WGL.ARB.extensions_string import wglGetExtensionsStringARB
        pygame.display.get_wm_info()['window']
        extensions = wglGetExtensionsStringARB(wglGetCurrentDC())
        assert extensions 
        assert b'WGL_ARB_extensions_string' in extensions, extensions

    def test_swap_control_interval(self):
        from OpenGL.WGL.EXT import swap_control
        if not swap_control.wglGetSwapIntervalEXT:
            raise pytest.skip(reason='No wglGetSwapIntervalEXT available')
        swap_control.wglGetSwapIntervalEXT()

        swap_control.wglSwapIntervalEXT(1)
