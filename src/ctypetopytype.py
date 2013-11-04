"""Utility function to convert a C type to a PyOpenGL-specific data-type name"""
import logging 
log = logging.getLogger( __name__ )

CTYPE_TO_ARRAY_TYPE = {
    '_cs.GLfloat': 'GLfloatArray',
    '_cs.float': 'GLfloatArray',
    '_cs.GLclampf': 'GLclampfArray',
    '_cs.GLdouble': 'GLdoubleArray',
    '_cs.double': 'GLdoubleArray',
    '_cs.int': 'GLintArray',
    '_cs.GLint': 'GLintArray',
    '_cs.GLuint': 'GLuintArray',
    '_cs.unsigned int':'GLuintArray',
    '_cs.unsigned char': 'GLbyteArray',
    '_cs.uint': 'GLuintArray',
    '_cs.GLshort': 'GLshortArray',
    '_cs.GLushort': 'GLushortArray',
    '_cs.short unsigned int':'GLushortArray',
    '_cs.GLubyte': 'GLubyteArray',
    '_cs.GLbool': 'GLbooleanArray',
    '_cs.GLboolean': 'GLbooleanArray',
    'arrays.GLbooleanArray': 'GLbooleanArray',
    '_cs.GLbyte': 'GLbyteArray',
    '_cs.char': 'GLbyteArray',
    '_cs.gleDouble': 'GLdoubleArray',
    '_cs.GLchar': 'GLcharArray',
    '_cs.GLcharARB': 'GLcharARBArray',
    '_cs.GLhalfNV': 'GLushortArray',
    '_cs.GLhandle': 'GLuintArray',
    '_cs.GLhandleARB': 'GLuintArray',
    '_cs.GLenum': 'GLuintArray',
    # following should all have special sub-classes that enforce dimensions
    '_cs.gleDouble * 4': 'GLdoubleArray',
    '_cs.gleDouble * 3': 'GLdoubleArray',
    '_cs.gleDouble * 2': 'GLdoubleArray',
    '_cs.c_float * 3': 'GLfloatArray',
    '_cs.gleDouble * 3 * 2': 'GLdoubleArray',
    '_cs.GLsizei': 'GLsizeiArray',
    '_cs.GLint64': 'GLint64Array',
    '_cs.GLint64EXT': 'GLint64Array',
    '_cs.GLuint64': 'GLuint64Array',
    '_cs.GLuint64EXT': 'GLuint64Array',
    
    '_cs.EGLint':'GLintArray',
    '_cs.EGLConfig':'GLvoidpArray',
    '_cs.EGLuint64KHR':'GLuint64Array',
    '_cs.EGLNativeDisplayType':'GLvoidpArray',
    '_cs.EGLNativeWindowType': 'GLvoidpArray',
    '_cs.EGLNativePixmapType': 'GLvoidpArray',
    '_cs.EGLTimeKHR': 'GLuint64Array',
}


def ctype_to_pytype( base ):
    """Given a C declared type for an argument/return type, get Python/ctypes version"""
    base = base.strip()
    for strip in ('const','struct'):
        if base.endswith( strip ):
            return ctype_to_pytype( base[:-len(strip)] )
        elif base.startswith( strip ):
            return ctype_to_pytype( base[len(strip):] )
    if base.endswith( '*' ):
        new = ctype_to_pytype( base[:-1] )
        if new == '_cs.GLvoid':
            return 'ctypes.c_void_p'
        elif new == 'ctypes.c_void_p':
            return 'arrays.GLvoidpArray'
        elif new in CTYPE_TO_ARRAY_TYPE:
            return 'arrays.%s'%(CTYPE_TO_ARRAY_TYPE[new])
        elif new in ( 'arrays.GLcharArray','arrays.GLcharARBArray'):
            # can't have a pointer to these...
            return 'ctypes.POINTER( ctypes.POINTER( _cs.GLchar ))'
        elif new in ( '_cs.GLcharARB',):
            return 'ctypes.POINTER( ctypes.c_char_p )'
        else:
            log.debug( 'Unconverted pointer type: %r', new )
            return 'ctypes.POINTER(%s)'%(new)
    else:
        if base == 'int':
            base = 'c_int'
        return '_cs.%s'%(base,)
