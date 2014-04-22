
if __name__ == "__main__":
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    glutInit( ' ' )
    glutInitDisplayMode( GLUT_SINGLE )
    window = glutCreateWindow("hello")
    glutDisplayFunc( lambda *args: 1 )
    #glutMainLoop()
    try:
        if fgDeinitialize: fgDeinitialize(False)
    except NameError as err:
        pass # Older PyOpenGL, you may see a seg-fault here...
