
if __name__ == "__main__":
    from OpenGL.GLUT import *
    from OpenGL.GL import *
    glutInit( ' ' )
    glutInitDisplayMode( GLUT_SINGLE )
    window = glutCreateWindow("hello")
    glutDisplayFunc( lambda *args: 1 )
    #glutMainLoop()
