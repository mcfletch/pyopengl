import basetestcase
import os, logging
import OpenGL
from OpenGL.GL import *
from OpenGL import GLU
try:
    import numpy as np
except ImportError as err:
    np = None
HERE = os.path.abspath(os.path.dirname(__file__))
log = logging.getLogger(__name__)

class TestEvaluators(basetestcase.BaseTest):
    evaluator_ctrlpoints = [[[ -1.5, -1.5, 4.0], [-0.5, -1.5, 2.0], [0.5, -1.5,
        -1.0], [1.5, -1.5, 2.0]], [[-1.5, -0.5, 1.0], [-0.5, -0.5, 3.0], [0.5, -0.5,
        0.0], [1.5, -0.5, -1.0]], [[-1.5, 0.5, 4.0], [-0.5, 0.5, 0.0], [0.5, 0.5,
        3.0], [1.5, 0.5, 4.0]], [[-1.5, 1.5, -2.0], [-0.5, 1.5, -2.0], [0.5, 1.5,
        0.0], [1.5, 1.5, -1.0]]]
    if (not OpenGL.ERROR_ON_COPY) or array:	
        def test_evaluator( self ):
            """Test whether the evaluator functions work"""
            glDisable(GL_CULL_FACE)
            glEnable(GL_MAP2_VERTEX_3)
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_NORMALIZE)
            if np:
                ctrl_points = np.array( self.evaluator_ctrlpoints,'f')
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
        from OpenGL.raw import GLU as GLU_raw
        knots = (GLfloat* 8) ( 0,0,0,0,1,1,1,1 )
        ctlpoints = (GLfloat*(3*4*4))( -3., -3., -3.,
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
        theNurb = GLU_raw.gluNewNurbsRenderer()
        GLU_raw.gluBeginSurface(theNurb)
        GLU_raw.gluNurbsSurface(
            theNurb, 
            8, ctypes.byref(knots), 8, ctypes.byref(knots),
            4 * 3, 3, ctypes.byref( ctlpoints ),
            4, 4, GL_MAP2_VERTEX_3
        )
        GLU_raw.gluEndSurface(theNurb)
    if np:
        def test_nurbs_raw_arrays( self ):
            """Test nurbs rendering using raw API calls with arrays"""
            from OpenGL.raw import GLU as GLU_raw 
            knots = np.array( ( 0,0,0,0,1,1,1,1 ), 'f' )
            ctlpoints = np.array( [[[-3., -3., -3.],
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
            theNurb = GLU_raw.gluNewNurbsRenderer()
            GLU_raw.gluBeginSurface(theNurb)
            GLU_raw.gluNurbsSurface(
                theNurb, 
                8, knots, 8, knots,
                4 * 3, 3, ctlpoints ,
                4, 4, GL_MAP2_VERTEX_3
            )
            GLU_raw.gluEndSurface(theNurb)
        def test_nurbs( self ):
            """Test nurbs rendering"""
            def buildControlPoints( ):
                ctlpoints = np.zeros( (4,4,3), 'f')
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
            theNurb = GLU.gluNewNurbsRenderer()
            GLU.gluNurbsProperty(theNurb, GLU.GLU_SAMPLING_TOLERANCE, 25.0);
            GLU.gluNurbsProperty(theNurb, GLU.GLU_DISPLAY_MODE, GLU.GLU_FILL);
            knots= np.array ([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0], "f")
            glPushMatrix();
            try:
                glRotatef(330.0, 1.,0.,0.);
                glScalef (0.5, 0.5, 0.5);

                GLU.gluBeginSurface(theNurb);
                try:
                    GLU.gluNurbsSurface(
                        theNurb,
                        knots, knots,
                        controlPoints,
                        GL_MAP2_VERTEX_3
                    );
                finally:
                    GLU.gluEndSurface(theNurb);
            finally:
                glPopMatrix();
    def test_quadrics( self ):
        """Test for rendering quadric objects"""
        quad = GLU.gluNewQuadric()
        glColor3f( 1,0, 0 )
        GLU.gluSphere( quad, 1.0, 16, 16 )

    if not OpenGL.ERROR_ON_COPY:
        def test_gluNurbsCurve( self ):
            """Test that gluNurbsCurve raises error on invalid arguments"""
            nurb = GLU.gluNewNurbsRenderer()
            GLU.gluBeginCurve( nurb )
            if OpenGL.ERROR_CHECKING:
                self.assertRaises( error.GLUerror,
                    GLU.gluNurbsCurve,
                        nurb, 
                        [0, 1.0],
                        [[0,0,0],[1,0,0],[1,1,0]],
                        GL_MAP1_VERTEX_3,
                )
                self.assertRaises( error.GLUerror,
                    GLU.gluNurbsCurve,
                        nurb, 
                        [],
                        [[0,0,0],[1,0,0],[1,1,0]],
                        GL_MAP1_VERTEX_3,
                )
                self.assertRaises( error.GLUerror,
                    GLU.gluNurbsCurve,
                        nurb, 
                        [],
                        [],
                        GL_MAP1_VERTEX_3,
                )

    def test_gle( self ):
        from OpenGL.GLE import (
            gleSetJoinStyle,
            TUBE_NORM_EDGE, TUBE_JN_ANGLE, TUBE_JN_CAP,
            glePolyCone,
        )
        if (gleSetJoinStyle):
            gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ANGLE | TUBE_JN_CAP)
            glePolyCone(((-6.0, 6.0, 0.0), (6.0, 6.0, 0.0), (6.0, -6.0, 0.0), (-6.0, -6.0, 0.0), (-6.0, 6.0, 0.0), (6.0, 6.0, 0.0)),
                                ((0.0, 0.0, 0.0), (0.0, 0.8, 0.3), (0.8, 0.3, 0.0), (0.2, 0.3, 0.9), (0.2, 0.8, 0.5), (0.0, 0.0, 0.0)), (1, 1, 3, 0.5, 2, 1))
        else:
            log.warn("No GLE extrusion library")
