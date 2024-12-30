#!/usr/bin/python
from __future__ import print_function
import sys, os
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import psutil


def main():
    pygame.init()
    pygame.display.set_mode((800, 600), pygame.OPENGL | pygame.DOUBLEBUF)
    glClearColor(1.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    done = False

    while not done:
        mem = 0
        for i in range(0, 500):
            if i == 10:
                mem = psutil.Process(os.getpid()).memory_percent()
            if i > 400:
                new_mem = psutil.Process(os.getpid()).memory_percent()
                assert new_mem == mem
                break

            modelview_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
            assert modelview_matrix is not None
        break
    sys.stdout.write('OK\n')
    sys.stdout.flush()


if __name__ == '__main__':
    main()
