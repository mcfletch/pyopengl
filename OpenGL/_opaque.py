"""Data-type definitions for EGL/GLES"""
import ctypes
pointer = ctypes.pointer

class _Opaque( ctypes.Structure ):
    """An Opaque Structure reference (base class)"""
class _opaque_pointer( ctypes.POINTER( _Opaque ) ):
    """A handle: an address, and the kind of thing it is a handle to.

    Two of these naming the same object are the same handle, and they have to
    say so.  Nothing hands back the identical Python object twice -- a new
    pointer is built on every call that returns one -- so comparing by object
    identity, which is what ctypes leaves in place, makes a handle that is
    never equal to itself.

    That is not only a surprise to a caller writing ``if context ==
    self.context``.  ``OpenGL.contextdata`` keys everything it holds per
    context by one of these: the client-side arrays the GL goes on reading
    after the call that registered them, and the cached version and extension
    list.  With a hash by address and no equality to match it, every lookup
    hashes to the right bucket and then compares unequal to what is in it --
    so nothing is ever found again, a fresh entry accumulates on each call,
    and the arrays that were being kept alive are kept alive forever under
    keys nobody can reach.
    """
    _type_ = _Opaque
    @classmethod
    def from_param( cls, value ):
        return ctypes.cast( value, cls )
    @property
    def address( self ):
        """The address, or None for a null handle.

        Read by casting rather than with ``addressof(self.contents)``: a null
        pointer has no contents, so that raises where a driver answering
        "there is none" should simply read as none.
        """
        return ctypes.cast( self, ctypes.c_void_p ).value
    @property
    def as_voidp( self ):
        return ctypes.c_voidp( self.address )
    def __hash__(self):
        """Allow these pointers to be used as keys in dictionaries"""
        return hash( (self.__class__, self.address) )
    def __eq__( self, other ):
        """Equal to another handle of the same kind at the same address.

        The kind is part of it: an ``EGLContext`` and an ``OSMesaContext`` are
        different things whatever addresses they happen to hold, and so is the
        bare integer inside either of them.
        """
        if not isinstance( other, _opaque_pointer ):
            return NotImplemented
        return (
            self.__class__ is other.__class__
            and self.address == other.address
        )
    def __ne__( self, other ):
        equal = self.__eq__( other )
        if equal is NotImplemented:
            return equal
        return not equal
def opaque_pointer_cls( name ):
    """Create an Opaque pointer class for the given name"""
    typ = type( name, (_Opaque,), {} )
    p_typ = type( name+'_pointer', (_opaque_pointer,), {'_type_':typ})
    return p_typ
