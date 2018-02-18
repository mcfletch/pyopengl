from __future__ import print_function
from OpenGL.GL import *
from OpenGL.GLUT import *
import sys
import OpenGL.GL.EXT.framebuffer_object as EXT
import OpenGL.GL.ARB.framebuffer_object as ARB

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)	
    glutInitWindowSize(640, 480)	
    glutInitWindowPosition(0, 0)	
    glutCreateWindow("Framebuffer bug demo")

    for i in range( 200 ):
        fbo = EXT.glGenFramebuffersEXT(1)
        print("FBO = ", fbo)
        EXT.glDeleteFramebuffersEXT (int(fbo))
        fbo = ARB.glGenFramebuffers(1)
        print("FBO = ", fbo)
        ARB.glDeleteFramebuffers(int(fbo))
        glFlush()
    try:
        if fgDeinitialize: fgDeinitialize(False)
    except NameError:
        pass # Older PyOpenGL, you may see a seg-fault here...

# Print message to console, and kick off the main to get it rolling.
if __name__ == "__main__":
    main()
        
