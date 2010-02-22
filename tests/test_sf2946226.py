import pygame, sys
from pygame.locals import *
import OpenGL
OpenGL.USE_ACCELERATE = False
from OpenGL.GL import *
from OpenGL.GL.EXT.framebuffer_object import *
from OpenGL.platform import safeGetError
from OpenGL import error

def draw ():
    glClearColor(0.0,0.0,0.0,0.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    #draw stuff here
    pygame.display.flip()

pygame.init()
pygame.display.set_mode((512,512),OPENGL | DOUBLEBUF)

#setup a texture
tex = glGenTextures(1);
glBindTexture(GL_TEXTURE_2D, tex);
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, 512, 512, 0, GL_RGBA,
GL_UNSIGNED_BYTE, None);
glBindTexture(GL_TEXTURE_2D, 0);

#setup teh fbo
fbo = glGenFramebuffersEXT(1)
glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fbo)
glBindTexture(GL_TEXTURE_2D, tex)

#this call produces an error!

glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT,
GL_COLOR_ATTACHMENT0_EXT,GL_TEXTURE_2D, tex, 0)

while 1:
    event=pygame.event.poll ()
    if event.type is QUIT:
        sys.exit(0)
    draw()
