"""Run-time calculation of offset into Python Numeric (old) structures

Numeric Python, by fortuitous chance, puts the one thing
we need precisely as the first value in the structure beyond the
PyObject * header, so that it's exactly that many bytes from the
pointer value for the object...
"""
import ctypes

def dataPointerFunction( ):
    """Calculate the data-pointer offset in the Numeric object header"""
    offset = object.__basicsize__
    from_address = ctypes.c_void_p.from_address
    def dataPointer( data):
        """Return pointer-to-data + offset"""
        return from_address( id( data ) + offset ).value
    return dataPointer

dataPointer = dataPointerFunction()

if __name__ == "__main__":
    import Numeric 
    test = Numeric.arange( 0,200, 1,'i' )
    aType = ctypes.c_int * 200
    test2 = aType.from_address( dataPointer( test ) )
    assert test == test2, (test,test2)