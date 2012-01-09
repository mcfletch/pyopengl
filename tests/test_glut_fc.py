"""Test GLUT forward-compatible mode..."""
import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True
OpenGL.ERROR_CHECKING = True
OpenGL.USE_ACCELERATE = False
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GL import shaders
import time
start = time.time()

window = None

def display():
    try:
        glutSetWindow(window);
        glClearColor (0.0, 0.0, (time.time()%1.0)/1.0, 0.0)
        glClear (GL_COLOR_BUFFER_BIT)
        try:
            glGetString( GL_EXTENSIONS )
        except GLError, err:
            pass 
        else:
            print 'Egads, glGetString should not have worked!'
        assert bool( glGenVertexArrays ), "Should have vertex array support in 3.2"
        glFlush ()
        glutSwapBuffers()
    except Exception, err:
        glutDestroyWindow( window )
        raise

size = (250,250)

def reshape( *args ):
    global size 
    size = args
    glViewport( *( (0,0)+args) )
    display()

def ontimer( *args ):
#    print 'timer', args, '@time', time.time()-start
    glutTimerFunc( 1000, ontimer, 24 )

def idle():
    delta = time.time()-start
    if delta < 10:
        global size 
        x,y = size 
        if delta < 5:
            change = +1
        else:
            change = -1
        x = x-change
        y = y+change
        if x < 1:
            x = 1
        if y < 1:
            y = 1
        glutReshapeWindow( x, y )
        size = (x,y)
        glutSetWindow(window)
        glutPostRedisplay()
    else:
        glutDestroyWindow( window )
        print 'window destroyed'
        import sys
        sys.exit( 0 )

def printFunction( name ):
    def onevent( *args ):
        print '%s -> %s'%(name, ", ".join( [str(a) for a in args ]))
    return onevent



if __name__ == "__main__":
    import sys
    newArgv = glutInit(sys.argv)
    glutInitContextVersion(3, 2)
    glutInitContextFlags(GLUT_FORWARD_COMPATIBLE)
    glutInitContextProfile(GLUT_CORE_PROFILE)
    glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH )

    glutSetOption(
        GLUT_ACTION_ON_WINDOW_CLOSE,
        GLUT_ACTION_GLUTMAINLOOP_RETURNS
    );
    
    print glGetString( GL_EXTENSIONS )
    
    glutInitWindowSize(250, 250)
    glutInitWindowPosition(100, 100)
    window = glutCreateWindow("hello")
    print 'window', repr(window)
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(printFunction( 'Mouse' ))
    glutEntryFunc(printFunction( 'Entry' ))
    glutKeyboardFunc( printFunction( 'Keyboard' ))
    glutKeyboardUpFunc( printFunction( 'KeyboardUp' ))
    glutMotionFunc( printFunction( 'Motion' ))
    glutPassiveMotionFunc( printFunction( 'PassiveMotion' ))
    glutVisibilityFunc( printFunction( 'Visibility' ))
    glutWindowStatusFunc( printFunction( 'WindowStatus' ))
    glutSpecialFunc( printFunction( 'Special' ))
    glutSpecialUpFunc( printFunction( 'SpecialUp' ))
    glutTimerFunc( 1000, ontimer, 23 )
    
    glutIdleFunc( idle )
    glutMainLoop()
