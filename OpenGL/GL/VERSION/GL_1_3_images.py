"""OpenGL version 1.3 imaging-handling routines"""
from OpenGL import wrapper, constants, arrays
from OpenGL.raw.GL.VERSION import GL_1_3 as simple
from OpenGL.GL import images, glget

for dimensions in (1,2,3):
    for function in ('glCompressedTexImage%sD','glCompressedTexSubImage%sD'):
        name = function%(dimensions,)
        globals()[ name ] = images.compressedImageFunction(
            getattr( simple, name )
        )
        try:
            del name, function
        except NameError, err:
            pass
    try:
        del dimensions
    except NameError, err:
        pass

if simple.glGetCompressedTexImage:
    def glGetCompressedTexImage( target, level, img=None ):
        """Retrieve a compressed texture image"""
        if img is None:
            length = glget.glGetTexLevelParameteriv(
                target, 0,
                simple.GL_TEXTURE_COMPRESSED_IMAGE_SIZE_ARB,
            )
            img = arrays.ArrayDataType.zeros( (length,), constants.GL_UNSIGNED_BYTE )
        return simple.glGetCompressedTexImage(target, 0, img);
