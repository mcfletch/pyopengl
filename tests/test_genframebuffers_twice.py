#! /usr/bin/env python
"""Test for glGenFramebuffersEXT multiple-call failure reported by Joshua Davis"""
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
# adapted from http://www.pygame.org/wiki/GLSLExample
from OpenGL.GL.EXT.framebuffer_object import *
def main():
    glutInit(0)
    glutInitDisplayMode(GLUT_RGB|GLUT_DOUBLE|GLUT_DEPTH)
    glutCreateWindow('test')
    framebuffer = glGenFramebuffersEXT(1)
    print type(framebuffer)
    cow = glGenFramebuffersEXT(1)
    print cow
    glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, framebuffer)

if __name__ == "__main__":
    main()
    