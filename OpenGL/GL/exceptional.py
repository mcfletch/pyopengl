"""Exceptional cases that need some extra wrapping"""
from OpenGL.platform import GL,GLU,createBaseFunction
from OpenGL import arrays, error, wrapper
from OpenGL.arrays.arraydatatype import GLfloatArray, GLdoubleArray
from OpenGL import constants as data_types
from OpenGL.lazywrapper import lazy
from OpenGL.raw import GL as simple
from OpenGL.raw.GL import constants
from OpenGL.raw.GL import annotations
import OpenGL
from OpenGL import _configflags
import ctypes

__all__ = [
    'glBegin',
    'glCallLists',
    'glColor',
    #'glColorTableParameterfv',
    'glDeleteTextures',
    'glEdgeFlagv',
    'glEnd',
    'glGenTextures',
    'glIndexdv',
    'glIndexfv',
    'glIndexsv',
    'glIndexubv',
    'glMap1d',
    'glMap1f',
    'glMap2d',
    'glMap2f',
    'glMaterial',
    'glRasterPos',
    'glRectfv',
    'glRectiv',
    'glRectsv',
    'glTexGenfv',
    'glTexParameter',
    'glVertex',
    'glAreTexturesResident',
]

glRasterPosDispatch = {
    2: simple.glRasterPos2d,
    3: simple.glRasterPos3d,
    4: simple.glRasterPos4d,
}

if _configflags.ERROR_CHECKING:
    @lazy( simple.glBegin )
    def glBegin( baseFunction, mode ):
        """Begin GL geometry-definition mode, disable automatic error checking"""
        error.onBegin( )
        return baseFunction( mode )
    @lazy( simple.glEnd )
    def glEnd( baseFunction ):
        """Finish GL geometry-definition mode, re-enable automatic error checking"""
        error.onEnd( )
        return baseFunction( )
else:
    glBegin = simple.glBegin
    glEnd = simple.glEnd

@lazy( simple.glDeleteTextures )
def glDeleteTextures( baseFunction, array ):
    """Delete specified set of textures"""
    ptr = arrays.GLuintArray.asArray( array )
    size = arrays.GLuintArray.arraySize( ptr )
    return baseFunction( size, ptr )


def glMap2( baseFunction, arrayType ):
    def glMap2( target, u1, u2, v1, v2, points):
        """glMap2(target, u1, u2, v1, v2, points[][][]) -> None

        This is a completely non-standard signature which doesn't allow for most
        of the funky uses with strides and the like, but it has been like this for
        a very long time...
        """
        ptr = arrayType.asArray( points )
        uorder,vorder,vstride = arrayType.dimensions( ptr )
        ustride = vstride*vorder
        return baseFunction(
            target,
            u1, u2,
            ustride, uorder,
            v1, v2,
            vstride, vorder,
            ptr
        )
    glMap2.__name__ = baseFunction.__name__
    glMap2.baseFunction = baseFunction
    return glMap2
glMap2d = glMap2( simple.glMap2d, arrays.GLdoubleArray )
glMap2f = glMap2( simple.glMap2f, arrays.GLfloatArray )
try:
    del glMap2
except NameError, err:
    pass

def glMap1( baseFunction, arrayType ):
    def glMap1(target,u1,u2,points):
        """glMap1(target, u1, u2, points[][][]) -> None

        This is a completely non-standard signature which doesn't allow for most
        of the funky uses with strides and the like, but it has been like this for
        a very long time...
        """
        ptr = arrayType.asArray( points )
        dims = arrayType.dimensions( ptr )
        uorder = dims[0]
        ustride = dims[1]
        return baseFunction( target, u1,u2,ustride,uorder, ptr )
    glMap1.__name__ == baseFunction.__name__
    glMap1.baseFunction = baseFunction
    return glMap1
glMap1d = glMap1( simple.glMap1d, arrays.GLdoubleArray )
glMap1f = glMap1( simple.glMap1f, arrays.GLfloatArray )
try:
    del glMap1
except NameError, err:
    pass

def glRasterPos( *args ):
    """Choose glRasterPosX based on number of args"""
    if len(args) == 1:
        # v form...
        args = args[0]
    return glRasterPosDispatch[ len(args) ]( *args )

glVertexDispatch = {
    2: simple.glVertex2d,
    3: simple.glVertex3d,
    4: simple.glVertex4d,
}
def glVertex( *args ):
    """Choose glVertexX based on number of args"""
    if len(args) == 1:
        # v form...
        args = args[0]
    return glVertexDispatch[ len(args) ]( *args )

@lazy( simple.glCallLists )
def glCallLists( baseFunction, lists, *args ):
    """glCallLists( str( lists ) or lists[] ) -> None

    Restricted version of glCallLists, takes a string or a GLuint compatible
    array data-type and passes into the base function.
    """
    if not len(args):
        if isinstance( lists, str ):
            return baseFunction(
                len(lists),
                constants.GL_UNSIGNED_BYTE,
                ctypes.c_void_p(arrays.GLubyteArray.dataPointer( lists )),
            )
        ptr = arrays.GLuintArray.asArray( lists )
        size = arrays.GLuintArray.arraySize( ptr )
        return baseFunction(
            size,
            constants.GL_UNSIGNED_INT,
            ctypes.c_void_p( arrays.GLuintArray.dataPointer(ptr))
        )
    return baseFunction( lists, *args )

def glTexParameter( target, pname, parameter ):
    """Set a texture parameter, choose underlying call based on pname and parameter"""
    if isinstance( parameter, float ):
        return simple.glTexParameterf( target, pname, parameter )
    elif isinstance( parameter, int ):
        return simple.glTexParameteri( target, pname, parameter )
    else:
        value = GLfloatArray.asArray( parameter, constants.GL_FLOAT )
        return simple.glTexParameterfv( target, pname, value )

@lazy( simple.glGenTextures )
def glGenTextures( baseFunction, count, textures=None ):
    """Generate count new texture names

    Note: for compatibility with PyOpenGL 2.x and below,
    a count of 1 will return a single integer, rather than
    an array of integers.
    """
    if count <= 0:
        raise ValueError( """Can't generate 0 or fewer textures""" )
    elif count == 1 and _configflags.SIZE_1_ARRAY_UNPACK:
        # this traditionally returned a single int/long, so we'll continue to
        # do so, even though it would be easier not to bother.
        textures = simple.GLuint( 0 )
        baseFunction( count, textures)
        return textures.value
    else:
        textures = arrays.GLuintArray.zeros( (count,))
        baseFunction( count, textures)
        return textures

def glMaterial( faces, constant, *args ):
    """glMaterial -- convenience function to dispatch on argument type

    If passed a single argument in args, calls:
        glMaterialfv( faces, constant, args[0] )
    else calls:
        glMaterialf( faces, constant, *args )
    """
    if len(args) == 1:
        arg = GLfloatArray.asArray( args[0] )
        if arg is None:
            raise ValueError( """Null value in glMaterial: %s"""%(args,) )
        return simple.glMaterialfv( faces, constant, arg )
    else:
        return simple.glMaterialf( faces, constant, *args )

glColorDispatch = {
    3: annotations.glColor3fv,
    4: annotations.glColor4fv,
}

def glColor( *args ):
    """glColor*f* -- convenience function to dispatch on argument type

    dispatches to glColor3f, glColor2f, glColor4f, glColor3f, glColor2f, glColor4f
    depending on the arguments passed...
    """
    arglen = len(args)
    if arglen == 1:
        arg = arrays.GLfloatArray.asArray( args[0] )
        function = glColorDispatch[arrays.GLfloatArray.arraySize( arg )]
        return function( arg )
    elif arglen == 2:
        return simple.glColor2d( *args )
    elif arglen == 3:
        return simple.glColor3d( *args )
    elif arglen == 4:
        return simple.glColor4d( *args )
    else:
        raise ValueError( """Don't know how to handle arguments: %s"""%(args,))


# Rectagle coordinates,
glRectfv = arrays.setInputArraySizeType(
    arrays.setInputArraySizeType(
        simple.glRectfv,
        2,
        arrays.GLfloatArray,
        'v1',
    ),
    2,
    arrays.GLfloatArray,
    'v2',
)
glRectiv = arrays.setInputArraySizeType(
    arrays.setInputArraySizeType(
        simple.glRectiv,
        2,
        arrays.GLintArray,
        'v1',
    ),
    2,
    arrays.GLintArray,
    'v2',
)
glRectsv = arrays.setInputArraySizeType(
    arrays.setInputArraySizeType(
        simple.glRectsv,
        2,
        arrays.GLshortArray,
        'v1',
    ),
    2,
    arrays.GLshortArray,
    'v2',
)


glIndexsv = arrays.setInputArraySizeType(
    simple.glIndexsv,
    1,
    arrays.GLshortArray,
    'c',
)
glIndexdv = arrays.setInputArraySizeType(
    simple.glIndexdv,
    1,
    arrays.GLdoubleArray,
    'c',
)
glIndexfv = arrays.setInputArraySizeType(
    simple.glIndexfv,
    1,
    arrays.GLfloatArray,
    'c',
)
glIndexubv = arrays.setInputArraySizeType(
    simple.glIndexubv,
    1,
    arrays.GLbyteArray,
    'c',
)
glEdgeFlagv = arrays.setInputArraySizeType(
    simple.glEdgeFlagv,
    1,
    arrays.GLubyteArray,
    'flag',
)
glTexGenfv = arrays.setInputArraySizeType(
    simple.glTexGenfv,
    None,
    arrays.GLfloatArray,
    'params',
)

#'glAreTexturesResident',
@lazy( simple.glAreTexturesResident )
def glAreTexturesResident( baseFunction, *args ):
    """Allow both Pythonic and C-style calls to glAreTexturesResident

        glAreTexturesResident( arrays.GLuintArray( textures) )

    or

        glAreTexturesResident( int(n), arrays.GLuintArray( textures), arrays.GLuboolean( output) )

    or

        glAreTexturesResident( int(n), arrays.GLuintArray( textures) )

    returns the output arrays.GLubooleanArray
    """
    if len(args) == 1:
        # Pythonic form...
        textures = args[0]
        textures = arrays.GLuintArray.asArray( textures )
        n = arrays.GLuintArray.arraySize(textures)
        output = arrays.GLbooleanArray.zeros( (n,))
    elif len(args) == 2:
        try:
            n = int( args[0] )
        except TypeError, err:
            textures = args[0]
            textures = arrays.GLuintArray.asArray( textures )

            n = arrays.GLuintArray.arraySize(textures)
            output = args[1]
            output = arrays.GLbooleanArray.asArray( output )
        else:
            textures = args[1]
            textures = arrays.GLuintArray.asArray( textures )

            output = arrays.GLbooleanArray.zeros( (n,))
    elif len(args) == 3:
        n,textures,output = args
        textures = arrays.GLuintArray.asArray( textures )
        output = arrays.GLbooleanArray.asArray( output )
    else:
        raise TypeError( """Expected 1 to 3 arguments to glAreTexturesResident""" )
    texturePtr = arrays.GLuintArray.typedPointer( textures )
    outputPtr = arrays.GLbooleanArray.typedPointer( output )
    result = baseFunction( n, texturePtr, outputPtr )
    if result:
        # weirdness of the C api, doesn't produce values if all are true
        for i in range(len(output)):
            output[i] = 1
    return output

#glMap2f
#glMap2d
#glMap1f
#glMap1d
#glPixelMapusv
#glTexGenfv
#glLightfv
#glFeedbackBuffer
#glDrawRangeElements
#glSelectBuffer
#glAreTexturesResident
#glPixelMapfv
#glTexGeniv
#glClipPlane
#glTexParameterfv
#glTexParameteriv
#glReadPixels
#glConvolutionParameterfv
#glPolygonStipple
#glFogiv
#glTexEnviv
#glRectdv
#glMaterialiv
#glColorTable
#glColorTableParameteriv
#glIndexiv
#glLightModeliv
#glDrawElements
#glConvolutionFilter1D
#glCallLists
