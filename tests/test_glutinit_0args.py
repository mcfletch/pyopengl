#! /usr/bin/env python
"""Test that GLUT.glutInit accepts 0 arguments"""
from OpenGL import GLUT

if __name__ == "__main__":
    try:
        GLUT.glutInit()
    except Exception, err:
        raise
    else:
        print 'accepted 0 arguments, as desired'
    