"""Implementation of OpenGL errors/exceptions

Note that OpenGL-ctypes will also throw standard errors,
such as TypeError or ValueError when appropriate.

ErrorChecker is an _ErrorChecker instance that allows you
to register a new error-checking function for use 
throughout the system.
"""
import logging
_log = logging.getLogger( 'OpenGL.error' )
from OpenGL import platform, _configflags
from ctypes import ArgumentError
__all__ = (
    "Error",'GLError','GLUError','GLUTError',
    'GLerror','GLUerror','GLUTerror','ArgumentError',
)

class Error( Exception ):
    """Base class for all PyOpenGL-specific exception classes"""
class NoContext( Error ):
    """Raised to indicate that there is no currently active context
    
    Technically almost *any* OpenGL call can segfault if there is 
    no active context.  The OpenGL.CHECK_CONTEXT flag, if enabled 
    will cause this error to be raised whenever a GL or GLU call is 
    issued (via PyOpenGL) if there is no currently valid context.
    """
class CopyError( Error ):
    """Raised to indicate that operation requires data-copying
    
    if you set:
        OpenGL.ERROR_ON_COPY = True 
    
    before importing OpenGL.GL, this error will be raised when 
    a passed argument would require a copy to be made.
    """

class NullFunctionError( Error ):
    """Error raised when an undefined function is called"""

class GLError( Error ):
    """OpenGL core error implementation class
    
    Primary purpose of this error class is to allow for 
    annotating an error with more details about the calling 
    environment so that it's easier to debug errors in the
    wrapping process.
    
    Attributes:
    
        err -- the OpenGL error code for the error 
        result -- the OpenGL result code for the operation
        baseOperation -- the "function" being called
        pyArgs -- the translated set of Python arguments
        cArgs -- the Python objects matching 1:1 the C arguments
        cArguments -- ctypes-level arguments to the operation,
            often raw integers for pointers and the like
        description -- OpenGL description of the error (textual)
    """
    def __init__( 
        self, 
        err=None, 
        result=None, 
        cArguments=None, 
        baseOperation=None, 
        pyArgs=None, 
        cArgs=None,
        description=None,
    ):
        """Initialise the GLError, storing metadata for later display"""
        (
            self.err, self.result, self.cArguments, 
            self.baseOperation, self.pyArgs, self.cArgs,
            self.description
        ) = (
            err, result, cArguments,
            baseOperation, pyArgs, cArgs,
            description
        )
    DISPLAY_ORDER = (
        'err', 
        'description',
        'baseOperation',
        'pyArgs', 
        'cArgs',
        'cArguments',
        'result', 
    )
    def __str__( self ):
        """Create a fully formatted representation of the error"""
        args = []
        for property in self.DISPLAY_ORDER:
            value = getattr( self, property, None )
            if value is not None or property=='description':
                formatFunction = 'format_%s'%(property)
                if hasattr( self, formatFunction ):
                    args.append( getattr(self,formatFunction)( property, value ))
                else:
                    args.append( '%s = %s'%(
                        property,
                        self.shortRepr( value ),
                    ))
        return '%s(\n\t%s\n)'%(self.__class__.__name__, ',\n\t'.join(
            [x for x in args if x]
        ))
    def __repr__( self ):
        """Produce a much shorter version of the error as a string"""
        return '%s( %s )'%(
            self.__class__.__name__,
            ", ".join([x for x in [
                'err=%s'%(self.err),
                self.format_description( 'description', self.description ) or '',
                self.format_baseOperation( 'baseOperation', self.baseOperation ) or '',
            ] if x])
        )
    def format_description( self, property, value ):
        """Format description using GLU's gluErrorString"""
        if value is None and self.err is not None:
            try:
                from OpenGL.GLU import gluErrorString
                self.description = value = gluErrorString( self.err )
            except Exception as err:
                return None
        if value is None:
            return None
        return '%s = %s'%(
            property,
            self.shortRepr( value ),
        )
    def shortRepr( self, value, firstLevel=True ):
        """Retrieve short representation of the given value"""
        if isinstance( value, (list,tuple) ) and value and len(repr(value))>=40:
            if isinstance( value, list ):
                template = '[\n\t\t%s\n\t]'
            else:
                template = '(\n\t\t%s,\n\t)'
            return template%( ",\n\t\t".join(
                [
                    self.shortRepr(x,False) for x in value
                ]
            ))
        r = repr( value )
        if len(r) < 120:
            return r
        else:
            return r[:117] + '...'
    def format_baseOperation( self, property, value ):
        """Format a baseOperation reference for display"""
        if hasattr( value, '__name__' ):
            return '%s = %s'%( property, value.__name__ )
        else:
            return '%s = %r'%( property, value )

class GLUError( Error ):
    """GLU error implementation class"""

class GLUTError( Error ):
    """GLUT error implementation class"""
class EGLError( GLError ):
    """EGL error implementation class"""


def inside_begin_block( ):
    """Whether a ``glBegin`` block is open on this thread.

    ``glBegin`` switches error checking off for the block -- ``glGetError`` is
    itself illegal between the two -- so that switch is the record of being in
    one, whichever dispatch implementation is running.

    It matters beyond error checking because *no* GL query is legal in a block,
    the extension string included, and an immediate-mode extension command has
    nowhere but a block to be first called from.  Entry-point resolution reads
    this to know that the extension string cannot be asked for right now.

    Read from ``sys.modules`` rather than imported: a process that has never
    imported desktop GL has no ``glBegin`` to have called, and loading one to
    find that out would load a driver to answer a question about a block that
    cannot exist.
    """
    checker = _desktop_checker( )
    return bool( checker is not None and getattr( checker, 'suspended', False ) )


def _desktop_checker( ):
    """Desktop GL's error checker, or None where nothing has made one.

    Read from ``sys.modules`` rather than imported, for the reason
    :func:`inside_begin_block` gives.
    """
    import sys

    module = sys.modules.get( 'OpenGL.raw.GL._errors' )
    return getattr( module, '_error_checker', None ) if module else None


def end_abandoned_block( ):
    """Close a ``glBegin`` block left open, and say whether there was one.

    A block belongs to the context it was opened in and has to be closed
    there.  A context created or destroyed while one is open is undefined, and
    a driver need not survive being denied the ``glEnd``: Intel's Windows ICD
    leaves state that the *next* context creation in the process faults on,
    which reaches the program as an access violation with nothing near it to
    name the block that caused it.

    A block is left open when an exception escapes it -- a bad vertex, an
    entry point the driver does not export -- which is why the exception-safe
    form is ``glBegin(...)`` then ``try: ... finally: glEnd()``.  This is what
    a toolkit calls before it creates or destroys a context, while the context
    holding the block is still current, so a program that got that shape wrong
    is answered with a closed block rather than a crash.  PyOpenGL calls it
    for the context changes it is told about, in
    :func:`OpenGL.dispatch.make_current` and
    :func:`OpenGL.dispatch.forget_context`; a toolkit that makes contexts of
    its own calls it for the change it makes and PyOpenGL does not see.

    With ``PYOPENGL_ERROR_CHECKING=0`` there is no checker and so no record
    that a block was opened, and this answers False: a program built that way
    closes its own blocks.
    """
    checker = _desktop_checker( )
    if checker is None:
        return False
    if not getattr( checker, 'suspended', False ):
        # No block to close.  ``onEnd`` is still what the context changes have
        # always called here, and outside a block it only puts the registered
        # checker back where it already is.
        checker.onEnd( )
        return False
    _close_block_in_gl( )
    checker.onEnd( )
    _resume_compiled_checking( )
    return True


def _close_block_in_gl( ):
    """Issue the ``glEnd`` an abandoned block never got, if there is a context.

    Only where one is current to close it in: :func:`end_abandoned_block` is
    also reached for a context that has already gone, and there ``glEnd``
    would be a call into nothing.  The platform's own entry point rather than
    ``OpenGL.GL.glEnd``, which would re-enter the bookkeeping this is part of.
    """
    from OpenGL.platform import PLATFORM

    try:
        if not PLATFORM.GetCurrentContext( ):
            return
        end = getattr( PLATFORM.GL, 'glEnd', None )
    except Exception:          # pragma: no cover - no GL library to ask at all
        return
    if end is not None:
        end( )


def _resume_compiled_checking( ):
    """Turn the compiled dispatch layer's own check back on, where it is in use.

    It keeps a suspension switch of its own -- ``glBegin`` throws both -- so a
    block closed here has to be closed in both.  Imported on use, so choosing
    the ctypes implementation does not load the C extension to say it is not
    wanted.
    """
    from OpenGL import _configflags

    if _configflags.DISPATCH != 'c':
        return
    from OpenGL import _dispatch

    _dispatch.suspend_error_checking( False )


#: Set when PyOpenGL's own entry-point lookup ran inside a glBegin block and
#: the platform records an error for it.  Read and cleared by glEnd.
_lookup_dirtied_block = False


def note_lookup_inside_block( ):
    """Record that an address lookup inside a block recorded an error.

    Called by the platform whose lookup does that -- WGL's.  The error belongs
    to a call the caller never made, and it is invisible until the block ends,
    so glEnd consumes it rather than raising it at them.
    """
    global _lookup_dirtied_block
    _lookup_dirtied_block = True


def take_lookup_inside_block( ):
    """Whether a lookup dirtied this block, clearing the record."""
    global _lookup_dirtied_block
    dirtied, _lookup_dirtied_block = _lookup_dirtied_block, False
    return dirtied


if _configflags.ERROR_CHECKING:
    from OpenGL import acceleratesupport
    _ErrorChecker = None
    if acceleratesupport.ACCELERATE_AVAILABLE:
        try:
            from OpenGL_accelerate.errorchecker import _ErrorChecker
        except ImportError as err:
            _log.warning( """OpenGL_accelerate seems to be installed, but unable to import error checking entry point!""" )
    if _ErrorChecker is None:
        class _ErrorChecker( object ):
            """Per-API error-checking object
            
            Attributes:
                _registeredChecker -- the checking function enabled when
                    not doing onBegin/onEnd processing
                _currentChecker -- currently active checking function
                suspended -- whether a glBegin block currently has checking
                    switched off, so that a caller can tell "no errors" from
                    "not looking"
            """
            _getErrors = None
            suspended = False
            #: Whether the error code comes from a GL_KHR_debug callback rather
            #: than from a glGetError round trip.  OpenGL.dispatch switches it.
            readsDebugOutput = False
            def __init__( self, platform, baseOperation=None, noErrorResult=0, errorClass=GLError, needs_context=True ):
                """Initialize from a platform module/reference

                needs_context -- whether this API's calls are made with a GL
                    context current.  EGL, GLX and WGL manage the display, the
                    config and the context itself, so theirs are made before
                    one exists and by definition; waiting for a context there
                    would report none of their errors, since the part of a
                    program that calls them is the part with no GL context.
                """
                self._isValid = platform.CurrentContextIsValid
                self._getErrors = baseOperation
                self._baseGetErrors = baseOperation
                self._noErrorResult = noErrorResult
                self._errorClass = errorClass
                self.needs_context = needs_context
                self._install()
                self._currentChecker = self._registeredChecker
            def _install( self ):
                """Settle which callable a check calls, from `_getErrors`."""
                #: Whether a check asks the platform for a context before
                #: reading the error.  The compiled checker publishes the same
                #: name for the same thing and gates on it, so a program -- or
                #: a test -- reads either implementation the same way.
                self.checkContext = bool(
                    _configflags.CONTEXT_CHECKING and self.needs_context
                )
                if self._getErrors:
                    if _configflags.CONTEXT_CHECKING and self.needs_context:
                        self._registeredChecker = self.safeGetError
                    else:
                        self._registeredChecker = self._getErrors
                else:
                    self._registeredChecker = self.nullGetError
            def baseGetErrors( self ):
                """The driver's own glGetError, whatever is reading errors now."""
                return self._baseGetErrors()
            def setErrorReader( self, reader=None ):
                """Read error codes from `reader`, or from glGetError again.

                A GL_KHR_debug callback notices the error during the call, so
                the check afterwards is a flag read rather than a round trip.
                `OpenGL.dispatch.use_debug_output` is the way in; this is where
                the choice takes effect.
                """
                self._getErrors = reader or self._baseGetErrors
                self.readsDebugOutput = reader is not None
                self._install()
                if not self.suspended:
                    self._currentChecker = self._registeredChecker
            def __bool__( self ):
                """We are "true" if we actually do anything"""
                if self._registeredChecker is self.nullGetError:
                    return False 
                return True
            def safeGetError( self ):
                """Check for error, testing for context before operation
                
                With no context there is nothing to ask, which is "no error to
                report" rather than an error of its own: answering None instead
                would be unequal to _noErrorResult and raise one.
                """
                if self._isValid():
                    return self._getErrors()
                return self._noErrorResult 
            def nullGetError( self ):
                """Used as error-checker when no error checking should be done"""
                return self._noErrorResult
            def glCheckError( 
                self,
                result,
                baseOperation=None,
                cArguments=None,
                *args
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
                err = self._currentChecker()
                if err != self._noErrorResult:
                    raise self._errorClass(
                        err,
                        result,
                        cArguments = cArguments,
                        baseOperation = baseOperation,
                    )
                return result
            def onBegin( self ):
                """Called by glBegin to record the fact that glGetError won't work"""
                self._currentChecker = self.nullGetError
                self.suspended = True
            def onEnd( self ):
                """Called by glEnd to record the fact that glGetError will work"""
                self._currentChecker = self._registeredChecker
                self.suspended = False
else:
    _ErrorChecker = None
# Compatibility with PyOpenGL 2.x series
GLUerror = GLUError
GLerror = GLError 
GLUTerror = GLUTError
