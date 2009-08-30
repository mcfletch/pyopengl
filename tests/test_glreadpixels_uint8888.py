import OpenGL.GL as gl
import OpenGL.images as images

def test_createTargetArray():
    size = (640,480)
    array1 = images.createTargetArray( gl.GL_BGRA, size, gl.GL_UNSIGNED_INT_8_8_8_8_REV)
    array2 = images.createTargetArray( gl.GL_RGBA, size, gl.GL_UNSIGNED_BYTE)
    array3 = images.createTargetArray( gl.GL_RGBA, size, gl.GL_UNSIGNED_INT_8_8_8_8_REV)
    assert array1.nbytes == array3.nbytes
    assert array1.nbytes == array2.nbytes
    
    try:
        images.createTargetArray( gl.GL_RGBA, size, gl.GL_UNSIGNED_BYTE_3_3_2 )
    except ValueError, err:
        pass 
    else:
        raise RuntimeError( """Should have failed with insufficient components in the type to hold the format""" )