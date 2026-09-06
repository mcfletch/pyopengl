"""Cython-coded GL-error-check module"""
#cython: language_level=3
from OpenGL import _configflags

cdef class _ErrorChecker:
    """Global error-checking object
    
    This error checker also includes "safeGetError" functionality,
    that is, it allows for checking for context validity as well 
    as for glBegin/glEnd checking.
    """
    cdef public int doChecks
    #: whether a glBegin block currently has checking switched off, so that a
    #: caller can tell "no errors" from "not looking"
    cdef public int suspended
    cdef public int checkContext
    cdef public object _isValid
    cdef public object _getErrors
    cdef public object _baseGetErrors
    cdef public object _errorClass
    cdef public int _noErrorResult
    #: whether this API's calls are made with a GL context current; read
    #: by callers and by the dispatch layer, so both implementations
    #: answer for it.
    cdef public int needs_context
    #: Whether the error code comes from a GL_KHR_debug callback rather than
    #: from a glGetError round trip.  OpenGL.dispatch switches it.
    cdef public int readsDebugOutput

    def __init__( self, platform, baseOperation, noErrorResult=0, errorClass=None, needs_context=True ):
        """Initialize from a platform module/reference

        needs_context -- whether this API's calls are made with a GL context
        current.  EGL, GLX and WGL manage the display, the config and the
        context itself, so theirs are made before one exists and by definition;
        waiting for a context there would report none of their errors.
        """
        self._isValid = platform.CurrentContextIsValid
        self._getErrors = baseOperation
        self._baseGetErrors = baseOperation
        self._noErrorResult = noErrorResult
        self._errorClass = errorClass

        self.doChecks = bool( _configflags.ERROR_CHECKING and self._getErrors )
        self.suspended = False
        self.needs_context = bool( needs_context )
        self.checkContext = bool( _configflags.CONTEXT_CHECKING and needs_context )
        self.readsDebugOutput = False

    def baseGetErrors( self ):
        """The driver's own glGetError, whatever is reading errors now."""
        return self._baseGetErrors()

    def setErrorReader( self, reader=None ):
        """Read error codes from `reader`, or from glGetError again.

        A GL_KHR_debug callback notices the error during the call, so the check
        afterwards is a flag read rather than a round trip.
        `OpenGL.dispatch.use_debug_output` is the way in; this is where the
        choice takes effect.
        """
        self._getErrors = reader if reader is not None else self._baseGetErrors
        self.readsDebugOutput = reader is not None
        if not self.suspended:
            self.doChecks = bool( _configflags.ERROR_CHECKING and self._getErrors )

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
                    # Nothing to ask, so nothing to report -- but errcheck's
                    # return value *is* the call's result, so returning here
                    # without it would answer None for every such call.
                    return result
            err = self._getErrors()
            if err != self._noErrorResult:
                if self._errorClass is None:
                    # circular import here otherwise
                    from OpenGL.error import GLError
                    self._errorClass = GLError
                raise self._errorClass(
                    err,
                    result,
                    cArguments = cArguments,
                    baseOperation = baseOperation,
                )
        return result
    def onBegin( self, target=None ):
        """Called by glBegin to record the fact that glGetError won't work"""
        self.doChecks = False
        self.suspended = True
    def onEnd( self, target=None ):
        """Called by glEnd to record the fact that glGetError will work"""
        self.doChecks = bool( _configflags.ERROR_CHECKING and self._getErrors )
        self.suspended = False
    def check( self ):
        return self.glCheckError( None, self._getErrors, [] )
