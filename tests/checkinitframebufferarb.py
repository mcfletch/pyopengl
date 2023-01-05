import pygame as pg
import OpenGL

OpenGL.setPlatform("wayland")
import OpenGL.GL
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.ARB.framebuffer_object import glInitFramebufferObjectARB


def main():
    pg.init()
    pg.display.set_mode((50, 50), DOUBLEBUF | OPENGL)
    pg.display.init()
    OpenGL.GL.glGetString(OpenGL.GL.GL_VERSION)
    print(glInitFramebufferObjectARB())
    print(OpenGL.__version__)


if __name__ == "__main__":
    main()
