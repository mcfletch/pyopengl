"""General pattern which does late-bound calls"""

cdef class LateBind:
    """Provides a __call__ which dispatches to self._finalCall

    When called without self._finalCall() makes a call to
    self.finalise() and then calls self._finalCall()
    """
    cdef object _finalCall
    def setFinalCall( self, object finalCall ):
        """Set our finalCall to the callable object given"""
        self._finalCall = finalCall.__call__

    def finalise( self ):
        """Finalise our target to our final callable object"""

    def __call__( self, *args, **named ):
        """Call self._finalCall, calling finalise() first if not already called

        There's actually *no* reason to unpack and repack the arguments,
        but unfortunately I don't know of a Cython syntax to specify
        that.
        """
        if not self._finalCall:
            self._finalCall = self.finalise()
        return self._finalCall( *args, **named )

cdef class Curry(object):
    """Provides a simple Curry which can bind (only) the first element"""
    cdef object wrapperFunction
    cdef object baseFunction
    def __init__( self, wrapperFunction, baseFunction ):
        """Stores self.wrapperFunction and self.baseFunction"""
        self.baseFunction = baseFunction
        self.wrapperFunction = wrapperFunction
    def __call__( self, *args, **named ):
        """returns self.wrapperFunction( self.baseFunction, *args, **named )"""
        return self.wrapperFunction( self.baseFunction, *args, **named )
