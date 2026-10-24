"""Data-type definitions for EGL/GLES"""
import ctypes
pointer = ctypes.pointer

class _Opaque( ctypes.Structure ):
    """An Opaque Structure reference (base class)"""
class _opaque_pointer( ctypes.POINTER( _Opaque ) ):
    """A handle: an address, and the kind of object it is a handle to.

    Two handles to the same object compare equal.  Each call that returns a
    handle builds a new pointer object, so the default ctypes comparison by
    object identity would make two handles to one object unequal.

    Equality also matters inside PyOpenGL.  ``OpenGL.contextdata`` keys its
    per-context storage by these handles: the client-side arrays the GL reads
    after the registering call returns, and the cached version and extension
    list.  With a hash by address and identity equality, every lookup would
    reach the right bucket and then compare unequal.  Each call would add a
    new entry, and the stored arrays would stay alive under keys no lookup
    can match.
    """
    _type_ = _Opaque
    @classmethod
    def from_param( cls, value ):
        return ctypes.cast( value, cls )
    @property
    def address( self ):
        """The address, or None for a null handle.

        Read by casting instead of with ``addressof(self.contents)``.  A null
        pointer has no contents, so ``addressof`` would raise, and a null
        handle from the driver should read as None.
        """
        return ctypes.cast( self, ctypes.c_void_p ).value
    @property
    def as_voidp( self ):
        return ctypes.c_voidp( self.address )
    def __hash__(self):
        """Allow these pointers to be used as keys in dictionaries"""
        return hash( (self.__class__, self.address) )
    def __eq__( self, other ):
        """Return True for another handle of the same kind at the same address.

        The kind is compared too.  An ``EGLContext`` and an ``OSMesaContext``
        are never equal, whatever addresses they hold, and neither equals a
        bare integer.
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
