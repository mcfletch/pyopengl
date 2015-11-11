"""Cython-coded GL-error-check module"""
from OpenGL import _configflags

cdef class _ErrorChecker:
    """Global error-checking object
    
    This error checker also includes "safeGetError" functionality,
    that is, it allows for checking for context validity as well 
    as for glBegin/glEnd checking.
    """
    cdef public int doChecks
    cdef public int checkContext
    cdef public object _isValid
    cdef public object _getErrors
    cdef public int _noErrorResult 
    
    def __init__( self, platform, baseOperation, noErrorResult=0 ):
        """Initialize from a platform module/reference"""
        self._isValid = platform.CurrentContextIsValid
        self._getErrors = baseOperation
        self._noErrorResult = noErrorResult
        
        self.doChecks = bool( _configflags.ERROR_CHECKING and self._getErrors )
        self.checkContext = _configflags.CONTEXT_CHECKING
    
    def glCheckError( 
        self,
        result,
        baseOperation=None,
        cArguments=None,
    ):
        """Base GL Error checker compatible with new ctypes errcheck protocol
        
        This function will raise a GLError with just the calling information
        available at the C-calling level, i.e. the error code, cArguments,
        baseOperation and result.  Higher-level code is responsible for any 
        extra annotations.
        
        Note:
            glCheckError relies on glBegin/glEnd interactions to 
            prevent glGetError being called during a glBegin/glEnd 
            sequence.  If you are calling glBegin/glEnd in C you 
            should call onBegin and onEnd appropriately.
        """
        cdef int err
        if self.doChecks:
            if self.checkContext:
                if not self._isValid():
                    return 
            err = self._getErrors()
            if err != self._noErrorResult:
                from OpenGL.error import GLError
                raise GLError(
                    err,
                    result,
                    cArguments = cArguments,
                    baseOperation = baseOperation,
                )
        return result
    def onBegin( self, target=None ):
        """Called by glBegin to record the fact that glGetError won't work"""
        self.doChecks = False
    def onEnd( self, target=None ):
        """Called by glEnd to record the fact that glGetError will work"""
        self.doChecks = bool( _configflags.ERROR_CHECKING and self._getErrors )
    def check( self ):
        return self.glCheckError( None, self._getErrors, [] )
