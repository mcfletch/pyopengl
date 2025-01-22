from __future__ import print_function
import sys
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.extensions import alternate
from OpenGL.GL.ARB.draw_instanced import *
from OpenGL.GL.EXT.draw_instanced import *


def detect():
    glutInit([])
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(200, 200)

    glutCreateWindow("Detection")

    functions = (
        glDrawArraysInstanced,
        glDrawArraysInstancedARB,
        glDrawArraysInstancedEXT,
        # glDrawArraysInstancedNV, is GLES only
    )

    for function in functions:
        print(function.__name__, bool(function))

    any = alternate(*functions)

    print(any, bool(any))
    sys.stdout.write('OK\n')
    sys.stdout.flush()
    try:
        if fgDeinitialize:
            fgDeinitialize(False)
    except NameError:
        pass  # Older PyOpenGL, you may see a seg-fault here...


if __name__ == "__main__":
    detect()
