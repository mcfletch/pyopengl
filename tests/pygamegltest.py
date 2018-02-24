"""Pygame independent GL test decorator

Usage:

    from pygamegltest import gltest, pygamewrapper
    @gltest
    def function():
        '''Function that should run under a GL context
        
        Size will be (300,300) and title will be the name of the 
        function passed in.
        '''
        return None
    
    @pygamewrapper( size=(640,480), name='Cool Test' )
    def function():
        '''Function that should run under specially configure context'''
        return None

Will create a new Pygame OpenGL context and let you run the function 
in that context. Each invocation gets a new context, so you should 
not use this for large test suites.
"""
import pygame, pygame.display
from functools import wraps

SCREEN = None
def pygametest( size=(300,300), name=None ):
    def gltest( function ):
        """Decorator to allow a function to run in a Pygame OpenGL context"""
        @wraps( function )
        def test_function( *args, **named ):
            global SCREEN
            pygame.display.init()
            SCREEN = pygame.display.set_mode(
                size,
                pygame.OPENGL | pygame.DOUBLEBUF,
            )
            pygame.display.set_caption(name or function.__name__)
            pygame.key.set_repeat(500,30)
            try:
                return function(*args, **named)
            finally:
                pygame.display.quit()
                pygame.quit()
        return test_function
    return gltest 

gltest = pygametest()
