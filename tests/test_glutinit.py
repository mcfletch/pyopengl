from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time

resX,resY = (400,300 )

def display( ):
    glutSetWindow(window);
    glClearColor (0.0, 0.0, (time.time()%1.0)/1.0, 0.0)
    glClear (GL_COLOR_BUFFER_BIT)
    glFlush ()
    glutSwapBuffers()


if __name__ == "__main__":
    glutInit([])
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

    glutInitWindowSize(resX, resY)

    glutInitWindowPosition(0, 0)
    window = glutCreateWindow("hello")
    glutDisplayFunc(display)
    for name in (GL_VENDOR,GL_RENDERER,GL_SHADING_LANGUAGE_VERSION,GL_EXTENSIONS):
        print name,glGetString(name)
    
    glutMainLoop()
    
