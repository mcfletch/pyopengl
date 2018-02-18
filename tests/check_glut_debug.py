"""Test GLUT forward-compatible mode..."""
from __future__ import print_function
import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True
OpenGL.ERROR_CHECKING = True
#OpenGL.USE_ACCELERATE = False
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import time
start = time.time()

from OpenGL.GL.AMD.debug_output import glGetDebugMessageLogAMD
from OpenGL.GL.ARB.debug_output import glGetDebugMessageLogARB
from OpenGL.GL.KHR.debug import glGetDebugMessageLogKHR
from OpenGL.GL.VERSION.GL_4_3 import glGetDebugMessageLog

glGetDebugMessageLog = extensions.alternate(
    glGetDebugMessageLog,
    glGetDebugMessageLogARB,
    glGetDebugMessageLogKHR,
    glGetDebugMessageLogAMD,
)

window = None

def display():
    try:
        glutSetWindow(window);
        glClearColor (0.0, 0.0, (time.time()%1.0)/1.0, 0.0)
        glClear (GL_COLOR_BUFFER_BIT)
        try:
            glGetString( GL_EXTENSIONS )
        except GLError:
            pass 
        else:
            print('Egads, glGetString should not have worked!')
        assert bool( glGenVertexArrays ), "Should have vertex array support in 3.2"
        for message in get_debug_messages():
            print(message)
        glFlush ()
        glutSwapBuffers()
    except Exception:
        glutDestroyWindow( window )
        raise

def get_debug_messages():
    messages = []
    count = glGetIntegerv( GL_DEBUG_LOGGED_MESSAGES )
    max_size = int(glGetIntegerv( GL_MAX_DEBUG_MESSAGE_LENGTH ))
    source = GLenum()
    type = GLenum()
    id = GLenum()
    severity = GLenum()
    length = GLsizei()
    buffer = ctypes.create_string_buffer( max_size )
    for i in range(count):
        result = glGetDebugMessageLog( 1, max_size, source, type, id, severity, length, buffer )
        if result:
            messages.append( {
                'message':buffer[:length.value],
                'type': type.value,
                'id': id.value,
                'severity': severity.value,
                'source': source.value,
            })
    return messages
    assert len(messages), messages

        

size = (250,250)

def reshape( *args ):
    global size 
    size = args
    glViewport( *( (0,0)+args) )
    display()

def printFunction( name ):
    def onevent( *args ):
        print('%s -> %s'%(name, ", ".join( [str(a) for a in args ])))
    return onevent



if __name__ == "__main__":
    import sys
    newArgv = glutInit(sys.argv)
    glutInitContextVersion(3, 1)
    glutInitContextFlags(GLUT_FORWARD_COMPATIBLE|GLUT_DEBUG)
    glutInitContextProfile(GLUT_CORE_PROFILE)
    glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH )

    glutSetOption(
        GLUT_ACTION_ON_WINDOW_CLOSE,
        GLUT_ACTION_GLUTMAINLOOP_RETURNS
    );
    glutInitWindowSize(250, 250)
    glutInitWindowPosition(100, 100)
    window = glutCreateWindow("hello")
    print('window', repr(window))
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
    
    glutMainLoop()
