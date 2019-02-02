#! /usr/bin/env python
from __future__ import print_function
import pygame, pygame.display
import logging, time, traceback, unittest, os
logging.basicConfig(level=logging.INFO)
HERE = os.path.dirname( __file__ )
import pickle
try:
    import cPickle
except ImportError as err:
    cPickle = pickle

try:
    from numpy import *
except ImportError as err:
    array = None

pygame.display.init()
import OpenGL 
if os.environ.get( 'TEST_NO_ACCELERATE' ):
    OpenGL.USE_ACCELERATE = False
#OpenGL.FULL_LOGGING = True
OpenGL.CONTEXT_CHECKING = True
OpenGL.FORWARD_COMPATIBLE_ONLY = False
OpenGL.UNSIGNED_BYTE_IMAGES_AS_STRING = True

#from OpenGL._bytes import bytes, _NULL_8_BYTE, unicode, as_8_bit
from OpenGL.GL import *
try:
    glGetError()
except error.NoContext as err:
    # good, should have got this error 
    pass
else:
    print( 'WARNING: Failed to catch invalid context' )
    #raise RuntimeError( """Did not catch invalid context!""" )
from OpenGL import error
from OpenGL.GLU import *
import OpenGL
from OpenGL.extensions import alternate
from OpenGL.GL.framebufferobjects import *
from OpenGL.GL.EXT.multi_draw_arrays import *
from OpenGL.GL.ARB.imaging import *
from OpenGL._bytes import _NULL_8_BYTE


glMultiDrawElements = alternate( 
    glMultiDrawElementsEXT, glMultiDrawElements, 
)
import basetestcase
    

class TestCore( basetestcase.BaseTest ):
    def test_errors( self ):
        """Test for error catching/checking"""
        try:
            glClear( GL_INVALID_VALUE )
        except Exception as err:
            assert err.err == 1281, ("""Expected invalid value (1281)""", err.err)
        else:
            assert not OpenGL.ERROR_CHECKING, """No error on invalid glClear"""
        try:
            glColorPointer(GL_INVALID_VALUE,GL_BYTE,0,None)
        except Exception as err:
            assert err.err == 1281, ("""Expected invalid value (1281)""", err.err)
            assert err.baseOperation, err.baseOperation
            assert err.pyArgs == (GL_INVALID_VALUE, GL_BYTE, 0, None), err.pyArgs
            assert err.cArgs == (GL_INVALID_VALUE, GL_BYTE, 0, None), err.cArgs
        else:
            assert not OpenGL.ERROR_CHECKING, """No error on invalid glColorPointer"""
        try:
            glBitmap(-1,-1,0,0,0,0,as_8_bit(""))
        except Exception as err:
            assert err.err in (1281,1282), ("""Expected invalid value (1281) or invalid operation (1282)""", err.err)
        else:
            assert not OpenGL.ERROR_CHECKING, """No error on invalid glBitmap"""
    if not OpenGL.ERROR_ON_COPY:
        def test_simple( self ):
            """Test for simple vertex-based drawing"""
            glDisable( GL_LIGHTING )
            glBegin( GL_TRIANGLES )
            try:
                try:
                    glVertex3f( 0.,1.,0. )
                except Exception:
                    traceback.print_exc()
                glVertex3fv( [-1,0,0] )
                glVertex3dv( [1,0,0] )
                try:
                    glVertex3dv( [1,0,4,5] )
                except ValueError:
                    #Got expected value error (good)
                    assert OpenGL.ARRAY_SIZE_CHECKING, """Should have raised ValueError when doing array size checking"""
                else:
                    assert not OpenGL.ARRAY_SIZE_CHECKING, """Should not have raised ValueError when not doing array size checking"""
            finally:
                glEnd()
            a = glGenTextures( 1 )
            assert a
            b = glGenTextures( 2 )
            assert len(b) == 2
    def test_arbwindowpos( self ):
        """Test the ARB window_pos extension will load if available"""
        from OpenGL.GL.ARB.window_pos import glWindowPos2dARB
        if glWindowPos2dARB:
            glWindowPos2dARB( 0.0, 3.0 )
    def test_getstring( self ):
        assert glGetString( GL_EXTENSIONS )
    def test_constantPickle( self ):
        """Test that our constants can be pickled/unpickled properly"""
        for p in pickle,cPickle:
            v = p.loads( p.dumps( GL_VERTEX_ARRAY ))
            assert v == GL_VERTEX_ARRAY, (v,GL_VERTEX_ARRAY)
            assert v.name == GL_VERTEX_ARRAY.name, v.name 
    
    
    def test_nonFloatColor( self ):
        """Test that we handle non-floating-point colour inputs"""
        for notFloat,shouldWork in ((0,True), (object(),False), (object,False)):
            try:
                glColor4f( 0,1,1,notFloat )
            except Exception:
                if shouldWork:
                    raise 
            else:
                if not shouldWork:
                    raise RuntimeError( """Expected failure for non-float value %s, succeeded"""%( notFloat, ))
    if array:
        def test_arrayTranspose( self ):
            m = glGetFloatv( GL_MODELVIEW_MATRIX )
            glMatrixMode( GL_MODELVIEW )
            glLoadIdentity()

            t = eye(4)
            t[3,0] = 20.0

            # the following glMultMatrixf call ignored this transpose
            t = t.T
            if OpenGL.ERROR_ON_COPY:
                t = ascontiguousarray( t )
            
            glMultMatrixd( t )

            m = glGetFloatv( GL_MODELVIEW_MATRIX )
            assert allclose( m[-1], [0,0,0,1] ), m
    
    if array:
        # currently crashes in py_buffer operation, so reverted to raw numpy 
        # api
        def test_mmap_data( self ):
            """Test that we can use mmap data array
            
            If we had a reasonable lib that dumped raw image data to a shared-mem file
            we might be able to use this for movie display :) 
            """
            fh = open( 'mmap-test-data.dat', 'wb+' )
            fh.write( _NULL_8_BYTE*(32*32*3+1))
            fh.flush()
            fh.close()
            # using memmap here...
            data = memmap( 'mmap-test-data.dat' )
            for i in range( 0,255,2 ):
                glDrawPixels( 32,32, GL_RGB, GL_UNSIGNED_BYTE, data, )
                glFlush()
                pygame.display.flip()
                data[::2] = i
                time.sleep( 0.001 )
    
    if array:
        def test_vbo( self ):
            """Test utility vbo wrapper"""
            from OpenGL.arrays import vbo
            assert vbo.get_implementation()
            points = array( [
                [0,0,0],
                [0,1,0],
                [1,.5,0],
                [1,0,0],
                [1.5,.5,0],
                [1.5,0,0],
            ], dtype='d')
            indices = array(
                range(len(points)),
                ['i','I'][bool(OpenGL.ERROR_ON_COPY)], # test coercion if we can
            )
            d = vbo.VBO(points)
            glDisable( GL_CULL_FACE )
            glNormal3f( 0,0,1 )
            glColor3f( 1,1,1 )
            glEnableClientState(GL_VERTEX_ARRAY)
            try:
                for x in range( 1, 255, 10 ):
                    d.bind()
                    try:
                        glVertexPointerd( d )
                        glDrawElements( GL_LINE_LOOP, len(indices), GL_UNSIGNED_INT, indices )
                    finally:
                        d.unbind()
                    lastPoint = array( [[1.5,(1/255.) * float(x),0]] )
                    d[-2:-1] = lastPoint
                    glFlush()
                    pygame.display.flip()
                    glClear( GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT )
                    time.sleep( 0.001 )
            finally:
                glDisableClientState( GL_VERTEX_ARRAY )
            # bug report from Dan Helfman, delete shouldn't cause 
            # errors if called explicitly
            d.delete()
        def test_glgetbufferparameter(self):
            from OpenGL.arrays import vbo
            buffer = glGenBuffers(1)
            vertex_array = glGenVertexArrays(1,buffer)
            glBindBuffer(GL_ARRAY_BUFFER, buffer)
            try:
                mapped = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_MAPPED)
                assert mapped == (GL_FALSE if OpenGL.SIZE_1_ARRAY_UNPACK else [GL_FALSE]), mapped
            finally:
                glBindBuffer(GL_ARRAY_BUFFER, 0)
                glDeleteVertexArrays(1,vertex_array)
                glDeleteBuffers(1,buffer)
    def test_fbo( self ):
        """Test that we support framebuffer objects
        
        http://www.gamedev.net/reference/articles/article2331.asp
        """
        if not glGenFramebuffers:
            print( 'No Frame Buffer Support!' )
            return False
        width = height = 128
        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        depthbuffer = glGenRenderbuffers(1 )
        glBindRenderbuffer(GL_RENDERBUFFER, depthbuffer)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height)
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, 
            depthbuffer
        )

        img = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, img)
        # NOTE: these lines are *key*, without them you'll likely get an unsupported format error,
        # ie. GL_FRAMEBUFFER_UNSUPPORTED
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGB8,  
            width, height, 0, GL_RGB, 
            GL_INT, 
            None # no data transferred
        ) 
        glFramebufferTexture2D(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, 
            img, 
            0 # mipmap level, normally 0
        )
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        assert status == GL_FRAMEBUFFER_COMPLETE, status
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glPushAttrib(GL_VIEWPORT_BIT) # viewport is shared with the main context
        try:
            glViewport(0,0,width, height)
            
            # rendering to the texture here...
            glColor3f( 1,0,0 )
            glNormal3f( 0,0,1 )
            glBegin( GL_QUADS )
            for v in [[0,0,0],[0,1,0],[1,1,0],[1,0,0]]:
                glColor3f( *v )
                glVertex3d( *v )
            glEnd()
        finally:
            glPopAttrib(); # restore viewport
        glBindFramebuffer(GL_FRAMEBUFFER, 0) # unbind
        
        glBindTexture(GL_TEXTURE_2D, img)
        
        glEnable( GL_TEXTURE_2D )
        
        # rendering with the texture here...
        glColor3f( 1,1,1 )
        glNormal3f( 0,0,1 )
        glDisable( GL_LIGHTING )
        glBegin( GL_QUADS )
        try:
            for v in [[0,0,0],[0,1,0],[1,1,0],[1,0,0]]:
                glTexCoord2f( *v[:2] )
                glVertex3d( *v )
        finally:
            glEnd()
    def test_gl_1_2_support( self ):
        if glBlendColor:
            glBlendColor( .3, .4, 1.0, .3 )
            print('OpenGL 1.2 support')
    if array:
        def test_glmultidraw( self ):
            """Test that glMultiDrawElements works, uses glDrawElements"""
            if glMultiDrawElements:
                points = array([
                    (i,0,0) for i in range( 8 )
                ] + [
                    (i,1,0) for i in range( 8 )
                ], 'd')
                indices = array([
                    [0,8,9,1, 2,10,11,3,],
                    [4,12,13,5,6,14,15,7],
                ],'B')
                index_pointers = arrays.GLvoidpArray.zeros( (2,))
                index_pointers[0] = arrays.GLbyteArray.dataPointer( indices )
                index_pointers[1] = arrays.GLbyteArray.dataPointer( indices[1] )
                counts = [ len(x) for x in indices ]
                if OpenGL.ERROR_ON_COPY:
                    counts = (GLuint*len(counts))(*counts)
                glEnableClientState( GL_VERTEX_ARRAY )
                glDisableClientState( GL_COLOR_ARRAY )
                glDisableClientState( GL_NORMAL_ARRAY )
                try:
                    glVertexPointerd( points )
                    glDisable( GL_LIGHTING )
                    try:
                        glMultiDrawElements(GL_QUAD_STRIP, counts, GL_UNSIGNED_BYTE, index_pointers, 2)
                    finally:
                        glEnable( GL_LIGHTING )
                finally:
                    glDisableClientState( GL_VERTEX_ARRAY )
            else:
                print('No multi_draw_arrays support')
    def test_glDrawBuffers_list( self ):
        """Test that glDrawBuffers with list argument doesn't crash"""
        a_type = GLenum*2
        args = a_type(
            GL_COLOR_ATTACHMENT0,
            GL_COLOR_ATTACHMENT1,
        )
        try:
            glDrawBuffers( 2, args )
        except GLError as err:
            assert err.err == GL_INVALID_OPERATION, err
    def test_glDrawBuffers_list_valid( self ):
        """Test that glDrawBuffers with list argument where value is set"""
        previous = glGetIntegerv( GL_READ_BUFFER )
        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        try:
            img1,img2 = glGenTextures(2)
            for img in img1,img2:
                glBindTexture( GL_TEXTURE_2D, img )
                glTexImage2D(
                    GL_TEXTURE_2D, 0, GL_RGB8,  
                    300, 300, 0, GL_RGB, 
                    GL_INT, 
                    None # no data transferred
                ) 
            

            glFramebufferTexture2D(
                GL_FRAMEBUFFER, 
                GL_COLOR_ATTACHMENT0, 
                GL_TEXTURE_2D, img1, 0
            )
            glFramebufferTexture2D(
                GL_FRAMEBUFFER, 
                GL_COLOR_ATTACHMENT1, 
                GL_TEXTURE_2D, img2, 0
            )
            a_type = GLenum*2
            drawingBuffers = a_type(
                GL_COLOR_ATTACHMENT0, 
                GL_COLOR_ATTACHMENT1,
            )
            glDrawBuffers(2, drawingBuffers )
            try:
                checkFramebufferStatus()
            except error.GLError:
                pass
            else:
                glReadBuffer( GL_COLOR_ATTACHMENT1 )
                pixels = glReadPixels( 0,0, 10,10, GL_RGB, GL_UNSIGNED_BYTE )
                assert len(pixels) == 300, len(pixels)
        finally:
            glBindFramebuffer( GL_FRAMEBUFFER, 0 )
        
        glReadBuffer( previous )
        
    def test_get_version( self ):
        from OpenGL.extensions import hasGLExtension
        if hasGLExtension( 'GL_VERSION_GL_2_0' ):
            assert glShaderSource
            assert glUniform1f
        else:
            assert not glShaderSource
            assert not glUniform1f
    
    def test_lookupint( self ):
        from OpenGL.raw.GL import _lookupint 
        l = _lookupint.LookupInt( GL_NUM_COMPRESSED_TEXTURE_FORMATS, GLint )
        result = int(l)
        if not os.environ.get('TRAVIS'):
            assert result, "No compressed textures on this platform? that seems unlikely"
        else:
            assert not result, "Travis xvfb doesn't normally have compressed textures, possible upgrade?"
    
    def test_glget( self ):
        """Test that we can run glGet... on registered constants without crashing..."""
        from OpenGL.raw.GL import _glgets
        get_items = sorted(_glgets._glget_size_mapping.items())
        for key,value in get_items:
            # There are glGet values that will cause a crash during cleanup
            # GL_ATOMIC_COUNTER_BUFFER_BINDING 0x92c1 crashes/segfaults
            if key >= 0x8df9 and key <= 0x8e23:
                continue
            if key >= 0x92be and key <= 0x92c9:
                continue
            print( 'Trying glGetFloatv( 0x%x )'%(key,))
            try:
                result = glGetFloatv( key )
            except error.GLError as err:
                if err.err == GL_INVALID_ENUM:
                    pass
                elif err.err == GL_INVALID_OPERATION:
                    if key == 0x882d: # gl draw buffer 
                        pass
                else:
                    raise 
            else:
                if value == (1,) and OpenGL.SIZE_1_ARRAY_UNPACK:
                    try:
                        result = float(result)
                    except TypeError as err:
                        err.args += (result,key)
                        raise
                else:
                    assert ArrayDatatype.dimensions( result ) == value, (result,ArrayDatatype.dimensions( result ), value)
    def test_max_compute_work_group_invocations(self):
        from OpenGL.extensions import hasGLExtension
        if hasGLExtension( 'GL_ARB_compute_shader' ):
            assert glGetIntegerv( GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS )
    
    
    def test_glCallLists_twice2( self ):
        """SF#2829309 report that glCallLists doubles operation"""
        glRenderMode (GL_RENDER)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, 1.0, 1.0, 10.0)
        glMatrixMode (GL_MODELVIEW)
        glLoadIdentity ()
        glTranslatef (0, 0, -3)
        first = glGenLists( 2 )
        second = first+1

        glNewList(first, GL_COMPILE_AND_EXECUTE)
        glInitNames ()
        if not OpenGL.ERROR_ON_COPY:
            glCallLists([second]) # replace with gCallList(2)
        else:
            lists = (GLuint * 1)()
            lists[0] = second
            glCallLists(lists)
        #glCallList(second)
        glEndList ()

        glNewList(second, GL_COMPILE)
        glPushName (1)
        glBegin (GL_POINTS)
        glVertex3f (0, 0, 0)
        glEnd ()
        glEndList ()
        glCallList( second )
        glPopName()
        depth = glGetIntegerv( GL_NAME_STACK_DEPTH )
        assert depth in (0,(0,)), depth # have popped, but even then, were' not in the mode...

        glSelectBuffer (100)
        glRenderMode (GL_SELECT)
        glCallList(1)
        depth = glGetIntegerv( GL_NAME_STACK_DEPTH )
        assert depth in (1,(1,)), depth # should have a single record
        glPopName()
        records = glRenderMode (GL_RENDER)
        # reporter says sees two records, Linux sees none, Win32 sees 1 :(
        assert len(records) == 1, records
    
    
    def test_orinput_handling( self ):
        x = glGenVertexArrays(1)
        x = int(x) # check that we got x as an integer-compatible value
        x2 = GLuint()
        r_value = glGenVertexArrays( 1, x2 )
        assert x2.value, x2.value
        assert r_value
        
        color = glGetFloatv( GL_FOG_COLOR )
        color2 = (GLfloat *4)()
        glGetFloatv( GL_FOG_COLOR, color2 )
        for a,b in zip( color,color2 ):
            assert a==b, (color,color2)
    
    
    def test_get_read_fb_binding( self ):
        glGetInteger(GL_READ_FRAMEBUFFER_BINDING)
    
    def test_shader_compile_string( self ):
        shader = glCreateShader(GL_VERTEX_SHADER)
        
        def glsl_version():
            """Parse GL_SHADING_LANGUAGE_VERSION into [int(major),int(minor)]"""
            version = glGetString( GL_SHADING_LANGUAGE_VERSION )
            version = version.split(as_8_bit(' '))[0]
            version = [int(x) for x in version.split(as_8_bit('.'))[:2]]
            return version 
        if glsl_version() < [3,3]:
            return
        SAMPLE_SHADER = '''#version 330
        void main() { gl_Position = vec4(0,0,0,0);}'''
        if OpenGL.ERROR_ON_COPY:
            SAMPLE_SHADER = as_8_bit( SAMPLE_SHADER )
        glShaderSource(shader, SAMPLE_SHADER)
        glCompileShader(shader)
        if not bool(glGetShaderiv(shader, GL_COMPILE_STATUS)) == True:
            print('Info log:')
            print(glGetShaderInfoLog(shader))
            assert False, """Failed to compile"""
    
    def test_gen_framebuffers_twice( self ):
        glGenFramebuffersEXT(1)
        f1 = glGenFramebuffersEXT(1)
        f2 = glGenFramebuffersEXT(1)
        assert f1 != f2, (f1,f2)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, f2)
        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
    
    def test_compressed_data(self):
        from OpenGL.extensions import hasGLExtension
        if hasGLExtension( 'GL_EXT_texture_compression_s3tc' ):
            from OpenGL.GL.EXT import texture_compression_s3tc as s3tc
            texture = glGenTextures(1)
            glEnable( GL_TEXTURE_2D )
            image_type = GLubyte *256*256
            image = image_type()
            glCompressedTexImage2D(
                GL_TEXTURE_2D, 0, 
                s3tc.GL_COMPRESSED_RGBA_S3TC_DXT5_EXT, 
                256, 256, 0, 
                image
            )
            assert texture
    
    
        
if __name__ == "__main__":
    logging.basicConfig( level=logging.INFO )
    unittest.main()
    pygame.display.quit()
    pygame.quit()
