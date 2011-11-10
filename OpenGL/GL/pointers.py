"""Implementations for "held-pointers" of various types

This argument type is special because it is stored, that is, it
needs to be cached on our side so that the memory address does not
go out-of-scope

storedPointers = {}
def glVertexPointerd( array ):
    "Natural writing of glVertexPointerd using standard ctypes"
    arg2 = GL_DOUBLE
    arg3 = 0 # stride
    arg4 = arrays.asArray(array, GL_DOUBLE)
    arg1 = arrays.arraySize( arg4, 'd' )
    platform.OpenGL.glVertexPointer( arg1, arg2, arg3, arrays.ArrayDatatype.dataPointer(arg4) )
    glCheckError()
    # only store if we successfully set the value...
    storedPointers[ GL_VERTEX_ARRAY ] = arg4
    return arg4
"""
from OpenGL import platform, arrays, error, wrapper, contextdata, converters, constant
from OpenGL.raw import GL as simple
from OpenGL.raw.GL import annotations
import ctypes
import weakref

GLsizei = ctypes.c_int
GLenum = ctypes.c_uint
GLint = ctypes.c_int
# OpenGL-ctypes variables that mimic OpenGL constant operation...
GL_INTERLEAVED_ARRAY_POINTER = constant.Constant( 'GL_INTERLEAVED_ARRAY_POINTER', -32910 )

__all__ = (
    'glColorPointer',
    'glColorPointerb','glColorPointerd','glColorPointerf','glColorPointeri',
    'glColorPointers','glColorPointerub','glColorPointerui','glColorPointerus',
    'glEdgeFlagPointer',
    'glEdgeFlagPointerb',
    'glIndexPointer',
    'glIndexPointerb','glIndexPointerd','glIndexPointerf',
    'glIndexPointeri','glIndexPointers','glIndexPointerub',
    'glNormalPointer',
    'glNormalPointerb',
    'glNormalPointerd','glNormalPointerf','glNormalPointeri','glNormalPointers',
    'glTexCoordPointer',
    'glTexCoordPointerb','glTexCoordPointerd','glTexCoordPointerf',
    'glTexCoordPointeri','glTexCoordPointers',
    'glVertexPointer',
    'glVertexPointerb','glVertexPointerd','glVertexPointerf','glVertexPointeri',
    'glVertexPointers',
    'glDrawElements','glDrawElementsui','glDrawElementsub','glDrawElementsus',
    'glFeedbackBuffer',
    'glSelectBuffer',
    'glRenderMode',
    'glGetPointerv',
    'glInterleavedArrays',
    'GL_INTERLEAVED_ARRAY_POINTER',
)


# Have to create *new* ctypes wrappers for the platform object!
# We can't just alter the default one since we have different ways of
# calling it

POINTER_FUNCTION_DATA = [
    ('glColorPointerd',  simple.glColorPointer, simple.GL_DOUBLE, simple.GL_COLOR_ARRAY_POINTER, 0, 3),
    ('glColorPointerf',  simple.glColorPointer, simple.GL_FLOAT, simple.GL_COLOR_ARRAY_POINTER, 0, 3),
    ('glColorPointeri',  simple.glColorPointer, simple.GL_INT, simple.GL_COLOR_ARRAY_POINTER, 0, 3),
    ('glColorPointers',  simple.glColorPointer, simple.GL_SHORT, simple.GL_COLOR_ARRAY_POINTER, 0, 3),
    ('glColorPointerub', simple.glColorPointer, simple.GL_UNSIGNED_BYTE, simple.GL_COLOR_ARRAY_POINTER, 0, 3),
    # these data-types are mapped from diff Numeric types
    ('glColorPointerb',  simple.glColorPointer, simple.GL_BYTE, simple.GL_COLOR_ARRAY_POINTER, 0, 3),
    ('glColorPointerui', simple.glColorPointer, simple.GL_UNSIGNED_INT, simple.GL_COLOR_ARRAY_POINTER, 0, 3),
    ('glColorPointerus', simple.glColorPointer, simple.GL_UNSIGNED_SHORT, simple.GL_COLOR_ARRAY_POINTER, 0, 3),

    ('glEdgeFlagPointerb', simple.glEdgeFlagPointer, simple.GL_BYTE, simple.GL_EDGE_FLAG_ARRAY_POINTER, 2, None),

    ('glIndexPointerd',  simple.glIndexPointer, simple.GL_DOUBLE, simple.GL_INDEX_ARRAY_POINTER, 1, None),
    ('glIndexPointerf',  simple.glIndexPointer, simple.GL_FLOAT, simple.GL_INDEX_ARRAY_POINTER, 1, None),
    ('glIndexPointeri',  simple.glIndexPointer, simple.GL_INT, simple.GL_INDEX_ARRAY_POINTER, 1, None),
    ('glIndexPointerub', simple.glIndexPointer, simple.GL_UNSIGNED_BYTE, simple.GL_INDEX_ARRAY_POINTER, 1, None),
    ('glIndexPointers',  simple.glIndexPointer, simple.GL_SHORT, simple.GL_INDEX_ARRAY_POINTER, 1, None),
    # these data-types are mapped from diff Numeric types
    ('glIndexPointerb',  simple.glIndexPointer, simple.GL_BYTE, simple.GL_INDEX_ARRAY_POINTER, 1, None),

    ('glNormalPointerd',  simple.glNormalPointer, simple.GL_DOUBLE, simple.GL_NORMAL_ARRAY_POINTER, 1, None),
    ('glNormalPointerf',  simple.glNormalPointer, simple.GL_FLOAT, simple.GL_NORMAL_ARRAY_POINTER, 1, None),
    ('glNormalPointeri',  simple.glNormalPointer, simple.GL_INT, simple.GL_NORMAL_ARRAY_POINTER, 1, None),
    ('glNormalPointerb',  simple.glNormalPointer, simple.GL_BYTE, simple.GL_NORMAL_ARRAY_POINTER, 1, None),
    ('glNormalPointers',  simple.glNormalPointer, simple.GL_SHORT, simple.GL_NORMAL_ARRAY_POINTER, 1, None),

    ('glTexCoordPointerd',  simple.glTexCoordPointer, simple.GL_DOUBLE, simple.GL_TEXTURE_COORD_ARRAY_POINTER, 0, 2),
    ('glTexCoordPointerf',  simple.glTexCoordPointer, simple.GL_FLOAT, simple.GL_TEXTURE_COORD_ARRAY_POINTER, 0, 2),
    ('glTexCoordPointeri',  simple.glTexCoordPointer, simple.GL_INT, simple.GL_TEXTURE_COORD_ARRAY_POINTER, 0, 2),
    ('glTexCoordPointerb',  simple.glTexCoordPointer, simple.GL_BYTE, simple.GL_TEXTURE_COORD_ARRAY_POINTER, 0, 2),
    ('glTexCoordPointers',  simple.glTexCoordPointer, simple.GL_SHORT, simple.GL_TEXTURE_COORD_ARRAY_POINTER, 0, 2),

    ('glVertexPointerd', simple.glVertexPointer, simple.GL_DOUBLE, simple.GL_VERTEX_ARRAY_POINTER, 0, 3),
    ('glVertexPointerf', simple.glVertexPointer, simple.GL_FLOAT, simple.GL_VERTEX_ARRAY_POINTER, 0, 3),
    ('glVertexPointeri', simple.glVertexPointer, simple.GL_INT, simple.GL_VERTEX_ARRAY_POINTER, 0, 3),
    ('glVertexPointerb', simple.glVertexPointer, simple.GL_INT, simple.GL_VERTEX_ARRAY_POINTER, 0, 3),
    ('glVertexPointers', simple.glVertexPointer, simple.GL_SHORT, simple.GL_VERTEX_ARRAY_POINTER, 0, 3),
]
def wrapPointerFunction( name, baseFunction, glType, arrayType,startArgs, defaultSize ):
    """Wrap the given pointer-setting function"""
    function= wrapper.wrapper( baseFunction )
    assert not getattr( function, 'pyConverters', None ), """Reusing wrappers?"""
    if arrayType:
        arrayModuleType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[ glType ]
        function.setPyConverter( 'pointer', arrays.asArrayType(arrayModuleType) )
    else:
        function.setPyConverter( 'pointer', arrays.AsArrayOfType('pointer','type') )
    function.setCConverter( 'pointer', converters.getPyArgsName( 'pointer' ) )
    if 'size' in function.argNames:
        function.setPyConverter( 'size' )
        function.setCConverter( 'size', arrays.arraySizeOfFirstType(arrayModuleType,defaultSize) )
    if 'type' in function.argNames:
        function.setPyConverter( 'type' )
        function.setCConverter( 'type', glType )
    if 'stride' in function.argNames:
        function.setPyConverter( 'stride' )
        function.setCConverter( 'stride', 0 )
    function.setStoreValues( arrays.storePointerType( 'pointer', arrayType ) )
    function.setReturnValues( wrapper.returnPyArgument( 'pointer' ) )
    return name,function



for name,function in [
    wrapPointerFunction( *args )
    for args in POINTER_FUNCTION_DATA
]:
    globals()[name] = function
try:
    del name, function
except NameError, err:
    pass

glVertexPointer = wrapper.wrapper( simple.glVertexPointer ).setPyConverter(
    'pointer', arrays.AsArrayOfType( 'pointer', 'type' ),
).setStoreValues(
    arrays.storePointerType( 'pointer', simple.GL_VERTEX_ARRAY_POINTER )
).setReturnValues(
    wrapper.returnPyArgument( 'pointer' )
)
glTexCoordPointer = wrapper.wrapper( simple.glTexCoordPointer ).setPyConverter(
    'pointer', arrays.AsArrayOfType( 'pointer', 'type' ),
).setStoreValues(
    arrays.storePointerType( 'pointer', simple.GL_TEXTURE_COORD_ARRAY_POINTER )
).setReturnValues(
    wrapper.returnPyArgument( 'pointer' )
)
glNormalPointer = wrapper.wrapper( simple.glNormalPointer ).setPyConverter(
    'pointer', arrays.AsArrayOfType( 'pointer', 'type' ),
).setStoreValues(
    arrays.storePointerType( 'pointer', simple.GL_NORMAL_ARRAY_POINTER )
).setReturnValues(
    wrapper.returnPyArgument( 'pointer' )
)
glIndexPointer = wrapper.wrapper( simple.glIndexPointer ).setPyConverter(
    'pointer', arrays.AsArrayOfType( 'pointer', 'type' ),
).setStoreValues(
    arrays.storePointerType( 'pointer', simple.GL_INDEX_ARRAY_POINTER )
).setReturnValues(
    wrapper.returnPyArgument( 'pointer' )
)
glEdgeFlagPointer = wrapper.wrapper( simple.glEdgeFlagPointer ).setPyConverter(
    # XXX type is wrong!
    'pointer', arrays.AsArrayTyped( 'pointer', arrays.GLushortArray ),
).setStoreValues(
    arrays.storePointerType( 'pointer', simple.GL_EDGE_FLAG_ARRAY_POINTER )
).setReturnValues(
    wrapper.returnPyArgument( 'pointer' )
)
glColorPointer = wrapper.wrapper( simple.glColorPointer ).setPyConverter(
    'pointer', arrays.AsArrayOfType( 'pointer', 'type' ),
).setStoreValues(
    arrays.storePointerType( 'pointer', simple.GL_COLOR_ARRAY_POINTER )
).setReturnValues(
    wrapper.returnPyArgument( 'pointer' )
)
glInterleavedArrays = wrapper.wrapper( simple.glInterleavedArrays ).setStoreValues(
    arrays.storePointerType( 'pointer', GL_INTERLEAVED_ARRAY_POINTER )
).setReturnValues(
    wrapper.returnPyArgument( 'pointer' )
)


glDrawElements = wrapper.wrapper( simple.glDrawElements ).setPyConverter(
    'indices', arrays.AsArrayOfType( 'indices', 'type' ),
).setReturnValues(
    wrapper.returnPyArgument( 'indices' )
)

def glDrawElementsTyped( type, suffix ):
    arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[ type ]
    function = wrapper.wrapper(
        simple.glDrawElements
    ).setPyConverter('type').setCConverter(
        'type', type
    ).setPyConverter('count').setCConverter(
        'count', arrays.AsArrayTypedSize( 'indices', arrayType ),
    ).setPyConverter(
        'indices', arrays.AsArrayTyped( 'indices', arrayType ),
    ).setReturnValues(
        wrapper.returnPyArgument( 'indices' )
    )
    return function
for type,suffix in ((simple.GL_UNSIGNED_BYTE,'ub'),(simple.GL_UNSIGNED_INT,'ui'),(simple.GL_UNSIGNED_SHORT,'us')):
    globals()['glDrawElements%(suffix)s'%globals()] = glDrawElementsTyped( type,suffix )
try:
    del type,suffix,glDrawElementsTyped
except NameError, err:
    pass

# create buffer of given size and return it for future reference
# keep a per-context weakref around to allow us to return the original
# array we returned IFF the user has kept a reference as well...
def glSelectBuffer( size, buffer = None ):
    """Create a selection buffer of the given size
    """
    if buffer is None:
        buffer = arrays.GLuintArray.zeros( (size,) )
    simple.glSelectBuffer( size, buffer )
    contextdata.setValue( simple.GL_SELECTION_BUFFER_POINTER, buffer )
    return buffer
def glFeedbackBuffer( size, type, buffer = None ):
    """Create a selection buffer of the given size
    """
    if buffer is None:
        buffer = arrays.GLfloatArray.zeros( (size,) )
    simple.glFeedbackBuffer( size, type, buffer )
    contextdata.setValue( simple.GL_FEEDBACK_BUFFER_POINTER, buffer )
    contextdata.setValue( "GL_FEEDBACK_BUFFER_TYPE", type )
    return buffer

def glRenderMode( newMode ):
    """Change to the given rendering mode

    If the current mode is GL_FEEDBACK or GL_SELECT, return
    the current buffer appropriate to the mode
    """
    # must get the current mode to determine operation...
    from OpenGL.GL import glGetIntegerv
    from OpenGL.GL import selection, feedback
    currentMode = glGetIntegerv( simple.GL_RENDER_MODE )
    try:
        currentMode = currentMode[0]
    except (TypeError,ValueError,IndexError), err:
        pass
    if currentMode in (simple.GL_RENDER,0):
        # no array needs to be returned...
        return simple.glRenderMode( newMode )
    result = simple.glRenderMode( newMode )
    # result is now an integer telling us how many elements were copied...

    if result < 0:
        if currentMode == simple.GL_SELECT:
            raise error.GLError(
                simple.GL_STACK_OVERFLOW,
                "glSelectBuffer too small to hold selection results",
            )
        elif currentMode == simple.GL_FEEDBACK:
            raise error.GLError(
                simple.GL_STACK_OVERFLOW,
                "glFeedbackBuffer too small to hold selection results",
            )
        else:
            raise error.GLError(
                simple.GL_STACK_OVERFLOW,
                "Unknown glRenderMode buffer (%s) too small to hold selection results"%(
                    currentMode,
                ),
            )
    # Okay, now that the easy cases are out of the way...
    #  Do we have a pre-stored pointer about which the user already knows?
    context = platform.GetCurrentContext()
    if context == 0:
        raise error.Error(
            """Returning from glRenderMode without a valid context!"""
        )
    arrayConstant, wrapperFunction = {
        simple.GL_FEEDBACK: (simple.GL_FEEDBACK_BUFFER_POINTER,feedback.parseFeedback),
        simple.GL_SELECT: (simple.GL_SELECTION_BUFFER_POINTER, selection.GLSelectRecord.fromArray),
    }[ currentMode ]
    current = contextdata.getValue( arrayConstant )
    # XXX check to see if it's the *same* array we set currently!
    if current is None:
        current = glGetPointerv( arrayConstant )
    # XXX now, can turn the array into the appropriate wrapper type...
    if wrapperFunction:
        current = wrapperFunction( current, result )
    return current

# XXX this belongs in the GL module, not here!
def glGetPointerv( constant ):
    """Retrieve a stored pointer constant"""
    # do we have a cached version of the pointer?
    # get the base pointer from the underlying operation
    vp = ctypes.voidp()
    simple.glGetPointerv( constant, ctypes.byref(vp) )
    current = contextdata.getValue( constant )
    if current is not None:
        if arrays.ArrayDatatype.dataPointer( current ) == vp.value:
            return current
    # XXX should be coercing to the proper type and converting to an array
    return vp
