"""Implementation of OpenGL constant objects"""
import sys
from OpenGL._bytes import bytes,unicode,as_8_bit, long, integer_types, maxsize
from OpenGL import _configflags

class Constant( object ):
    """OpenGL constant that displays itself as a name rather than a value

    The purpose of this class is to make debugging OpenGL code easier,
    as you recieve messages that say what value you passed in in a
    human-readable form, rather than as a bald number that requires
    lookup and disambiguation in the header file.
    """
    def __new__( cls, name, value=None ):
        """Initialise the constant with the given name and value"""
        if not isinstance( value, Constant ):
            if isinstance( value, float ) and cls is not FloatConstant:
                return FloatConstant( name, value )
            elif isinstance( value, int ) and cls is not IntConstant:
                return IntConstant( name, value )
            elif isinstance( value, long ) and cls is not LongConstant:
                return LongConstant( name, value )
            elif isinstance( value, (bytes,unicode) ) and cls is not StringConstant:
                return StringConstant( name, as_8_bit(value) )
        if isinstance( value, integer_types ):
            if value > maxsize:
                # Two's-complement wrap into the platform's signed range so the
                # value round-trips through ctypes.  e.g. GL_TIMEOUT_IGNORED
                # 0xFFFFFFFFFFFFFFFF -> -1 (ctypes c_uint64(-1) == 0xFFFF...FFFF).
                # The old '-(value & maxsize)' produced -0x7FFF...FFFF instead.
                value = value - 2 * (maxsize + 1)
        base = super(Constant,cls).__new__( cls, value )
        base.name = name
        if _configflags.MODULE_ANNOTATIONS:
            frame = sys._getframe().f_back
            if frame and frame.f_back and '__name__' in frame.f_back.f_globals:
                base.__module__ = frame.f_back.f_globals['__name__']
        return base
    def __repr__( self ):
        """Return the name, rather than the bald value"""
        return self.name
    def __getnewargs__( self ):
        """Produce the new arguments for recreating the instance"""
        return (self.name,) + super( Constant, self ).__getnewargs__()

class NumericConstant( Constant ):
    """Base class for numeric-value constants"""
    def __str__( self ):
        """Return the value as a human-friendly string"""
        return '%s (%s)'%(self.name,super(Constant,self).__str__())
    def __getstate__(self):
        """Retrieve state for pickle and the like"""
        return self.name
    def __setstate__( self, state ):
        self.name = state

class IntConstant( NumericConstant, int ):
    """Integer constant"""
if int is not long:
    class LongConstant( NumericConstant, long ):
        """Long integer constant"""
else:
    LongConstant = IntConstant
class FloatConstant( NumericConstant, float ):
    """Float constant"""

class StringConstant( Constant, bytes ):
    """String constants"""
    def __repr__( self ):
        """Return the value as a human-friendly string"""
        return '%s (%s)'%(self.name,super(Constant,self).__str__())

def declared( name, value, module ):
    """A constant that reports ``module`` as the module declaring it

    ``Constant`` takes the module from the frame that built it, which is the
    right answer only while each module builds its own constants.  The
    declaration tables build them all from one place, so that guess would name
    the loader for every constant in the library; this says which module the
    declaration belongs to instead.

    Under the default ``MODULE_ANNOTATIONS`` nothing is recorded at all, here
    or in ``Constant``, and this is ``Constant`` with an argument it ignores.
    """
    constant = Constant( name, value )
    if _configflags.MODULE_ANNOTATIONS:
        constant.__module__ = module
    return constant


if __name__ == "__main__":
    x = IntConstant( 'testint', 3 )
    y = FloatConstant( 'testfloat', 3.0 )
    z = StringConstant( 'teststr', 'some testing string' )

    import pickle
    for val in x,y,z:
        restored = pickle.loads( pickle.dumps( val ))
        assert restored == val, (str(restored),str(val))
        assert restored.name == val.name, (restored.name,val.name)
