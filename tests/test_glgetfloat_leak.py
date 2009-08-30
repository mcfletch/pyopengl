#!/usr/bin/python

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def main():
    pygame.init()
    pygame.display.set_mode((800,600), pygame.OPENGL|
        pygame.DOUBLEBUF)
    glClearColor(1.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

    done = False

    while not done:
        for i in range(0,50000):
            modelview_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
            if not i % 500:
                print '.',
        print
        pygame.display.flip()

        eventlist = pygame.event.get()
        for event in eventlist:
            if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                done = True

if __name__ == '__main__':
    main()