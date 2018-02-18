#! /usr/bin/env python
"""Test that GLUT.glutInit accepts 0 arguments"""
from __future__ import print_function
from OpenGL import GLUT

if __name__ == "__main__":
    try:
        GLUT.glutInit()
    except Exception as err:
        raise
    else:
        print('accepted 0 arguments, as desired')
        try:
            if fgDeinitialize: fgDeinitialize(False)
        except NameError as err:
            pass # Older PyOpenGL, you may see a seg-fault here...
    
