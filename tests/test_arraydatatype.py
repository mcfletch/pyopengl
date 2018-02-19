import basetestcase
import os, sys
import OpenGL
from OpenGL.arrays import (
    arraydatatype
)
from OpenGL.GL import *
try:
    import numpy as np
except ImportError as err:
    np = None
HERE = os.path.abspath(os.path.dirname(__file__))
import pytest
from OpenGL import acceleratesupport

class TestCoreDatatype(basetestcase.BaseTest):
    def test_arrayPointer( self ):
        dt = arraydatatype.GLuintArray
        d = dt.zeros( (3,))
        dp = dt.typedPointer( d )
        assert dp[0] == 0 
        assert dp[1] == 0
        assert dp[2] == 0
        dp[1] = 1
        assert dp[1] == 1
        assert d[1] == 1
    def test_ctypes_array( self ):
        color = (GLfloat * 3)( 0,1,0 )
        glColor3fv( color )
    if not OpenGL.ERROR_ON_COPY:
        def test_pointers( self ):
            """Test that basic pointer functions work"""
            vertex = GLdouble * 3
            vArray =  vertex * 2
            glVertexPointerd( [[2,3,4,5],[2,3,4,5]] )
            glVertexPointeri( ([2,3,4,5],[2,3,4,5]) )
            glVertexPointers( [[2,3,4,5],[2,3,4,5]] )
            glVertexPointerd( vArray( vertex(2,3,4),vertex(2,3,4) ) )
            myVector = vArray( vertex(2,3,4),vertex(2,3,4) )
            glVertexPointer(
                3,
                GL_DOUBLE,
                0,
                ctypes.cast( myVector, ctypes.POINTER(GLdouble)) 
            )
            
            repr(glVertexPointerb( [[2,3],[4,5]] ))
            glVertexPointerf( [[2,3],[4,5]] )
            assert arrays.ArrayDatatype.dataPointer( None ) == None
            glVertexPointerf( None )
            
            glNormalPointerd( [[2,3,4],[2,3,4]] )
            glNormalPointerd( None )
        
            glTexCoordPointerd( [[2,3,4],[2,3,4]] )
            glTexCoordPointerd( None )
        
            glColorPointerd( [[2,3,4],[2,3,4]] )
            glColorPointerd( None )
        
            glEdgeFlagPointerb( [0,1,0,0,1,0] )
            glEdgeFlagPointerb( None )
        
            glIndexPointerd( [0,1,0,0,1,0] )
            glIndexPointerd( None )
            
            glColor4fv( [0,0,0,1] )
            
            # string data-types...
            import struct
            s = struct.pack( '>iiii', 2,3,4,5 ) * 2
            glVertexPointer( 4,GL_INT,0,s )
        def test_texture( self ):
            """Test texture (requires OpenGLContext and PIL)"""
            try:
                from OpenGLContext import texture
                import Image 
                from OpenGL.GLUT import glutSolidTeapot
            except ImportError:
                pass
            else:
                assert glutSolidTeapot
                glEnable( GL_TEXTURE_2D )
                ourTexture = texture.Texture(
                    Image.open( os.path.join( HERE, 'yingyang.png') )
                )
                ourTexture()
                
                result = glGetTexImageub( GL_TEXTURE_2D,0,GL_RGBA )
                assert isinstance( result, bytes ), type(result)
                result = glGetTexImage( GL_TEXTURE_2D,0,GL_RGBA, GL_UNSIGNED_BYTE )
                assert isinstance( result, bytes ), type(result)
                
                glEnable( GL_LIGHTING )
                glEnable( GL_LIGHT0 )
                glBegin( GL_TRIANGLES )
                try:
                    try:
                        glTexCoord2f( .5, 1 )
                        glVertex3f( 0.,1.,0. )
                    except Exception:
                        traceback.print_exc()
                    glTexCoord2f( 0, 0 )
                    glVertex3fv( [-1,0,0] )
                    glTexCoord2f( 1, 0 )
                    glVertex3dv( [1,0,0] )
                    try:
                        glVertex3dv( [1,0] )
                    except ValueError:
                        assert OpenGL.ARRAY_SIZE_CHECKING, """Should have raised ValueError when doing array size checking"""
                    else:
                        assert not OpenGL.ARRAY_SIZE_CHECKING, """Should not have raised ValueError when not doing array size checking"""
                finally:
                    glEnd()
    @pytest.mark.skipif( not np, reason="Numpy not available")
    def test_numpyConversion( self ):
        """Test that we can run a numpy conversion from double to float for glColorArray"""
        a = np.arange( 0,1.2, .1, 'd' ).reshape( (-1,3 ))
        glEnableClientState(GL_VERTEX_ARRAY)
        try:
            glColorPointerf( a )
            glColorPointerd( a )
        finally:
            glDisableClientState( GL_VERTEX_ARRAY )
    @pytest.mark.skipif( not np, reason="Numpy not available")
    def test_glbuffersubdata_numeric(self):
        from OpenGL.arrays import vbo
        assert vbo.get_implementation()
        points = np.array( [
            [0,0,0],
            [0,1,0],
            [1,.5,0],
            [1,0,0],
            [1.5,.5,0],
            [1.5,0,0],
        ], dtype='f')
        d = vbo.VBO(points)
        with d:
            glBufferSubData(
                d.target,
                12,
                12,
                np.array([1,1,1],dtype='f'),
            )
    @pytest.mark.skipif( not np, reason="Numpy not available")
    @pytest.mark.skipif( OpenGL.ERROR_ON_COPY, reason="Test requires array copy")
    def test_copyNonContiguous( self ):
        """Test that a non-contiguous (transposed) array gets applied as a copy"""
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix( )
        try:
            transf = np.identity(4, dtype=np.float32)
            # some arbitrary transformation...
            transf[0,3] = 2.5
            transf[2,3] = -80
            
            # what do we get with the un-transposed version...
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glMultMatrixf(transf)
            untransposed = glGetFloatv(GL_MODELVIEW_MATRIX)
            # now transposed...

            # with a copy it works...
            t2 = transf.transpose().copy()
            # This doesn't work:
            glLoadIdentity()
            glMultMatrixf(t2)
            # This does work:
            #glMultMatrixf(transf.transpose().copy())
            transposed = glGetFloatv(GL_MODELVIEW_MATRIX)

            assert not np.allclose( transposed, untransposed ), (transposed, untransposed)
            
            t2 = transf.transpose()
            # This doesn't work:
            glLoadIdentity()
            glMultMatrixf(t2)
            # This does work:
            #glMultMatrixf(transf.transpose().copy())
            transposed = glGetFloatv(GL_MODELVIEW_MATRIX)
            
            assert not np.allclose( transposed, untransposed ), (transposed, untransposed)
        finally:
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()

    def test_bytes_array_support( self ):
        color = b'\000'*12
        glColor3fv( color )
        
        
    @pytest.mark.skipif( not (
        OpenGL.USE_ACCELERATE and acceleratesupport.ACCELERATE_AVAILABLE
    ), reason="Need OpenGL_accelerate for buffer support")
    def test_bytearray_support( self ):
        import struct 
        data = struct.pack( b'fff', .5, .4, .3 )
        color = bytearray( data )
        glColor3fv( color )
    
    @pytest.mark.skipif( not (
        OpenGL.USE_ACCELERATE and acceleratesupport.ACCELERATE_AVAILABLE
    ), reason="Need OpenGL_accelerate for buffer support")
    def test_buffer_api_basic(self):
        import array as silly_array
        structures = [
            (b'this and that',13,1,True,1,b'B',[13],[1]),
        ]
        if sys.version_info[:2] >= (2,7):
            structures.append(
                # on Python 3.4 we do *not* get the (3) prefix :(
                ((GLint * 3)( 1,2,3 ),12,4,False,1,[b'(3)<i',b'(3)<l',b'<i'],[3],None),
            )
        
        if sys.version_info[:2] >= (3,0):
            # only supports buffer protocol in 3.x
            structures.extend([
                (silly_array.array('I',[1,2,3]),12,4,False,1,b'I',[3],[4]),
            ])
        try:
            structures.append( (memoryview(b'this'),4,1,True,1,b'B',[4],[1]) )
        except NameError:
            # Python 2.6 doesn't have memory view 
            pass
        try:
            if array:
                structures.extend( [
                    (arange(0,9,dtype='I').reshape((3,3)),36,4,False,2,b'I',[3,3],[12,4]),
                    (arange(0,9,dtype='I').reshape((3,3))[:,1],12,4,False,1,b'I',[3],[12]),
                ])
        except NameError:
            # Don't have numpy installed...
            pass
        
        from OpenGL.arrays import _buffers
        for object,length,itemsize,readonly,ndim,format,shape,strides in structures:
            buf = _buffers.Py_buffer.from_object( object, _buffers.PyBUF_STRIDES|_buffers.PyBUF_FORMAT )
            with buf:
                assert buf.len == length, (object,length,buf.len)
                assert buf.itemsize == itemsize, (object,itemsize,buf.itemsize)
                assert buf.readonly == readonly, (object,readonly,buf.readonly)
                assert buf.ndim == ndim, (object,ndim,buf.ndim)
                if isinstance( format, list):
                    assert buf.format in format, (object,format,buf.format)
                else:
                    assert buf.format == format, (object,format,buf.format)
                assert buf.shape[:buf.ndim] == shape, (object, shape, buf.shape[:buf.ndim])
                assert buf.dims == shape, (object, shape, buf.dims )
                assert buf.buf 
                if strides is None:
                    assert not buf.strides 
                else:
                    assert buf.strides[:buf.ndim] == strides, (object, strides, buf.strides[:buf.ndim])
            assert buf.obj == None, buf.obj
            del buf
    
    
    @pytest.mark.skipif( not (
        OpenGL.USE_ACCELERATE and acceleratesupport.ACCELERATE_AVAILABLE
    ), reason="Need OpenGL_accelerate for buffer support")
    def test_memoryview_support( self ):
        color = bytearray( b'\000'*12 )
        mem = memoryview( color )
        glColor3fv( mem )
                

    def test_void_dp_for_void_dp_is_self( self ):
        array = ctypes.c_voidp( 12 )
        translated = ArrayDatatype.voidDataPointer( array )
        assert translated.value == array.value, translated

    def test_params_python3_strings( self ):
        try:
            glGetUniformBlockIndex( 0, unicode("Moo") )
        except ArgumentError:
            assert OpenGL.ERROR_ON_COPY, """Shouldn't have raised error on copy for unicode"""
        except TypeError:
            raise
        except GLError:
            # expected error, as we don't have a shader there...
            pass

    @pytest.mark.skipif( not np, reason="Numpy not available")
    def test_array_subclass( self ):
        s = Subclassed([0,1,2,3,4])
        result = arraydatatype.ArrayDatatype.asArray( s )
        assert isinstance( result, Subclassed )
    
    @pytest.mark.skipif( not np, reason="Numpy not available")
    def test_byte_count_numpy( self ):
        for a,expected in [
            (np.array([1,2],dtype='f'),8),
            (np.array([1,2],dtype='d'),16),
            (np.array([1,2],dtype='B'),2),
            (np.array([[1],[2]],dtype='B'),2),
            (np.float32(),4),
            (np.float64(),8),
        ]:
            handler = arraydatatype.ArrayDatatype.getHandler( a )
            
            assert type(a) in handler.HANDLED_TYPES, type(a)
            calculated = arraydatatype.ArrayDatatype.arrayByteCount( a )
            assert calculated == expected, "Byte count for %s was %s, expected %"%(
                a, calculated, expected,
            )
    def test_byte_count( self ):
        for a,expected in [
            (ctypes.c_float(),4),
            ((ctypes.c_float*3*4)(),4*3*4),
            
        ]:
            calculated = arraydatatype.ArrayDatatype.arrayByteCount( a )
            assert calculated == expected, "Byte count for %s was %s, expected %"%(
                a, calculated, expected,
            )
        
if np:
    class Subclassed( np.ndarray ):
        pass 
