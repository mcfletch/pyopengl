import ctypes
try:
    from ctypes.util import find_library
except ImportError, err:
    from ctypes.util import findLib 
    def find_library( string ):
        return findLib( string )[0]

GL = OpenGL = ctypes.CDLL( find_library('GL'), mode=ctypes.RTLD_GLOBAL )
GLU = ctypes.CDLL( find_library('GLU'), mode=ctypes.RTLD_GLOBAL )
# glut shouldn't need to be global IIUC
GLUT = ctypes.CDLL( find_library('glut'), mode=ctypes.RTLD_GLOBAL )
print 'GL', GL
print 'GLU', GLU
print 'GLUT', GLUT
print GLUT.glutSolidTeapot