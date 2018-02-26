import basetestcase
import os
from OpenGL.GL import *
try:
    import numpy as np
except ImportError as err:
    np = None
from OpenGL.arrays import arraydatatype
HERE = os.path.abspath(os.path.dirname(__file__))
from OpenGL.GL.ARB import texture_rg

class TestTextures(basetestcase.BaseTest):
    def test_enable_histogram( self ):
        if glInitImagingARB():
            glHistogram(GL_HISTOGRAM, 256, GL_LUMINANCE, GL_FALSE)
            glEnable( GL_HISTOGRAM )
            glDisable( GL_HISTOGRAM )
        else:
            print('No ARB imaging extension')
    if np:
        def test_glreadpixels_warray( self ):
            """SF#1311265 allow passing in the array object"""
            width,height = self.width, self.height
            data = np.zeros( (width,height,3), 'B' )
            image1 = glReadPixelsub(0,0,width,height,GL_RGB,array=data)
            assert image1 is not None
        someData = [ (0,255,0)]
        def test_glAreTexturesResident( self ):
            """Test that PyOpenGL api for glAreTexturesResident is working
            
            Note: not currently working on AMD64 Linux for some reason
            """
            textures = glGenTextures(2)
            residents = []
            data = np.array( self.someData,'i' )
            for texture in textures:
                glBindTexture( GL_TEXTURE_2D,int(texture) )
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 1, 1, 0, GL_RGB, GL_INT, data)
                residents.append(
                    glGetTexParameteriv(GL_TEXTURE_2D, GL_TEXTURE_RESIDENT )
                )
            glGetError()
            result = glAreTexturesResident( textures)
            assert len(result) == 2
            for (tex,expected,found) in zip( textures, residents, result ):
                if expected != found:
                    print(('Warning: texture %s residence expected %s got %s'%( tex, expected, found )))
    def test_glreadpixelsf( self ):
        """Issue #1979002 crash due to mis-calculation of resulting array size"""
        width,height = self.width, self.height
        readback_image1 = glReadPixelsub(0,0,width,height,GL_RGB)
        assert readback_image1 is not None
        readback_image2 = glReadPixelsf(0,0,width,height,GL_RGB)
        assert readback_image2 is not None
    def test_glreadpixels_is_string( self ):
        """Issue #1959860 incompatable change to returning arrays reversed"""
        width,height = self.width, self.height
        readback_image1 = glReadPixels(0,0,width,height,GL_RGB, GL_UNSIGNED_BYTE)
        assert isinstance( readback_image1, bytes ), type( readback_image1 )
        readback_image1 = glReadPixels(0,0,width,height,GL_RGB, GL_BYTE)
        assert not isinstance( readback_image1, bytes ), type(readback_image2)
    def test_passBackResults( self ):
        """Test ALLOW_NUMPY_SCALARS to allow numpy scalars to be passed in"""
        textures = glGenTextures(2)
        glBindTexture( GL_TEXTURE_2D, textures[0] )
    def test_nullTexture( self ):
        """Test that we can create null textures"""
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 512, 512, 0, GL_RGB, GL_INT, None)

    def test_get_boolean_bitmap( self ):
        # should not raise error
        glGetBoolean(GL_TEXTURE_2D)
    if np:
        def test_draw_bitmap_pixels( self ):
            """SF#2152623 Drawing pixels as bitmaps (bits)"""
            # this core-dumps on Mesa Intel on Ubuntu 15.04 :(
            # nosetest skip would be more appropriate
            return False
            pixels = np.array([0,0,0,0,0,0,0,0],'B')
            glDrawPixels( 8,8, GL_COLOR_INDEX, GL_BITMAP, pixels )

    def test_get_max_tex_units( self ):
        """SF#2895081 glGetIntegerv( GL_MAX_TEXTURE_IMAGE_UNITS )"""
        units = glGetIntegerv( GL_MAX_TEXTURE_IMAGE_UNITS )
        assert units
    def test_glGenTextures( self ):
        texture = glGenTextures(1)
        assert texture
        
    def test_createTargetArray(self):
        import OpenGL.GL as gl
        import OpenGL.images as images
        size = (640,480)
        array1 = images.createTargetArray( gl.GL_BGRA, size, gl.GL_UNSIGNED_INT_8_8_8_8_REV)
        array2 = images.createTargetArray( gl.GL_RGBA, size, gl.GL_UNSIGNED_BYTE)
        array3 = images.createTargetArray( gl.GL_RGBA, size, gl.GL_UNSIGNED_INT_8_8_8_8_REV)
        if hasattr( array1, 'nbytes'):
            assert array1.nbytes == array3.nbytes
            assert array1.nbytes == array2.nbytes
        else:
            assert ctypes.sizeof( array1 ) == ctypes.sizeof(array3)
            assert ctypes.sizeof( array1 ) == ctypes.sizeof(array2)
        
        try:
            images.createTargetArray( gl.GL_RGBA, size, gl.GL_UNSIGNED_BYTE_3_3_2 )
        except ValueError as err:
            pass 
        else:
            raise RuntimeError( """Should have failed with insufficient components in the type to hold the format""" )
    

    def test_rg_format(self):
        # Note: this is actually only known after context creation...
        if not texture_rg.glInitTextureRgARB():
            return 
        texture = glGenTextures(1)
        data = arraydatatype.GLfloatArray.asArray([.3,.5])
        glBindTexture( GL_TEXTURE_2D,int(texture) )
        glTexImage2D(GL_TEXTURE_2D, 0, texture_rg.GL_RG, 1, 1, 0, GL_RG, GL_FLOAT, data)
    
        
