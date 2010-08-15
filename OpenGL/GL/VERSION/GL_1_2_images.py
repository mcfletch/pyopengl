"""Version 1.2 Image-handling functions

Almost all of the 1.2 enhancements are image-handling-related,
so this is, most of the 1.2 wrapper code...

Note that the functions that manually wrap certain operations are
guarded by if simple.functionName checks, so that you can use
if functionName to see if the function is available at run-time.
"""
from OpenGL import wrapper, constants, arrays
from OpenGL.lazywrapper import lazy
from OpenGL.raw.GL.VERSION import GL_1_2 as simple
from OpenGL.raw.GL.ARB import imaging
from OpenGL.GL import images
import ctypes

glGetHistogramParameterfv = wrapper.wrapper(simple.glGetHistogramParameterfv).setOutput(
    "params",(1,),
)
glGetHistogramParameteriv = wrapper.wrapper(simple.glGetHistogramParameteriv).setOutput(
    "params",(1,),
)

for suffix,arrayConstant in [
    ('b', constants.GL_BYTE),
    ('f', constants.GL_FLOAT),
    ('i', constants.GL_INT),
    ('s', constants.GL_SHORT),
    ('ub', constants.GL_UNSIGNED_BYTE),
    ('ui', constants.GL_UNSIGNED_INT),
    ('us', constants.GL_UNSIGNED_SHORT),
]:
    for functionName in (
        'glTexImage3D',
        'glTexSubImage3D', # extension/1.2 standard
    ):
        functionName, function = images.typedImageFunction(
            suffix, arrayConstant, getattr(simple, functionName),
        )
        globals()[functionName] = function
        try:
            del function, functionName
        except NameError, err:
            pass
    try:
        del suffix,arrayConstant
    except NameError, err:
        pass

glTexImage3D = images.setDimensionsAsInts(
    images.setImageInput(
        simple.glTexImage3D,
        typeName = 'type',
    )
)
glTexSubImage3D = images.setDimensionsAsInts(
    images.setImageInput(
        simple.glTexSubImage3D,
        typeName = 'type',
    )
)
glColorTable = images.setDimensionsAsInts(
    images.setImageInput(
        simple.glColorTable,
        pixelName = 'table',
        typeName = 'type',
    )
)
glColorSubTable = images.setDimensionsAsInts(
    images.setImageInput(
        simple.glColorSubTable,
        pixelName = 'data',
    )
)
glSeparableFilter2D = images.setDimensionsAsInts(
    images.setImageInput(
        images.setImageInput(
            simple.glSeparableFilter2D,
            pixelName = 'row',
            typeName = 'type',
        ),
        pixelName = 'column',
        typeName = 'type',
    )
)
glConvolutionFilter1D = images.setDimensionsAsInts(
    images.setImageInput(
        simple.glConvolutionFilter1D,
        pixelName = 'image',
        typeName = 'type',
    )
)
glConvolutionFilter2D = images.setDimensionsAsInts(
    images.setImageInput(
        simple.glConvolutionFilter2D,
        pixelName = 'image',
        typeName = 'type',
    )
)
@lazy( simple.glGetConvolutionFilter )
def glGetConvolutionFilter( baseFunction, target, format, type ):
    """Retrieve 1 or 2D convolution parameter "kernels" as pixel data"""
    dims = (
        glGetConvolutionParameteriv( target, imaging.GL_CONVOLUTION_WIDTH )[0],
    )
    if target != imaging.GL_CONVOLUTION_1D:
        dims += (
            glGetConvolutionParameteriv( target, imaging.GL_CONVOLUTION_HEIGHT )[0],
        )
    # is it always 4?  Seems to be, but the spec/man-page isn't really clear about it...
    dims += (4,)
    array = images.images.SetupPixelRead( format, dims, type )
    arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[
        images.images.TYPE_TO_ARRAYTYPE.get(type,type)
    ]
    baseFunction(
        target, format, type,
        ctypes.c_void_p( arrayType.dataPointer(array))
    )
    return array
@lazy( simple.glGetSeparableFilter )
def glGetSeparableFilter( baseFunction, target, format, type ):
    """Retrieve 2 1D convolution parameter "kernels" as pixel data"""
    rowDims = (
        glGetConvolutionParameteriv( imaging.GL_CONVOLUTION_WIDTH )[0],
        4,
    )
    columnDims = (
        glGetConvolutionParameteriv( imaging.GL_CONVOLUTION_HEIGHT )[0],
        4,
    )
    arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[
        images.images.TYPE_TO_ARRAYTYPE.get(type,type)
    ]
    row = images.images.SetupPixelRead( format, rowDims, type )
    column = images.images.SetupPixelRead( format, columnDims, type )
    baseFunction(
        target, format, type,
        ctypes.c_void_p( arrayType.dataPointer(row)),
        ctypes.c_void_p( arrayType.dataPointer(column)),
        None # span
    )
    return row, column
@lazy( simple.glGetColorTable )
def glGetColorTable( baseFunction, target, format, type ):
    """Retrieve the current 1D color table as a bitmap"""
    dims = (
        glGetColorTableParameteriv(target, imaging.GL_COLOR_TABLE_WIDTH),
        4, # Grr, spec *seems* to say that it's different sizes, but it doesn't really say...
    )
    array = images.images.SetupPixelRead( format, dims, type )
    arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[
        images.images.TYPE_TO_ARRAYTYPE.get(type,type)
    ]
    baseFunction(
        target, format, type,
        ctypes.c_void_p( arrayType.dataPointer(array))
    )
    return array
@lazy( simple.glGetHistogram )
def glGetHistogram( baseFunction, target, reset, format, type, values=None):
    """Retrieve current 1D histogram as a 1D bitmap"""
    if values is None:
        width = glGetHistogramParameteriv(
            target,
            imaging.GL_HISTOGRAM_WIDTH,
        )
        values = images.images.SetupPixelRead( format, (width,4), type )
    arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[
        images.images.TYPE_TO_ARRAYTYPE.get(type,type)
    ]
    baseFunction(
        target, reset, format, type,
        ctypes.c_void_p( arrayType.dataPointer(values))
    )
    return values

@lazy( simple.glGetMinmax )
def glGetMinmax( baseFunction, target, reset, format, type, values=None):
    """Retrieve minimum and maximum values as a 2-element image"""
    if values is None:
        width = 2
        values = images.images.SetupPixelRead( format, (width,4), type )
    arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[
        images.images.TYPE_TO_ARRAYTYPE.get(type,type)
    ]
    baseFunction(
        target, reset, format, type,
        ctypes.c_void_p( arrayType.dataPointer(values))
    )
    return values

# 4-items, specified in spec...
glColorTableParameterfv = arrays.setInputArraySizeType(
    simple.glColorTableParameterfv,
    4,
    arrays.GLfloatArray,
    'params',
)
GL_GET_CTP_SIZES = {
    imaging.GL_COLOR_TABLE_FORMAT :1,
    imaging.GL_COLOR_TABLE_WIDTH  :1,
    imaging.GL_COLOR_TABLE_RED_SIZE :1,
    imaging.GL_COLOR_TABLE_GREEN_SIZE :1,
    imaging.GL_COLOR_TABLE_BLUE_SIZE :1,
    imaging.GL_COLOR_TABLE_ALPHA_SIZE :1,
    imaging.GL_COLOR_TABLE_LUMINANCE_SIZE :1,
    imaging.GL_COLOR_TABLE_INTENSITY_SIZE :1,
}
glGetColorTableParameterfv = wrapper.wrapper(simple.glGetColorTableParameterfv).setOutput(
    "params",GL_GET_CTP_SIZES, "pname",
)
glGetColorTableParameteriv = wrapper.wrapper(simple.glGetColorTableParameteriv).setOutput(
    "params",GL_GET_CTP_SIZES, "pname",
)
GL_GET_CP_SIZES = {
    imaging.GL_CONVOLUTION_BORDER_MODE: 1,
    imaging.GL_CONVOLUTION_BORDER_COLOR: 4,
    imaging.GL_CONVOLUTION_FILTER_SCALE: 4,
    imaging.GL_CONVOLUTION_FILTER_BIAS: 4,
    imaging.GL_CONVOLUTION_FORMAT: 1,
    imaging.GL_CONVOLUTION_WIDTH: 1,
    imaging.GL_CONVOLUTION_HEIGHT: 1,
    imaging.GL_MAX_CONVOLUTION_WIDTH: 1,
    imaging.GL_MAX_CONVOLUTION_HEIGHT: 1,
}
glGetConvolutionParameteriv = wrapper.wrapper(simple.glGetConvolutionParameteriv).setOutput(
    "params",GL_GET_CP_SIZES, "pname",
)
glGetConvolutionParameterfv = wrapper.wrapper(simple.glGetConvolutionParameterfv).setOutput(
    "params",GL_GET_CP_SIZES, "pname",
)
