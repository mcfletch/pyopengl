"""Image-handling routines

### Unresolved:

    Following methods are not yet resolved due to my not being sure how the
    function should be wrapped:

        glCompressedTexImage3D
        glCompressedTexImage2D
        glCompressedTexImage1D
        glCompressedTexSubImage3D
        glCompressedTexSubImage2D
        glCompressedTexSubImage1D
"""
from OpenGL.raw import GL as simple
from OpenGL import images, arrays, wrapper, platform
import ctypes

def asInt( value ):
    if isinstance( value, float ):
        return int(round(value,0))
    return value

## update the image tables with standard image types...
#images.FORMAT_BITS.update( {
#	simple.GL_BITMAP : 1, # must be GL_UNSIGNED_BYTE
#
#	simple.GL_RED : 8,
#	simple.GL_GREEN : 8,
#	simple.GL_BLUE : 8,
#	simple.GL_ALPHA : 8,
#	simple.GL_LUMINANCE : 8,
#	simple.GL_LUMINANCE_ALPHA : 8,
#	simple.GL_COLOR_INDEX : 8,
#	simple.GL_STENCIL_INDEX : 8,
#	simple.GL_DEPTH_COMPONENT : 8,
#	simple.GL_RGB : 24,
#	simple.GL_BGR : 24,
#
#	simple.GL_RGBA : 32,
#	simple.GL_BGRA : 32,
#	simple.GL_ABGR_EXT : 32,
#	simple.GL_CMYK_EXT : 32,
#
#	simple.GL_CMYKA_EXT : 40,
#
#	simple.GL_YCRCB_422_SGIX : 8, # must be GL_UNSIGNED_BYTE
#	simple.GL_YCRCB_444_SGIX : 8, # must be GL_UNSIGNED_SHORT
#
#	simple.GL_FORMAT_SUBSAMPLE_24_24_OML : 32, # must be GL_UNSIGNED_INT_10_10_10_2
#	simple.GL_FORMAT_SUBSAMPLE_244_244_OML : 32, # must be GL_UNSIGNED_INT_10_10_10_2
#} )
images.COMPONENT_COUNTS.update( {
    simple.GL_BITMAP : 1, # must be GL_UNSIGNED_BYTE

    simple.GL_RED : 1,
    simple.GL_GREEN : 1,
    simple.GL_BLUE : 1,
    simple.GL_ALPHA : 1,
    simple.GL_LUMINANCE : 1,
    simple.GL_LUMINANCE_ALPHA : 2,
    simple.GL_COLOR_INDEX : 1,
    simple.GL_STENCIL_INDEX : 1,
    simple.GL_DEPTH_COMPONENT : 1,
    simple.GL_RGB : 3,
    simple.GL_BGR : 3,

    simple.GL_RGBA : 4,
    simple.GL_BGRA : 4,
    simple.GL_ABGR_EXT : 4,
    simple.GL_CMYK_EXT : 4,

    simple.GL_CMYKA_EXT : 5,

    simple.GL_YCRCB_422_SGIX : 1, # must be GL_UNSIGNED_BYTE
    simple.GL_YCRCB_444_SGIX : 1, # must be GL_UNSIGNED_SHORT

    simple.GL_FORMAT_SUBSAMPLE_24_24_OML : 1, # must be GL_UNSIGNED_INT_10_10_10_2
    simple.GL_FORMAT_SUBSAMPLE_244_244_OML : 1, # must be GL_UNSIGNED_INT_10_10_10_2
} )

#images.TYPE_TO_BITS.update( {
#	simple.GL_UNSIGNED_BYTE_3_3_2 : 8,
#	simple.GL_UNSIGNED_BYTE_2_3_3_REV : 8,
#	simple.GL_UNSIGNED_SHORT_4_4_4_4 : 16,
#	simple.GL_UNSIGNED_SHORT_4_4_4_4_REV : 16,
#	simple.GL_UNSIGNED_SHORT_5_5_5_1 : 16,
#	simple.GL_UNSIGNED_SHORT_1_5_5_5_REV : 16,
#	simple.GL_UNSIGNED_SHORT_5_6_5 : 16,
#	simple.GL_UNSIGNED_SHORT_5_6_5_REV : 16,
#	simple.GL_UNSIGNED_INT_8_8_8_8 : 32,
#	simple.GL_UNSIGNED_INT_8_8_8_8_REV : 32,
#	simple.GL_UNSIGNED_INT_10_10_10_2 : 32,
#	simple.GL_UNSIGNED_INT_2_10_10_10_REV : 32,
#	simple.GL_UNSIGNED_BYTE : ctypes.sizeof(simple.GLubyte) * 8,
#	simple.GL_BYTE: ctypes.sizeof(simple.GLbyte) * 8,
#	simple.GL_UNSIGNED_SHORT :  ctypes.sizeof(simple.GLushort) * 8,
#	simple.GL_SHORT :  ctypes.sizeof(simple.GLshort) * 8,
#	simple.GL_UNSIGNED_INT : ctypes.sizeof(simple.GLuint) * 8,
#	simple.GL_INT : ctypes.sizeof(simple.GLint) * 8,
#	simple.GL_FLOAT : ctypes.sizeof(simple.GLfloat) * 8,
#	simple.GL_DOUBLE : ctypes.sizeof(simple.GLdouble) * 8,
#} )
images.TYPE_TO_ARRAYTYPE.update( {
    simple.GL_UNSIGNED_BYTE_3_3_2 : simple.GL_UNSIGNED_BYTE,
    simple.GL_UNSIGNED_BYTE_2_3_3_REV : simple.GL_UNSIGNED_BYTE,
    simple.GL_UNSIGNED_SHORT_4_4_4_4 : simple.GL_UNSIGNED_SHORT,
    simple.GL_UNSIGNED_SHORT_4_4_4_4_REV : simple.GL_UNSIGNED_SHORT,
    simple.GL_UNSIGNED_SHORT_5_5_5_1 : simple.GL_UNSIGNED_SHORT,
    simple.GL_UNSIGNED_SHORT_1_5_5_5_REV : simple.GL_UNSIGNED_SHORT,
    simple.GL_UNSIGNED_SHORT_5_6_5 : simple.GL_UNSIGNED_SHORT,
    simple.GL_UNSIGNED_SHORT_5_6_5_REV : simple.GL_UNSIGNED_SHORT,
    simple.GL_UNSIGNED_INT_8_8_8_8 : simple.GL_UNSIGNED_INT,
    simple.GL_UNSIGNED_INT_8_8_8_8_REV : simple.GL_UNSIGNED_INT,
    simple.GL_UNSIGNED_INT_10_10_10_2 : simple.GL_UNSIGNED_INT,
    simple.GL_UNSIGNED_INT_2_10_10_10_REV : simple.GL_UNSIGNED_INT,
    simple.GL_UNSIGNED_BYTE : simple.GL_UNSIGNED_BYTE,
    simple.GL_BYTE: simple.GL_BYTE,
    simple.GL_UNSIGNED_SHORT : simple.GL_UNSIGNED_SHORT,
    simple.GL_SHORT :  simple.GL_SHORT,
    simple.GL_UNSIGNED_INT : simple.GL_UNSIGNED_INT,
    simple.GL_INT : simple.GL_INT,
    simple.GL_FLOAT : simple.GL_FLOAT,
    simple.GL_DOUBLE : simple.GL_DOUBLE,
    simple.GL_BITMAP : simple.GL_UNSIGNED_BYTE,
} )
images.TIGHT_PACK_FORMATS.update({
    simple.GL_UNSIGNED_BYTE_3_3_2 : 3,
    simple.GL_UNSIGNED_BYTE_2_3_3_REV : 3,
    simple.GL_UNSIGNED_SHORT_4_4_4_4 : 4,
    simple.GL_UNSIGNED_SHORT_4_4_4_4_REV : 4,
    simple.GL_UNSIGNED_SHORT_5_5_5_1 : 4,
    simple.GL_UNSIGNED_SHORT_1_5_5_5_REV : 4,
    simple.GL_UNSIGNED_SHORT_5_6_5 : 3,
    simple.GL_UNSIGNED_SHORT_5_6_5_REV : 3,
    simple.GL_UNSIGNED_INT_8_8_8_8 : 4,
    simple.GL_UNSIGNED_INT_8_8_8_8_REV : 4,
    simple.GL_UNSIGNED_INT_10_10_10_2 : 4,
    simple.GL_UNSIGNED_INT_2_10_10_10_REV : 4,
    simple.GL_BITMAP: 8, # single bits, 8 of them...
})

images.RANK_PACKINGS.update( {
    4: [
        (simple.glPixelStorei,simple.GL_PACK_SKIP_VOLUMES_SGIS, 0),
        (simple.glPixelStorei,simple.GL_PACK_IMAGE_DEPTH_SGIS, 0),
        (simple.glPixelStorei,simple.GL_PACK_ALIGNMENT, 1),
    ],
    3: [
        (simple.glPixelStorei,simple.GL_PACK_SKIP_IMAGES, 0),
        (simple.glPixelStorei,simple.GL_PACK_IMAGE_HEIGHT, 0),
        (simple.glPixelStorei,simple.GL_PACK_ALIGNMENT, 1),
    ],
    2: [
        (simple.glPixelStorei,simple.GL_PACK_ROW_LENGTH, 0),
        (simple.glPixelStorei,simple.GL_PACK_SKIP_ROWS, 0),
        (simple.glPixelStorei,simple.GL_PACK_ALIGNMENT, 1),
    ],
    1: [
        (simple.glPixelStorei,simple.GL_PACK_SKIP_PIXELS, 0),
        (simple.glPixelStorei,simple.GL_PACK_ALIGNMENT, 1),
    ],
} )


__all__ = (
    'glReadPixels',
    'glReadPixelsb',
    'glReadPixelsd',
    'glReadPixelsf',
    'glReadPixelsi',
    'glReadPixelss',
    'glReadPixelsub',
    'glReadPixelsui',
    'glReadPixelsus',

    'glGetTexImage',

    'glDrawPixels',
    'glDrawPixelsb',
    'glDrawPixelsf',
    'glDrawPixelsi',
    'glDrawPixelss',
    'glDrawPixelsub',
    'glDrawPixelsui',
    'glDrawPixelsus',


    'glTexSubImage2D',
    'glTexSubImage1D',
    #'glTexSubImage3D',

    'glTexImage1D',
    'glTexImage2D',
    #'glTexImage3D',

    'glGetTexImageb',
    'glGetTexImaged',
    'glGetTexImagef',
    'glGetTexImagei',
    'glGetTexImages',
    'glGetTexImageub',
    'glGetTexImageui',
    'glGetTexImageus',
    'glTexImage1Db',
    'glTexImage2Db',
    #'glTexImage3Db',
    'glTexSubImage1Db',
    'glTexSubImage2Db',
    #'glTexSubImage3Db',
    'glTexImage1Df',
    'glTexImage2Df',
    #'glTexImage3Df',
    'glTexSubImage1Df',
    'glTexSubImage2Df',
    #'glTexSubImage3Df',
    'glTexImage1Di',
    'glTexImage2Di',
    #'glTexImage3Di',
    'glTexSubImage1Di',
    'glTexSubImage2Di',
    #'glTexSubImage3Di',
    'glTexImage1Ds',
    'glTexImage2Ds',
    #'glTexImage3Ds',
    'glTexSubImage1Ds',
    'glTexSubImage2Ds',
    #'glTexSubImage3Ds',
    'glTexImage1Dub',
    'glTexImage2Dub',
    #'glTexImage3Dub',
    'glTexSubImage1Dub',
    'glTexSubImage2Dub',
    #'glTexSubImage3Dub',
    'glTexImage1Dui',
    'glTexImage2Dui',
    #'glTexImage3Dui',
    'glTexSubImage1Dui',
    'glTexSubImage2Dui',
    #'glTexSubImage3Dui',
    'glTexImage1Dus',
    'glTexImage2Dus',
    #'glTexImage3Dus',
    'glTexSubImage1Dus',
    'glTexSubImage2Dus',
    #'glTexSubImage3Dus',

    #'glColorTable',
    #'glGetColorTable',
    #'glColorSubTable',

    #'glConvolutionFilter1D',
    #'glConvolutionFilter2D',
    #'glGetConvolutionFilter',
    #'glSeparableFilter2D',
    #'glGetSeparableFilter',

    #'glGetMinmax',
)

for suffix,type in [
    ('b',simple.GL_BYTE),
    ('d',simple.GL_DOUBLE),
    ('f',simple.GL_FLOAT),
    ('i',simple.GL_INT),
    ('s',simple.GL_SHORT),
    ('ub',simple.GL_UNSIGNED_BYTE),
    ('ui',simple.GL_UNSIGNED_INT),
    ('us',simple.GL_UNSIGNED_SHORT),
]:
    def glReadPixels( x,y,width,height,format,type=type, array=None ):
        """Read specified pixels from the current display buffer

        This typed version returns data in your specified default
        array data-type format, or in the passed array, which will
        be converted to the array-type required by the format.
        """
        x,y,width,height = asInt(x),asInt(y),asInt(width),asInt(height)
        arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[ images.TYPE_TO_ARRAYTYPE.get(type,type) ]
        if array is None:
            array = images.SetupPixelRead( format, (width,height), type )
        else:
            array = arrayType.asArray( array )
        imageData = arrayType.voidDataPointer( array )
        simple.glReadPixels(
            x,y,
            width, height,
            format,type,
            imageData
        )
        return array
    globals()["glReadPixels%s"%(suffix,)] = glReadPixels
    def glGetTexImage( target, level,format,type=type ):
        """Get a texture-level as an image"""
        from OpenGL.GL import glget
        dims = [glget.glGetTexLevelParameteriv( target, level, simple.GL_TEXTURE_WIDTH )]
        if target != simple.GL_TEXTURE_1D:
            dims.append( glget.glGetTexLevelParameteriv( target, level, simple.GL_TEXTURE_HEIGHT ) )
            if target != simple.GL_TEXTURE_2D:
                dims.append( glget.glGetTexLevelParameteriv( target, level, simple.GL_TEXTURE_DEPTH ) )
        array = images.SetupPixelRead( format, tuple(dims), type )
        arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[ images.TYPE_TO_ARRAYTYPE.get(type,type) ]
        simple.glGetTexImage(
            target, level, format, type, ctypes.c_void_p( arrayType.dataPointer(array))
        )
        return array
    globals()["glGetTexImage%s"%(suffix,)] = glGetTexImage
##	def glGetTexSubImage( target, level,format,type ):
##		"""Get a texture-level as an image"""
##		from OpenGL.GL import glget
##		dims = [glget.glGetTexLevelParameteriv( target, level, simple.GL_TEXTURE_WIDTH )]
##		if target != simple.GL_TEXTURE_1D:
##			dims.append( glget.glGetTexLevelParameteriv( target, level, simple.GL_TEXTURE_HEIGHT ) )
##			if target != simple.GL_TEXTURE_2D:
##				dims.append( glget.glGetTexLevelParameteriv( target, level, simple.GL_TEXTURE_DEPTH ) )
##		array = images.SetupPixelRead( format, tuple(dims), type )
##		arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[ images.TYPE_TO_ARRAYTYPE.get(type,type) ]
##		simple.glGetTexImage(
##			target, level, format, type, ctypes.c_void_p( arrayType.dataPointer(array))
##		)
##		return array
##	"%s = glGetTexImage"%(suffix)
    try:
        del suffix,type
    except NameError, err:
        pass
# Now the real glReadPixels...
def glReadPixels( x,y,width,height,format,type, array=None, outputType=str ):
    """Read specified pixels from the current display buffer

    x,y,width,height -- location and dimensions of the image to read
        from the buffer
    format -- pixel format for the resulting data
    type -- data-format for the resulting data
    array -- optional array/offset into which to store the value
    outputType -- default (str) provides string output of the
        results iff OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING is True
        and type == GL_UNSIGNED_BYTE.  Any other value will cause
        output in the default array output format.

    returns the pixel data array in the format defined by the
    format, type and outputType
    """
    x,y,width,height = asInt(x),asInt(y),asInt(width),asInt(height)

    arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[ images.TYPE_TO_ARRAYTYPE.get(type,type) ]
    if array is None:
        array = images.SetupPixelRead( format, (width,height), type )
    else:
        array = arrayType.asArray( array )
    imageData = arrayType.voidDataPointer( array )
    simple.glReadPixels(
        x,y,width,height,
        format,type,
        imageData
    )
    if outputType is str:
        return images.returnFormat( array, type )
    else:
        return array

def glGetTexImage( target, level,format,type, outputType=str ):
    """Get a texture-level as an image

    target -- enum constant for the texture engine to be read
    level -- the mip-map level to read
    format -- image format to read out the data
    type -- data-type into which to read the data

    outputType -- default (str) provides string output of the
        results iff OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING is True
        and type == GL_UNSIGNED_BYTE.  Any other value will cause
        output in the default array output format.

    returns the pixel data array in the format defined by the
    format, type and outputType
    """
    from OpenGL.GL import glget
    dims = [glget.glGetTexLevelParameteriv( target, level, simple.GL_TEXTURE_WIDTH )]
    if target != simple.GL_TEXTURE_1D:
        dims.append( glget.glGetTexLevelParameteriv( target, level, simple.GL_TEXTURE_HEIGHT ) )
        if target != simple.GL_TEXTURE_2D:
            dims.append( glget.glGetTexLevelParameteriv( target, level, simple.GL_TEXTURE_DEPTH ) )
    array = images.SetupPixelRead( format, tuple(dims), type )
    arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[ images.TYPE_TO_ARRAYTYPE.get(type,type) ]
    simple.glGetTexImage(
        target, level, format, type, ctypes.c_void_p( arrayType.dataPointer(array))
    )
    if outputType is str:
        return images.returnFormat( array, type )
    else:
        return array


INT_DIMENSION_NAMES = [
    'width','height','depth','x','y','z',
    'xoffset','yoffset','zoffset',
    'start', 'count',
]
def asWrapper( value ):
    if not isinstance( value, wrapper.Wrapper ):
        return wrapper.wrapper( value )
    return value

def asIntConverter( value, *args ):
    if isinstance( value, float ):
        return int(round(value,0))
    return value

def setDimensionsAsInts( baseOperation ):
    """Set arguments with names in INT_DIMENSION_NAMES to asInt processing"""
    baseOperation = asWrapper( baseOperation )
    argNames = getattr( baseOperation, 'pyConverterNames', baseOperation.argNames )
    for i,argName in enumerate(argNames):
        if argName in INT_DIMENSION_NAMES:
            baseOperation.setPyConverter( argName, asIntConverter )
    return baseOperation



class ImageInputConverter( object ):
    def __init__( self, rank, pixelsName=None, typeName='type' ):
        self.rank = rank
        self.typeName = typeName
        self.pixelsName = pixelsName
    def finalise( self, wrapper ):
        """Get our pixel index from the wrapper"""
        self.typeIndex = wrapper.pyArgIndex( self.typeName )
        self.pixelsIndex = wrapper.pyArgIndex( self.pixelsName )
    def __call__( self, arg, baseOperation, pyArgs ):
        """pyConverter for the pixels argument"""
        images.setupDefaultTransferMode()
        images.rankPacking( self.rank )
        type = pyArgs[ self.typeIndex ]
        arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[ images.TYPE_TO_ARRAYTYPE[ type ] ]
        return arrayType.asArray( arg )
#	def cResolver( self, array ):
#		return array
#		return ctypes.c_void_p( arrays.ArrayDatatype.dataPointer( array ) )

class TypedImageInputConverter( ImageInputConverter ):
    def __init__( self, rank, pixelsName, arrayType, typeName=None ):
        self.rank = rank
        self.arrayType = arrayType
        self.pixelsName = pixelsName
        self.typeName = typeName
    def __call__( self, arg, baseOperation, pyArgs ):
        """The pyConverter for the pixels"""
        images.setupDefaultTransferMode()
        images.rankPacking( self.rank )
        return self.arrayType.asArray( arg )
    def finalise( self, wrapper ):
        """Get our pixel index from the wrapper"""
        self.pixelsIndex = wrapper.pyArgIndex( self.pixelsName )
    def width( self, pyArgs, index, wrappedOperation ):
        """Extract the width from the pixels argument"""
        return self.arrayType.dimensions( pyArgs[self.pixelsIndex] )[0]
    def height( self, pyArgs, index, wrappedOperation ):
        """Extract the height from the pixels argument"""
        return self.arrayType.dimensions( pyArgs[self.pixelsIndex] )[1]
    def depth( self, pyArgs, index, wrappedOperation ):
        """Extract the depth from the pixels argument"""
        return self.arrayType.dimensions( pyArgs[self.pixelsIndex] )[2]
    def type( self, pyArgs, index, wrappedOperation ):
        """Provide the item-type argument from our stored value

        This is used for pre-bound processing where we want to provide
        the type by implication...
        """
        return self.typeName

class CompressedImageConverter( object ):
    def finalise( self, wrapper ):
        """Get our pixel index from the wrapper"""
        self.dataIndex = wrapper.pyArgIndex( 'data' )
    def __call__( self, pyArgs, index, wrappedOperation ):
        """Create a data-size measurement for our image"""
        arg = pyArgs[ self.dataIndex ]
        return arrays.ArrayType.arrayByteCount( arg )



DIMENSION_NAMES = (
    'width','height','depth'
)
PIXEL_NAMES = (
    'pixels', 'row', 'column',
)
DATA_SIZE_NAMES = (
    'imageSize',
)

def setImageInput(
    baseOperation, arrayType=None, dimNames=DIMENSION_NAMES,
    pixelName="pixels", typeName=None
):
    """Determine how to convert "pixels" into an image-compatible argument"""
    baseOperation = asWrapper( baseOperation )
    # rank is the count of width,height,depth arguments...
    rank = len([
        # rank is the number of dims we want, not the number we give...
        argName for argName in baseOperation.argNames
        if argName in dimNames
    ]) + 1
    if arrayType:
        converter = TypedImageInputConverter( rank, pixelName, arrayType, typeName=typeName )
        for i,argName in enumerate(baseOperation.argNames):
            if argName in dimNames:
                baseOperation.setPyConverter( argName )
                baseOperation.setCConverter( argName, getattr(converter,argName) )
            elif argName == 'type' and typeName is not None:
                baseOperation.setPyConverter( argName )
                baseOperation.setCConverter( argName, converter.type )
    else:
        converter = ImageInputConverter( rank, pixelsName=pixelName, typeName=typeName or 'type' )
    for argName in baseOperation.argNames:
        if argName in DATA_SIZE_NAMES:
            baseOperation.setPyConverter( argName )
            baseOperation.setCConverter( argName, converter.imageDataSize )
    baseOperation.setPyConverter(
        pixelName, converter,
    )
#	baseOperation.setCResolver(
#		pixelName, converter.cResolver
#	)
    return baseOperation

glDrawPixels = setDimensionsAsInts(
    setImageInput(
        simple.glDrawPixels
    )
)
glTexSubImage2D = setDimensionsAsInts(
    setImageInput(
        simple.glTexSubImage2D
    )
)
glTexSubImage1D = setDimensionsAsInts(
    setImageInput(
        simple.glTexSubImage1D
    )
)
glTexImage2D = setDimensionsAsInts(
    setImageInput(
        simple.glTexImage2D
    )
)
glTexImage1D = setDimensionsAsInts(
    setImageInput(
        simple.glTexImage1D
    )
)

def typedImageFunction( suffix, arrayConstant,  baseFunction ):
    """Produce a typed version of the given image function"""
    functionName = baseFunction.__name__
    functionName = '%(functionName)s%(suffix)s'%locals()
    if baseFunction:
        arrayType = arrays.GL_CONSTANT_TO_ARRAY_TYPE[ arrayConstant ]
        function = setDimensionsAsInts(
            setImageInput(
                baseFunction,
                arrayType,
                typeName = arrayConstant,
            )
        )
        return functionName, function
    else:
        return functionName, baseFunction

def _setDataSize( baseFunction, argument='imageSize' ):
    """Set the data-size value to come from the data field"""
    if baseFunction:
        converter = CompressedImageConverter()
        return asWrapper( baseFunction ).setPyConverter(
            argument
        ).setCConverter( argument, converter )
    else:
        return baseFunction

def compressedImageFunction( baseFunction ):
    """Set the imageSize and dimensions-as-ints converters for baseFunction"""
    if baseFunction:
        return setDimensionsAsInts(
            _setDataSize(
                baseFunction, argument='imageSize'
            )
        )
    else:
        return baseFunction

for suffix,arrayConstant in [
    ('b', simple.GL_BYTE),
    ('f', simple.GL_FLOAT),
    ('i', simple.GL_INT),
    ('s', simple.GL_SHORT),
    ('ub', simple.GL_UNSIGNED_BYTE),
    ('ui', simple.GL_UNSIGNED_INT),
    ('us', simple.GL_UNSIGNED_SHORT),
]:
    for functionName in (
        'glTexImage1D','glTexImage2D',
        'glTexSubImage1D','glTexSubImage2D',
        'glDrawPixels',
        #'glTexSubImage3D','glTexImage3D', # extension/1.2 standard
    ):
        functionName, function = typedImageFunction(
            suffix, arrayConstant, getattr(simple,functionName),
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
