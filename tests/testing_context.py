import pygame
from pygame.locals import *
import pygame.key
import pygame.display
from OpenGL.GLUT import *


def createPyGameContext():
    """Setup a minimal PyGame context for testing"""
    pygame.display.init()
    screen = pygame.display.set_mode(
        (300,300),
        OPENGL | DOUBLEBUF,
    )
    pygame.display.set_caption("testing")
    pygame.key.set_repeat(500,30)
    return pygame.display

def createGLUTContext():
    """Setup a minimal GLUT context for testing"""
    glutInit( [] )
    glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB )
    glutInitWindowSize(250, 250)
    glutInitWindowPosition(100, 100)
    window = glutCreateWindow("hello")
    return window