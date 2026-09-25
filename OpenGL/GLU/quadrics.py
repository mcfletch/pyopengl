"""Wrapper/Implementation of the GLU quadrics object for PyOpenGL"""
from OpenGL.raw import GLU as _simple
from OpenGL.platform import createBaseFunction, PLATFORM
import ctypes
from typing import ClassVar

class GLUQuadric( _simple.GLUquadric ):
    """Implementation class for GLUQuadric classes in PyOpenGL"""
    FUNCTION_TYPE = PLATFORM.functionTypeFor(PLATFORM.GLU)
    CALLBACK_TYPES: ClassVar[dict] = {
        # mapping from "which" GLU enumeration to a ctypes function type
        _simple.GLU_ERROR : FUNCTION_TYPE( None, _simple.GLenum )
    }
    #: mapping from "which" to a registrar with the proper callback argtype;
    #: filled in below once the class (and so POINTER(GLUQuadric)) exists.
    CALLBACK_FUNCTION_REGISTRARS: ClassVar[dict] = {}
    def getAsParam( self ):
        """Pass instances by pointer; gluNewQuadric returns the dereferenced struct"""
        return ctypes.pointer( self )
    _as_parameter_ = property( getAsParam )
    def addCallback( self, which, function ):
        """Register a callback for the quadric object

        At the moment only GLU_ERROR is supported by OpenGL, but
        we allow for the possibility of more callbacks in the future...
        """
        callbackType = self.CALLBACK_TYPES.get( which )
        if not callbackType:
            raise ValueError(
                """Don't have a registered callback type for %r"""%(
                    which,
                )
            )
        if not isinstance( function, callbackType ):
            cCallback = callbackType( function )
        else:
            cCallback = function
        self.CALLBACK_FUNCTION_REGISTRARS[ which ]( self, which, cCallback )
        # XXX catch errors!
        if getattr( self, 'callbacks', None ) is None:
            self.callbacks = {}
        self.callbacks[ which ] = cCallback
        return cCallback
GLUquadric = GLUQuadric

# A registrar per callback type; the raw gluQuadricCallback has a generic
# function-pointer argtype that ffi cannot prepare, so build a typed one.
GLUQuadric.CALLBACK_FUNCTION_REGISTRARS = dict(
    (
        which,
        createBaseFunction(
            'gluQuadricCallback', dll=PLATFORM.GLU, resultType=None,
            argTypes=[ctypes.POINTER(GLUQuadric), _simple.GLenum, funcType],
            doc='gluQuadricCallback( POINTER(GLUQuadric)(quadric), GLenum(which), _GLUfuncptr(CallBackFunc) ) -> None',
            argNames=('quadric', 'which', 'CallBackFunc'),
        ),
    )
    for (which, funcType) in GLUQuadric.CALLBACK_TYPES.items()
)

def gluQuadricCallback( quadric, which=_simple.GLU_ERROR, function=None ):
    """Set the GLU error callback function"""
    return quadric.addCallback( which, function )

# Override to produce instances of the sub-class...
_gluNewQuadric = createBaseFunction(
    'gluNewQuadric', dll=PLATFORM.GLU, resultType=ctypes.POINTER(GLUQuadric),
    argTypes=[],
    doc="""gluNewQuadric(  ) -> GLUQuadric

Create a new GLUQuadric object""",
    argNames=[],
)

def gluNewQuadric():
    """Create a new GLUQuadric object (dereferenced, as for tess/nurbs)"""
    # Returning the struct (not the bare pointer) lets gluQuadricCallback find
    # addCallback and keeps the callback alive on the object the caller holds.
    return _gluNewQuadric()[0]

__all__ = (
    'gluNewQuadric',
    'gluQuadricCallback',
    'GLUQuadric',
)
