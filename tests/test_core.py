#! /usr/bin/env python
import unittest, pygame, pygame.display, time, traceback, os, sys
import logging 
logging.basicConfig()

try:
    from numpy import *
except ImportError, err:
    try:
        from Numeric import *
    except ImportError, err:
        array = None

pygame.display.init()
import OpenGL 
OpenGL.CONTEXT_CHECKING = True
OpenGL.FORWARD_COMPATIBLE_ONLY = False
from OpenGL._bytes import bytes, _NULL_8_BYTE
from OpenGL.GL import *
try:
    glGetError()
except error.NoContext, err:
    # good, should have got this error 
    pass
else:
    raise RuntimeError( """Did not catch invalid context!""" )
from OpenGL import constants, error
from OpenGL.GLU import *
from OpenGL.arrays import arraydatatype
import OpenGL
from OpenGL.extensions import alternate
import ctypes
from OpenGL.GL.framebufferobjects import *
from OpenGL.GL.EXT.multi_draw_arrays import *
from OpenGL.GL.ARB.imaging import *

glMultiDrawElements = alternate( 
    glMultiDrawElementsEXT, glMultiDrawElements, 
)


class Tests( unittest.TestCase ):
    evaluator_ctrlpoints = [[[ -1.5, -1.5, 4.0], [-0.5, -1.5, 2.0], [0.5, -1.5,
        -1.0], [1.5, -1.5, 2.0]], [[-1.5, -0.5, 1.0], [-0.5, -0.5, 3.0], [0.5, -0.5,
        0.0], [1.5, -0.5, -1.0]], [[-1.5, 0.5, 4.0], [-0.5, 0.5, 0.0], [0.5, 0.5,
        3.0], [1.5, 0.5, 4.0]], [[-1.5, 1.5, -2.0], [-0.5, 1.5, -2.0], [0.5, 1.5,
        0.0], [1.5, 1.5, -1.0]]]
    width = height = 300
    def setUp( self ):
        """Set up the operation"""
        
        self.screen = pygame.display.set_mode(
            (self.width,self.height),
            pygame.OPENGL | pygame.DOUBLEBUF,
        )
        
        pygame.display.set_caption('Testing system')
        pygame.key.set_repeat(500,30)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, 300/300., 1.0, 20.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            -2,0,3, # eyepoint
            0,0,0, # center-of-view
            0,1,0, # up-vector
        )
        glClearColor( 0,0,.25, 0 )
        glClear( GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT )
    
    def tearDown( self ):
        glFlush()
        pygame.display.flip()
        time.sleep( .25 )
        #raw_input( 'Okay? ' )
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
    if (not OpenGL.ERROR_ON_COPY) or array:	
        def test_evaluator( self ):
            """Test whether the evaluator functions work"""
            glDisable(GL_CULL_FACE)
            glEnable(GL_MAP2_VERTEX_3)
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_NORMALIZE)
            if array:
                ctrl_points = array( self.evaluator_ctrlpoints,'f')
            else:
                ctrl_points = self.evaluator_ctrlpoints
            glMap2f(GL_MAP2_VERTEX_3, 0, 1, 0, 1, ctrl_points)
            glMapGrid2f(20, 0.0, 1.0, 20, 0.0, 1.0)
            glShadeModel(GL_FLAT)
            glEvalMesh2(GL_FILL, 0, 20, 0, 20)
            glTranslatef( 0,0.001, 0 )
            glEvalMesh2(GL_POINT, 0, 20, 0, 20)
    def test_nurbs_raw( self ):
        """Test nurbs rendering using raw API calls"""
        from OpenGL.raw import GLU 
        knots = (constants.GLfloat* 8) ( 0,0,0,0,1,1,1,1 )
        ctlpoints = (constants.GLfloat*(3*4*4))( -3., -3., -3.,
            -3., -1., -3.,
            -3.,  1., -3.,
            -3.,  3., -3.,

        -1., -3., -3.,
            -1., -1.,  3.,
            -1.,  1.,  3.,
            -1.,  3., -3.,

        1., -3., -3.,
             1., -1.,  3.,
             1.,  1.,  3.,
             1.,  3., -3.,

        3., -3., -3.,
            3., -1., -3.,
             3.,  1., -3.,
             3.,  3., -3. )
        theNurb = gluNewNurbsRenderer()
        GLU.gluBeginSurface(theNurb)
        GLU.gluNurbsSurface(
            theNurb, 
            8, ctypes.byref(knots), 8, ctypes.byref(knots),
            4 * 3, 3, ctypes.byref( ctlpoints ),
            4, 4, GL_MAP2_VERTEX_3
        )
        GLU.gluEndSurface(theNurb)
    if array:
        def test_nurbs_raw_arrays( self ):
            """Test nurbs rendering using raw API calls with arrays"""
            from OpenGL.raw import GLU 
            import numpy
            knots = numpy.array( ( 0,0,0,0,1,1,1,1 ), 'f' )
            ctlpoints = numpy.array( [[[-3., -3., -3.],
                [-3., -1., -3.],
                [-3.,  1., -3.],
                [-3.,  3., -3.]],

            [[-1., -3., -3.],
                [-1., -1.,  3.],
                [-1.,  1.,  3.],
                [-1.,  3., -3.]],

            [[ 1., -3., -3.],
                [ 1., -1.,  3.],
                [ 1.,  1.,  3.],
                [ 1.,  3., -3.]],

            [[ 3., -3., -3.],
                [ 3., -1., -3.],
                [ 3.,  1., -3.],
                [ 3.,  3., -3.]]], 'f' )
            theNurb = GLU.gluNewNurbsRenderer()
            GLU.gluBeginSurface(theNurb)
            GLU.gluNurbsSurface(
                theNurb, 
                8, knots, 8, knots,
                4 * 3, 3, ctlpoints ,
                4, 4, GL_MAP2_VERTEX_3
            )
            GLU.gluEndSurface(theNurb)
        def test_nurbs( self ):
            """Test nurbs rendering"""
            from OpenGL.raw import GLU 
            def buildControlPoints( ):
                ctlpoints = zeros( (4,4,3), 'd')
                for u in range( 4 ):
                    for v in range( 4):
                        ctlpoints[u][v][0] = 2.0*(u - 1.5)
                        ctlpoints[u][v][1] = 2.0*(v - 1.5);
                        if (u == 1 or u ==2) and (v == 1 or v == 2):
                            ctlpoints[u][v][2] = 3.0;
                        else:
                            ctlpoints[u][v][2] = -3.0;
                return ctlpoints
            controlPoints = buildControlPoints()
            theNurb = GLU.gluNewNurbsRenderer()[0]
            #theNurb = gluNewNurbsRenderer();
            gluNurbsProperty(theNurb, GLU_SAMPLING_TOLERANCE, 25.0);
            gluNurbsProperty(theNurb, GLU_DISPLAY_MODE, GLU_FILL);
            knots= array ([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0], "d")
            glPushMatrix();
            try:
                glRotatef(330.0, 1.,0.,0.);
                glScalef (0.5, 0.5, 0.5);

                gluBeginSurface(theNurb);
                try:
                    gluNurbsSurface(
                        theNurb,
                        knots, knots,
                        controlPoints,
                        GL_MAP2_VERTEX_3
                    );
                finally:
                    gluEndSurface(theNurb);
            finally:
                glPopMatrix();
    def test_errors( self ):
        """Test for error catching/checking"""
        try:
            glClear( GL_INVALID_VALUE )
        except Exception, err:
            assert err.err == 1281, ("""Expected invalid value (1281)""", err.err)
        else:
            raise RuntimeError( """No error on invalid glClear""" )
        try:
            glColorPointer(GL_INVALID_VALUE,GL_BYTE,0,None)
        except Exception, err:
            assert err.err == 1281, ("""Expected invalid value (1281)""", err.err)
            assert err.baseOperation, err.baseOperation
            assert err.pyArgs == (GL_INVALID_VALUE, GL_BYTE, 0, None), err.pyArgs
            assert err.cArgs == (GL_INVALID_VALUE, GL_BYTE, 0, None), err.cArgs
        else:
            raise RuntimeError( """No error on invalid glColorPointer""" )
        try:
            glBitmap(-1,-1,0,0,0,0,"")
        except Exception, err:
            assert err.err in (1281,1282), ("""Expected invalid value (1281) or invalid operation (1282)""", err.err)
        else:
            raise RuntimeError( """No error on invalid glBitmap""" )
    def test_quadrics( self ):
        """Test for rendering quadric objects"""
        quad = gluNewQuadric()
        glColor3f( 1,0, 0 )
        gluSphere( quad, 1.0, 16, 16 )
    if not OpenGL.ERROR_ON_COPY:
        def test_simple( self ):
            """Test for simple vertex-based drawing"""
            glDisable( GL_LIGHTING )
            glBegin( GL_TRIANGLES )
            try:
                try:
                    glVertex3f( 0.,1.,0. )
                except Exception, err:
                    traceback.print_exc()
                glVertex3fv( [-1,0,0] )
                glVertex3dv( [1,0,0] )
                try:
                    glVertex3dv( [1,0] )
                except ValueError, err:
                    #Got expected value error (good)
                    pass
                else:
                    raise RuntimeError(
                        """Should have raised a value error on passing 2-element array to 3-element function!""",
                    )
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
    if not OpenGL.ERROR_ON_COPY:
        def test_pointers( self ):
            """Test that basic pointer functions work"""
            vertex = constants.GLdouble * 3
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
                ctypes.cast( myVector, ctypes.POINTER(constants.GLdouble)) 
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
            result = glVertexPointer( 4,GL_INT,0,s )
        TESS_TEST_SHAPE = [
                [191,   0],
                [ 191, 1480],
                [ 191, 1480],
                [ 401, 1480],
                [ 401, 1480],
                [401,   856],
                [401,   856],
                [1105,  856],
                [1105,  856],
                [1105, 1480],
                [1105, 1480],
                [1315, 1480],
                [1315, 1480],
                [1315,    0],
                [1315,    0],
                [1105,    0],
                [1105,    0],
                [1105,  699],
                [1105,  699],
                [401,   699],
                [401,   699],
                [401,     0],
                [401,     0],
                [191,     0],
                [191,     0],
                [191,     0],
            ]
        def test_tess(self ):
            """Test that tessellation works"""
            glDisable( GL_LIGHTING )
            glColor3f( 1,1,1 )
            glNormal3f( 0,0,1 )
            def begin( *args ):
                return glBegin( *args )
            def vertex( *args ):
                return glVertex3dv( *args )
            def end( *args ):
                return glEnd( *args )
            def combine( coords, vertex_data, weight):
                return coords
            tobj = gluNewTess()
            gluTessCallback(tobj, GLU_TESS_BEGIN, begin);
            gluTessCallback(tobj, GLU_TESS_VERTEX, vertex); 
            gluTessCallback(tobj, GLU_TESS_END, end); 
            gluTessCallback(tobj, GLU_TESS_COMBINE, combine); 
            gluTessBeginPolygon(tobj, None); 
            gluTessBeginContour(tobj);
            for (x,y) in self.TESS_TEST_SHAPE:
                vert = (x,y,0.0)
                gluTessVertex(tobj, vert, vert);
            gluTessEndContour(tobj); 
            gluTessEndPolygon(tobj);
        def test_texture( self ):
            """Test texture (requires OpenGLContext and PIL)"""
            try:
                from OpenGLContext import texture
                import Image 
                from OpenGL.GLUT import glutSolidTeapot
            except ImportError, err:
                pass
            else:
                glEnable( GL_TEXTURE_2D )
                ourTexture = texture.Texture(
                    Image.open( 'yingyang.png' )
                )
                ourTexture()
                
                glEnable( GL_LIGHTING )
                glEnable( GL_LIGHT0 )
                glBegin( GL_TRIANGLES )
                try:
                    try:
                        glTexCoord2f( .5, 1 )
                        glVertex3f( 0.,1.,0. )
                    except Exception, err:
                        traceback.print_exc()
                    glTexCoord2f( 0, 0 )
                    glVertex3fv( [-1,0,0] )
                    glTexCoord2f( 1, 0 )
                    glVertex3dv( [1,0,0] )
                    try:
                        glVertex3dv( [1,0] )
                    except ValueError, err:
                        #Got expected value error (good)
                        pass
                    else:
                        raise RuntimeError(
                            """Should have raised a value error on passing 2-element array to 3-element function!""",
                        )
                finally:
                    glEnd()
    if array:
        def test_numpyConversion( self ):
            """Test that we can run a numpy conversion from double to float for glColorArray"""
            import numpy
            a = numpy.arange( 0,1.2, .1, 'd' ).reshape( (-1,3 ))
            glEnableClientState(GL_VERTEX_ARRAY)
            try:
                glColorPointerf( a )
                glColorPointerd( a )
            finally:
                glDisableClientState( GL_VERTEX_ARRAY )
    def test_constantPickle( self ):
        """Test that our constants can be pickled/unpickled properly"""
        import pickle, cPickle
        for p in pickle,cPickle:
            v = p.loads( p.dumps( GL_VERTEX_ARRAY ))
            assert v == GL_VERTEX_ARRAY, (v,GL_VERTEX_ARRAY)
            assert v.name == GL_VERTEX_ARRAY.name, v.name 
    
    if not OpenGL.ERROR_ON_COPY:
        def test_copyNonContiguous( self ):
            """Test that a non-contiguous (transposed) array gets applied as a copy"""
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix( )
            try:
                import numpy
                transf = numpy.identity(4, dtype=numpy.float32)
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

                assert not numpy.allclose( transposed, untransposed ), (transposed, untransposed)
                
                t2 = transf.transpose()
                # This doesn't work:
                glLoadIdentity()
                glMultMatrixf(t2)
                # This does work:
                #glMultMatrixf(transf.transpose().copy())
                transposed = glGetFloatv(GL_MODELVIEW_MATRIX)
                
                assert not numpy.allclose( transposed, untransposed ), (transposed, untransposed)
            finally:
                glMatrixMode(GL_MODELVIEW)
                glPopMatrix()
    def test_nullTexture( self ):
        """Test that we can create null textures"""
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 512, 512, 0, GL_RGB, GL_INT, None)
    
    def test_nonFloatColor( self ):
        """Test that we handle non-floating-point colour inputs"""
        for notFloat,shouldWork in ((0,True), (object(),False), (object,False)):
            try:
                glColor4f( 0,1,1,notFloat )
            except Exception, err:
                if shouldWork:
                    raise 
            else:
                if not shouldWork:
                    raise RuntimeError( """Expected failure for non-float value %s, succeeded"""%( notFloat, ))
    someData = [ (0,255,0)]
    def test_glAreTexturesResident( self ):
        """Test that PyOpenGL api for glAreTexturesResident is working
        
        Note: not currently working on AMD64 Linux for some reason
        """
        import numpy
        textures = glGenTextures(2)
        residents = []
        data = numpy.array( self.someData,'i' )
        for texture in textures:
            glBindTexture( GL_TEXTURE_2D,int(texture) )
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, 1, 1, 0, GL_RGB, GL_INT, data)
            residents.append(
                glGetTexParameteriv(GL_TEXTURE_2D, GL_TEXTURE_RESIDENT )
            )
        error.glCheckError(None)
        result = glAreTexturesResident( textures)
        assert len(result) == 2
        for (tex,expected,found) in zip( textures, residents, result ):
            if expected != found:
                print 'Warning: texture %s residence expected %s got %s'%( tex, expected, found )
        
    if OpenGL.ALLOW_NUMPY_SCALARS:
        def test_passBackResults( self ):
            """Test ALLOW_NUMPY_SCALARS to allow numpy scalars to be passed in"""
            textures = glGenTextures(2)
            glBindTexture( GL_TEXTURE_2D, textures[0] )
    if array:
        def test_arrayTranspose( self ):
            import numpy
            m = glGetFloatv( GL_MODELVIEW_MATRIX )
            glMatrixMode( GL_MODELVIEW )
            glLoadIdentity()

            t = eye(4)
            t[3,0] = 20.0

            # the following glMultMatrixf call ignored this transpose
            t = t.T

            glMultMatrixf( t )

            m = glGetFloatv( GL_MODELVIEW_MATRIX )
            assert numpy.allclose( m[-1], [0,0,0,1] ), m
    def test_glreadpixelsf( self ):
        """Issue #1979002 crash due to mis-calculation of resulting array size"""
        width,height = self.width, self.height
        readback_image1 = glReadPixelsub(0,0,width,height,GL_RGB)
        readback_image2 = glReadPixelsf(0,0,width,height,GL_RGB)
    def test_glreadpixels_is_string( self ):
        """Issue #1959860 incompatable change to returning arrays reversed"""
        width,height = self.width, self.height
        readback_image1 = glReadPixels(0,0,width,height,GL_RGB, GL_UNSIGNED_BYTE)
        assert isinstance( readback_image1, str ), type( readback_image1 )
        readback_image1 = glReadPixels(0,0,width,height,GL_RGB, GL_BYTE)
        assert not isinstance( readback_image1, str ), type(readback_image2)
    
    if array:
        def test_glreadpixels_warray( self ):
            """SF#1311265 allow passing in the array object"""
            width,height = self.width, self.height
            data = zeros( (width,height,3), 'B' )
            image1 = glReadPixelsub(0,0,width,height,GL_RGB,array=data)
            
        def test_mmap_data( self ):
            """Test that we can use mmap data array
            
            If we had a reasonable lib that dumped raw image data to a shared-mem file
            we might be able to use this for movie display :) 
            """
            fh = open( 'mmap-test-data.dat', 'wb+' )
            fh.write( _NULL_8_BYTE*(32*32*3+1))
            fh.flush()
            fh.close()
            # using numpy.memmap here...
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
            import numpy
            from OpenGL.arrays import vbo
            assert vbo.get_implementation()
            dt = arraydatatype.GLdoubleArray
            array = numpy.array( [
                [0,0,0],
                [0,1,0],
                [1,.5,0],
                [1,0,0],
                [1.5,.5,0],
                [1.5,0,0],
            ], dtype='d')
            indices = numpy.array(
                range(len(array)),
                'i',
            )
            d = vbo.VBO(array)
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
                    lastPoint = numpy.array( [[1.5,(1/255.) * float(x),0]] )
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
    def test_fbo( self ):
        """Test that we support framebuffer objects
        
        http://www.gamedev.net/reference/articles/article2331.asp
        """
        if not glGenFramebuffers:
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
            print 'OpenGL 1.2 support'
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
                print 'No multi_draw_arrays support'
    def test_glDrawBuffers_list( self ):
        """Test that glDrawBuffers with list argument doesn't crash"""
        a_type = constants.GLenum*2
        args = a_type(
            GL_COLOR_ATTACHMENT0,
            GL_COLOR_ATTACHMENT1,
        )
        try:
            glDrawBuffers( 2, args )
        except GLError, err:
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
            a_type = constants.GLenum*2
            drawingBuffers = a_type(
                GL_COLOR_ATTACHMENT0, 
                GL_COLOR_ATTACHMENT1,
            )
            glDrawBuffers(2, drawingBuffers )
            try:
                checkFramebufferStatus()
            except error.GLError, err:
                pass
            else:
                glReadBuffer( GL_COLOR_ATTACHMENT1 )
                pixels = glReadPixels( 0,0, 10,10, GL_RGB, GL_UNSIGNED_BYTE )
                assert len(pixels) == 300, len(pixels)
        finally:
            glBindFramebuffer( GL_FRAMEBUFFER, 0 )
        
        glReadBuffer( previous )
        
    def test_enable_histogram( self ):
        if glInitImagingARB():
            glHistogram(GL_HISTOGRAM, 256, GL_LUMINANCE, GL_FALSE)
            glEnable( GL_HISTOGRAM )
            glDisable( GL_HISTOGRAM )
        else:
            print 'No ARB imaging extension'
    if not OpenGL.ERROR_ON_COPY:
        def test_gluNurbsCurve( self ):
            """Test that gluNurbsCurve raises error on invalid arguments"""
            nurb = gluNewNurbsRenderer()
            gluBeginCurve( nurb )
            self.failUnlessRaises( error.GLUerror,
                gluNurbsCurve,
                    nurb, 
                    [0, 1.0],
                    [[0,0,0],[1,0,0],[1,1,0]],
                    GL_MAP1_VERTEX_3,
            )
            self.failUnlessRaises( error.GLUerror,
                gluNurbsCurve,
                    nurb, 
                    [],
                    [[0,0,0],[1,0,0],[1,1,0]],
                    GL_MAP1_VERTEX_3,
            )
            self.failUnlessRaises( error.GLUerror,
                gluNurbsCurve,
                    nurb, 
                    [],
                    [],
                    GL_MAP1_VERTEX_3,
            )
    def test_get_version( self ):
        from OpenGL.extensions import getGLVersion
        version = getGLVersion()
        if version >= [2,0]:
            assert glShaderSource
            assert glUniform1f
        else:
            assert not glShaderSource
            assert not glUniform1f
    
    def test_tess_collection( self ):
        """SF#2354596 tessellation combine results collected"""
        def start(typ=None):
            print 'start', typ
        def tessvertex(vertex_data, polygon_data):
            # polygon data *should* be collected here
            assert polygon_data is collected, polygon_data
            polygon_data.append(vertex_data)
            #collected.append( vertex_data )
            return polygon_data
        combined = []
        def tesscombine(coords, vertex_data, weight):
            combined.append( coords )
            return (True,coords)	# generated vertices marked as True

        def tessedge(flag,*args,**named):
            pass	# dummy
        collected=[]	# collect triangle vertices

        # set up tessellator in CSG intersection mode
        tess=gluNewTess()
        gluTessProperty(tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_ABS_GEQ_TWO)
        gluTessCallback(tess, GLU_TESS_BEGIN, glBegin)
        gluTessCallback(tess, GLU_TESS_END, glEnd)
        gluTessCallback(tess, GLU_TESS_COMBINE,      tesscombine)
        gluTessCallback(tess, GLU_TESS_EDGE_FLAG,    tessedge)	# no strips
        gluTessCallback(tess, GLU_TESS_VERTEX_DATA,  tessvertex)

        gluTessBeginPolygon(tess, collected)
        try:
            for contour in [
                # first square
                [(-1,0,-1),(1,0,-1),(1,0,1),(-1,0,1)],
                # second intersects the first
                [(.5,0,-.5),(1.5,0,-.5),(1.5,0,.5),(.5,0,.5)],
            ]:
                
                gluTessBeginContour(tess)
                try:
                    for point in contour:
                        point = array( point, 'f' )
                        gluTessVertex( tess, point, (False,point))
                finally:
                    gluTessEndContour(tess)
        finally:
            result = gluTessEndPolygon(tess)

        assert len(combined) == 2, "Should have generated two new vertices"
        # Show collected triangle vertices :-
        # Original input vertices are marked as False.
        # Vertices generated in combine callback are marked as True.
        assert collected
    
    def test_tess_cb_traditional( self ):
        outline = [
            [191,   0],
            [ 191, 1480],
            [ 191, 1480],
            [ 401, 1480],
            [ 401, 1480],
            [401,   856],
            [401,   856],
            [1105,  856],
            [1105,  856],
            [1105, 1480],
            [1105, 1480],
            [1315, 1480],
            [1315, 1480],
            [1315,    0],
            [1315,    0],
            [1105,    0],
            [1105,    0],
            [1105,  699],
            [1105,  699],
            [401,   699],
            [401,   699],
            [401,     0],
            [401,     0],
            [191,     0],
            [191,     0],
            [191,     0],
        ]
        scale = 1200.
        self.tess = gluNewTess()
        gluTessCallback(self.tess, GLU_TESS_BEGIN, glBegin)
        def test( t, polyData=None ):
            glNormal( 0,0, -1 )
            glColor3f( t[0],t[1],t[2] )
            return glVertex3f( t[0],t[1],t[2])
        gluTessCallback(self.tess, GLU_TESS_VERTEX_DATA, test)
        gluTessCallback(self.tess, GLU_TESS_END, glEnd);
        combined = []
        def combine( points, vertices, weights ):
            #print 'combine called', points, vertices, weights
            combined.append( points )
            return points
        gluTessCallback(self.tess, GLU_TESS_COMBINE, combine)
        gluTessBeginPolygon( self.tess, None )
        try:
            gluTessBeginContour( self.tess )
            try:
                for (x,y) in outline:
                    vertex = array((x/scale,y/scale,0.0),'d')
                    gluTessVertex(self.tess, vertex, vertex)
            finally:
                gluTessEndContour( self.tess )
        finally:
            gluTessEndPolygon(self.tess)
        
    
    def test_get_boolean_bitmap( self ):
        # should not raise error
        value = glGetBoolean(GL_TEXTURE_2D)
    if array:
        def test_draw_bitmap_pixels( self ):
            """SF#2152623 Drawing pixels as bitmaps (bits)"""
            pixels = array([0,0,0,0,0,0,0,0],'B')
            glDrawPixels( 8,8, GL_COLOR_INDEX, GL_BITMAP, pixels )
    
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
        glCallLists([second]) # replace with gCallList(2)
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
        assert depth == (0,), depth # have popped, but even then, were' not in the mode...

        glSelectBuffer (100)
        glRenderMode (GL_SELECT)
        glCallList(1)
        depth = glGetIntegerv( GL_NAME_STACK_DEPTH )
        assert depth == (1,), depth # should have a single record
        glPopName()
        records = glRenderMode (GL_RENDER)
        # reporter says sees two records, Linux sees none, Win32 sees 1 :(
        assert len(records) == 1, records
    
    def test_get_max_tex_units( self ):
        """SF#2895081 glGetIntegerv( GL_MAX_TEXTURE_IMAGE_UNITS )"""
        units = glGetIntegerv( GL_MAX_TEXTURE_IMAGE_UNITS )
        
        
if __name__ == "__main__":
    unittest.main()
    pygame.display.quit()
    pygame.quit()
