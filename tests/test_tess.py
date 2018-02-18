import basetestcase
import os
from OpenGL.GL import *
from OpenGL.GLU import *
try:
    import numpy as np
except ImportError as err:
    np = None
HERE = os.path.abspath(os.path.dirname(__file__))

class TestTess( basetestcase.BaseTest ):
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
    def test_tess_collection( self ):
        """SF#2354596 tessellation combine results collected"""
        all_vertices = []
        combinations = []
        def start(*args):
            pass
        def stop(*args):
            pass
        def tessvertex(vertex_data, polygon_data=None):
            # polygon data *should* be collected here
            #assert polygon_data is all_vertices, polygon_data
            all_vertices.append(vertex_data)
            #collected.append( vertex_data )
            return polygon_data
        def tesscombine(coords, vertex_data, weights,_=None):
            new = (True,coords)
            combinations.append( coords )
            return new

        def tessedge(flag,*args,**named):
            pass	# dummy
        def tesserr( enum ):
            raise RuntimeError( gluErrorString( enum ) )

        # set up tessellator in CSG intersection mode
        tess=gluNewTess()
        gluTessProperty(tess, GLU_TESS_WINDING_RULE, GLU_TESS_WINDING_ABS_GEQ_TWO)
        gluTessCallback(tess, GLU_TESS_BEGIN, start)
        gluTessCallback(tess, GLU_TESS_END, stop)
        gluTessCallback(tess, GLU_TESS_EDGE_FLAG, tessedge)	# no strips
        gluTessCallback(tess, GLU_TESS_VERTEX, tessvertex)
        gluTessCallback(tess, GLU_TESS_ERROR, tesserr )
        gluTessCallback(tess, GLU_TESS_COMBINE, tesscombine)

        gluTessBeginPolygon(tess, all_vertices)
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
                        if np:
                            if OpenGL.ERROR_ON_COPY:
                                point = np.array( point, 'd' )
                            else:
                                point = np.array( point, 'f' )
                        else: 
                            point = (GLdouble*3)(*point)
                        gluTessVertex( tess, point, (False,point))
                finally:
                    gluTessEndContour(tess)
        finally:
            gluTessEndPolygon(tess)

        # Show collected triangle vertices :-
        # Original input vertices are marked as False.
        # Vertices generated in combine callback are marked as True.
        assert all_vertices, "Nothing collected"
        combined,original = [x for x in all_vertices if x[0]], [x for x in all_vertices if not x[0]]
        
        assert combined, ("No combined vertices", all_vertices )
        assert original, ("No original vertices", all_vertices )
        assert len(combinations) == 2, combinations
    
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
                    if np:
                        vertex = np.array((x/scale,y/scale,0.0),'d')
                    else:
                        vertex = (GLdouble*3)(x/scale,y/scale,0.0)
                    gluTessVertex(self.tess, vertex, vertex)
            finally:
                gluTessEndContour( self.tess )
        finally:
            gluTessEndPolygon(self.tess)
